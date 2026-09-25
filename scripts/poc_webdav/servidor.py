"""
Prueba de concepto: WebDAV mínimo en Flask para editar un .odt con LibreOffice
sin acceso al servidor de ficheros.

Qué simula (no es código de BDDAT, no importa nada de `app/`):
    - Almacén direccionado por contenido: blobs/<sha256[:2]>/<sha256>, escritos
      una vez y nunca modificados.
    - Tabla de versiones (aquí un JSON): cada documento apunta a una lista de
      versiones; la vigente es la última.
    - Token de capacidad en la URL: /dav/<token>/<nombre>. El token dice qué
      documento y qué usuario; no hay cookie ni cabecera Authorization, porque
      LibreOffice no comparte la sesión del navegador.
    - Bloqueo mínimo (LOCK/UNLOCK) en memoria: un segundo editor recibe 423.

Registra cada petición en `peticiones.jsonl` para saber qué verbos usa
LibreOffice de verdad.

Uso:
    python servidor.py <dir_datos> <fichero_inicial.odt> [puerto]
Imprime la URL de edición del documento 1 para dos usuarios (ana, beto) y un
token caducado.
"""
import hashlib
import json
import os
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from email.utils import formatdate
from xml.sax.saxutils import escape

from flask import Flask, Response, request

DATOS = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else './datos_poc')
INICIAL = sys.argv[2] if len(sys.argv) > 2 else None
PUERTO = int(sys.argv[3]) if len(sys.argv) > 3 else 5077

app = Flask(__name__)
_cerrojo = threading.Lock()

# token -> {doc_id, usuario, caduca}
TOKENS: dict[str, dict] = {}
# doc_id -> {lock_token, usuario, caduca}
LOCKS: dict[int, dict] = {}


# ── Almacén direccionado por contenido ──────────────────────────────────────

def _ruta_blob(sha: str) -> str:
    return os.path.join(DATOS, 'blobs', sha[:2], sha)


def guardar_blob(contenido: bytes) -> str:
    sha = hashlib.sha256(contenido).hexdigest()
    ruta = _ruta_blob(sha)
    if not os.path.exists(ruta):
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        tmp = f'{ruta}.{uuid.uuid4().hex}.tmp'
        with open(tmp, 'wb') as f:
            f.write(contenido)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, ruta)          # escritura atómica: nunca un blob a medias
    return sha


def leer_blob(sha: str) -> bytes:
    with open(_ruta_blob(sha), 'rb') as f:
        contenido = f.read()
    if hashlib.sha256(contenido).hexdigest() != sha:   # verificación al leer
        raise IOError(f'blob {sha} corrupto')
    return contenido


# ── "Tabla" de versiones ────────────────────────────────────────────────────

def _ruta_bd() -> str:
    return os.path.join(DATOS, 'versiones.json')


def cargar_bd() -> dict:
    if not os.path.exists(_ruta_bd()):
        return {}
    with open(_ruta_bd()) as f:
        return json.load(f)


def guardar_bd(bd: dict) -> None:
    tmp = _ruta_bd() + '.tmp'
    with open(tmp, 'w') as f:
        json.dump(bd, f, indent=2, ensure_ascii=False)
    os.replace(tmp, _ruta_bd())


def version_vigente(doc_id: int) -> dict:
    return cargar_bd()[str(doc_id)]['versiones'][-1]


def nueva_version(doc_id: int, contenido: bytes, usuario: str, origen: str) -> tuple[dict, bool]:
    """Devuelve (versión vigente, creada). Mismo contenido → no crea versión."""
    sha = guardar_blob(contenido)
    bd = cargar_bd()
    doc = bd[str(doc_id)]
    if doc['versiones'] and doc['versiones'][-1]['sha256'] == sha:
        return doc['versiones'][-1], False
    v = {
        'n': len(doc['versiones']) + 1,
        'sha256': sha,
        'tamano': len(contenido),
        'usuario': usuario,
        'origen': origen,
        'creada': datetime.now(timezone.utc).isoformat(timespec='seconds'),
    }
    doc['versiones'].append(v)
    guardar_bd(bd)
    return v, True


# ── Registro de peticiones ──────────────────────────────────────────────────

@app.before_request
def _registrar():
    request._t0 = time.time()


@app.after_request
def _registrar_fin(resp):
    cab = {k: v for k, v in request.headers.items()
           if k.lower() in ('depth', 'if', 'lock-token', 'timeout', 'content-type',
                            'content-length', 'user-agent', 'overwrite', 'destination')}
    linea = {
        'metodo': request.method,
        'ruta': request.path,
        'estado': resp.status_code,
        'cabeceras': cab,
        'cuerpo_bytes': len(request.get_data(cache=True) or b''),
        'ms': round((time.time() - request._t0) * 1000, 1),
    }
    if request.method in ('PROPFIND', 'PROPPATCH', 'LOCK'):
        linea['cuerpo'] = request.get_data(as_text=True)
    if request.method in ('PROPFIND', 'LOCK'):
        linea['respuesta'] = resp.get_data(as_text=True)[:600]
    with open(os.path.join(DATOS, 'peticiones.jsonl'), 'a') as f:
        f.write(json.dumps(linea, ensure_ascii=False) + '\n')
    return resp


# ── WebDAV ──────────────────────────────────────────────────────────────────

DAV_METODOS = ['OPTIONS', 'GET', 'HEAD', 'PUT', 'PROPFIND', 'PROPPATCH', 'LOCK', 'UNLOCK',
               'DELETE', 'MOVE', 'COPY', 'MKCOL']
ALLOW = ', '.join(DAV_METODOS)
MIME_ODT = 'application/vnd.oasis.opendocument.text'


def _resolver_token(token: str):
    t = TOKENS.get(token)
    if t is None or t['caduca'] < time.time():
        return None
    return t


def _lock_vigente(doc_id: int):
    lk = LOCKS.get(doc_id)
    if lk and lk['caduca'] < time.time():
        LOCKS.pop(doc_id, None)
        lk = None
    return lk


LOCK_MAX = int(os.environ.get('POC_LOCK_MAX', '600'))


def _segundos_lock(cabecera: str | None) -> int:
    """Lo que pide el cliente (Timeout: Second-N), con techo LOCK_MAX. Con un
    techo bajo se comprueba que LibreOffice renueva el bloqueo en ediciones largas."""
    try:
        pedido = int((cabecera or '').split('-', 1)[1])
    except (IndexError, ValueError):
        pedido = LOCK_MAX
    return min(pedido, LOCK_MAX)


def _token_de_if(cabecera: str | None) -> str | None:
    """Extrae opaquelocktoken:... de la cabecera If: (<...>)."""
    if not cabecera:
        return None
    ini = cabecera.find('<')
    fin = cabecera.find('>', ini)
    return cabecera[ini + 1:fin] if ini >= 0 and fin > ini else None


def _fecha_http(iso: str) -> str:
    return formatdate(datetime.fromisoformat(iso).timestamp(), usegmt=True)


def _activelock(lk: dict) -> str:
    restante = max(0, int(lk['caduca'] - time.time()))
    return ('<D:activelock><D:locktype><D:write/></D:locktype><D:lockscope><D:exclusive/></D:lockscope>'
            f'<D:depth>0</D:depth><D:owner>{escape(lk["usuario"])}</D:owner>'
            f'<D:timeout>Second-{restante}</D:timeout>'
            f'<D:locktoken><D:href>{lk["lock_token"]}</D:href></D:locktoken></D:activelock>')


def _propfind_respuesta(href: str, *, coleccion: bool, v: dict | None, nombre: str,
                        lk: dict | None = None) -> str:
    if coleccion:
        props = ('<D:resourcetype><D:collection/></D:resourcetype>'
                 f'<D:displayname>{escape(nombre)}</D:displayname>')
    else:
        # getlastmodified es la fecha de la VERSIÓN, no "ahora": LibreOffice la
        # compara al guardar con la que vio al abrir para detectar que otro ha
        # cambiado el fichero, y si cambia aborta el guardado.
        props = (
            '<D:resourcetype/>'
            f'<D:displayname>{escape(nombre)}</D:displayname>'
            f'<D:getcontentlength>{v["tamano"]}</D:getcontentlength>'
            f'<D:getcontenttype>{MIME_ODT}</D:getcontenttype>'
            f'<D:getetag>"{v["sha256"]}"</D:getetag>'
            f'<D:getlastmodified>{_fecha_http(v["creada"])}</D:getlastmodified>'
            f'<D:creationdate>{v["creada"]}</D:creationdate>'
            '<D:supportedlock><D:lockentry><D:lockscope><D:exclusive/></D:lockscope>'
            '<D:locktype><D:write/></D:locktype></D:lockentry></D:supportedlock>'
            f'<D:lockdiscovery>{_activelock(lk) if lk else ""}</D:lockdiscovery>'
        )
    return (f'<D:response><D:href>{escape(href)}</D:href><D:propstat><D:prop>{props}</D:prop>'
            '<D:status>HTTP/1.1 200 OK</D:status></D:propstat></D:response>')


def _multistatus(respuestas: list[str]) -> Response:
    cuerpo = ('<?xml version="1.0" encoding="utf-8"?>'
              '<D:multistatus xmlns:D="DAV:">' + ''.join(respuestas) + '</D:multistatus>')
    return Response(cuerpo, status=207, content_type='application/xml; charset=utf-8')


@app.route('/dav/<token>/', methods=DAV_METODOS)
def dav_coleccion(token):
    """La 'carpeta' del token: solo contiene el documento. LibreOffice la
    consulta al guardar (comprueba el padre)."""
    t = _resolver_token(token)
    if t is None:
        return Response('token no válido o caducado', status=403)
    if request.method == 'OPTIONS':
        return Response(status=200, headers={'DAV': '1, 2', 'Allow': ALLOW, 'MS-Author-Via': 'DAV'})
    if request.method == 'PROPFIND':
        doc = cargar_bd()[str(t['doc_id'])]
        resp = [_propfind_respuesta(f'/dav/{token}/', coleccion=True, v=None, nombre=token)]
        if request.headers.get('Depth', '1') != '0':
            v = doc['versiones'][-1]
            resp.append(_propfind_respuesta(f'/dav/{token}/{doc["nombre"]}', coleccion=False,
                                            v=v, nombre=doc['nombre']))
        return _multistatus(resp)
    return Response(status=405, headers={'Allow': 'OPTIONS, PROPFIND'})


@app.route('/dav/<token>/<path:nombre>', methods=DAV_METODOS)
def dav_documento(token, nombre):
    t = _resolver_token(token)
    if t is None:
        return Response('token no válido o caducado', status=403)
    doc_id = t['doc_id']
    doc = cargar_bd()[str(doc_id)]
    if nombre != doc['nombre']:
        # LibreOffice intenta crear ficheros auxiliares (p. ej. .~lock.*#) si el
        # servidor no bloquea; aquí no existe nada más que el documento.
        if request.method in ('PROPFIND', 'GET', 'HEAD'):
            return Response(status=404)
        return Response('solo existe el documento del token', status=403)

    m = request.method
    if m == 'OPTIONS':
        return Response(status=200, headers={'DAV': '1, 2', 'Allow': ALLOW, 'MS-Author-Via': 'DAV'})

    if m in ('GET', 'HEAD'):
        v = doc['versiones'][-1]
        cuerpo = b'' if m == 'HEAD' else leer_blob(v['sha256'])
        r = Response(cuerpo, content_type=MIME_ODT, headers={'ETag': f'"{v["sha256"]}"'})
        r.headers['Content-Length'] = str(v['tamano'])
        return r

    if m == 'PROPFIND':
        v = doc['versiones'][-1]
        return _multistatus([_propfind_respuesta(request.path, coleccion=False, v=v, nombre=nombre,
                                                 lk=_lock_vigente(doc_id))])

    if m == 'PROPPATCH':
        # LibreOffice no debería necesitarlo; se acepta sin guardar nada.
        return _multistatus([_propfind_respuesta(request.path, coleccion=False,
                                                 v=doc['versiones'][-1], nombre=nombre)])

    if m == 'LOCK':
        with _cerrojo:
            lk = _lock_vigente(doc_id)
            refresco = _token_de_if(request.headers.get('If'))
            if lk and lk['lock_token'] != refresco and lk['usuario'] != t['usuario']:
                return Response(f'bloqueado por {lk["usuario"]}', status=423)
            if lk is None or (lk['lock_token'] != refresco):
                lk = {'lock_token': f'opaquelocktoken:{uuid.uuid4()}', 'usuario': t['usuario']}
            lk['caduca'] = time.time() + _segundos_lock(request.headers.get('Timeout'))
            LOCKS[doc_id] = lk
        cuerpo = ('<?xml version="1.0" encoding="utf-8"?><D:prop xmlns:D="DAV:"><D:lockdiscovery>'
                  f'{_activelock(lk)}</D:lockdiscovery></D:prop>')
        return Response(cuerpo, status=200, content_type='application/xml; charset=utf-8',
                        headers={'Lock-Token': f'<{lk["lock_token"]}>'})

    if m == 'UNLOCK':
        with _cerrojo:
            lk = _lock_vigente(doc_id)
            pedido = (request.headers.get('Lock-Token') or '').strip('<> ')
            if lk and lk['lock_token'] == pedido:
                LOCKS.pop(doc_id, None)
        return Response(status=204)

    if m == 'PUT':
        with _cerrojo:
            lk = _lock_vigente(doc_id)
            if lk and lk['usuario'] != t['usuario']:
                return Response(f'bloqueado por {lk["usuario"]}', status=423)
            if t.get('solo_lectura'):
                return Response('token de solo lectura', status=403)
            v, creada = nueva_version(doc_id, request.get_data(), t['usuario'], 'webdav')
        return Response(status=204 if not creada else 201, headers={'ETag': f'"{v["sha256"]}"'})

    # DELETE, MOVE, COPY, MKCOL: el almacén es inmutable, nunca se borra por DAV.
    return Response('operación no admitida', status=403)


# ── Arranque ────────────────────────────────────────────────────────────────

def _emitir_token(doc_id: int, usuario: str, *, segundos: int = 8 * 3600, solo_lectura=False) -> str:
    tok = uuid.uuid4().hex + uuid.uuid4().hex   # 256 bits
    TOKENS[tok] = {'doc_id': doc_id, 'usuario': usuario, 'caduca': time.time() + segundos,
                   'solo_lectura': solo_lectura}
    return tok


def _preparar():
    os.makedirs(DATOS, exist_ok=True)
    bd = cargar_bd()
    if '1' not in bd:
        if not INICIAL:
            sys.exit('Falta fichero inicial')
        with open(INICIAL, 'rb') as f:
            contenido = f.read()
        bd['1'] = {'nombre': 'Requerimiento subsanación AT-123.odt', 'versiones': []}
        guardar_bd(bd)
        nueva_version(1, contenido, 'generador', 'generado')
    nombre = cargar_bd()['1']['nombre']
    from urllib.parse import quote
    base = f'http://127.0.0.1:{PUERTO}/dav'
    urls = {
        'ana': f'{base}/{_emitir_token(1, "ana")}/{quote(nombre)}',
        'beto': f'{base}/{_emitir_token(1, "beto")}/{quote(nombre)}',
        'caducado': f'{base}/{_emitir_token(1, "ana", segundos=-1)}/{quote(nombre)}',
    }
    with open(os.path.join(DATOS, 'urls.json'), 'w') as f:
        json.dump(urls, f, indent=2)
    print(json.dumps(urls, indent=2), flush=True)


if __name__ == '__main__':
    _preparar()
    app.run(host='127.0.0.1', port=PUERTO, threaded=True, debug=False)

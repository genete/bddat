"""
Cliente de la prueba de concepto: maneja LibreOffice por UNO contra el WebDAV de
`servidor.py`. Ejecutar con el Python que trae el módulo `uno` (en Debian/Ubuntu,
/usr/bin/python3 con el paquete python3-uno).

Cada escenario usa su propio proceso soffice con perfil propio, como si fueran
dos puestos distintos.

Uso:
    python cliente_lo.py <dir_datos>
"""
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request

import uno
from com.sun.star.beans import PropertyValue

DATOS = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else './datos_poc')
with open(os.path.join(DATOS, 'urls.json')) as f:
    URLS = json.load(f)


def _prop(nombre, valor):
    p = PropertyValue()
    p.Name, p.Value = nombre, valor
    return p


class Puesto:
    """Un soffice headless con perfil propio, escuchando en una tubería."""

    def __init__(self, nombre):
        self.nombre = nombre
        self.perfil = tempfile.mkdtemp(prefix=f'lo_{nombre}_')
        self.tuberia = f'poc_{nombre}_{os.getpid()}'
        self.proc = subprocess.Popen(
            ['soffice', '--headless', '--invisible', '--norestore', '--nologo',
             f'-env:UserInstallation=file://{self.perfil}',
             f'--accept=pipe,name={self.tuberia};urp;'],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        local = uno.getComponentContext()
        resolver = local.ServiceManager.createInstanceWithContext(
            'com.sun.star.bridge.UnoUrlResolver', local)
        for _ in range(60):
            try:
                ctx = resolver.resolve(
                    f'uno:pipe,name={self.tuberia};urp;StarOffice.ComponentContext')
                break
            except Exception:
                time.sleep(0.5)
        else:
            raise RuntimeError('soffice no arrancó')
        self.desktop = ctx.ServiceManager.createInstanceWithContext(
            'com.sun.star.frame.Desktop', ctx)

    def abrir(self, url, **extra):
        props = [_prop('Hidden', True)] + [_prop(k, v) for k, v in extra.items()]
        return self.desktop.loadComponentFromURL(url, '_blank', 0, tuple(props))

    def cerrar(self):
        try:
            self.desktop.terminate()
        except Exception:
            pass
        try:
            self.proc.wait(timeout=20)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def texto(doc):
    return doc.getText().getString()


def anadir_parrafo(doc, frase):
    t = doc.getText()
    t.insertString(t.getEnd(), '\n' + frase, False)


def versiones():
    with open(os.path.join(DATOS, 'versiones.json')) as f:
        return json.load(f)['1']['versiones']


def resultado(nombre, ok, detalle=''):
    print(f'[{"OK " if ok else "FALLO"}] {nombre}' + (f' — {detalle}' if detalle else ''), flush=True)
    return ok


def main():
    todo_ok = True

    # 1. Abrir por http://, editar, guardar → PUT → versión nueva de "ana".
    ana = Puesto('ana')
    try:
        n0 = len(versiones())
        doc = ana.abrir(URLS['ana'])
        todo_ok &= resultado('1a abrir por http://', doc is not None,
                             f'solo lectura={doc.isReadonly()}, {len(texto(doc))} caracteres')
        anadir_parrafo(doc, 'PÁRRAFO AÑADIDO POR ANA VÍA WEBDAV')
        doc.store()
        vs = versiones()
        todo_ok &= resultado('1b guardar crea versión nueva',
                             len(vs) == n0 + 1 and vs[-1]['usuario'] == 'ana',
                             f'versiones {n0}→{len(vs)}, última de {vs[-1]["usuario"]}')

        # 2. Con ana dentro (documento abierto y bloqueado), entra beto.
        beto = Puesto('beto')
        try:
            doc_b = None
            try:
                doc_b = beto.abrir(URLS['beto'])
            except Exception as e:
                todo_ok &= resultado('2a beto abre mientras ana edita', False, repr(e))
            if doc_b is not None:
                ro = doc_b.isReadonly()
                resultado('2a beto abre mientras ana edita', True, f'solo lectura={ro}')
                try:
                    anadir_parrafo(doc_b, 'INTENTO DE BETO')
                    doc_b.store()
                    todo_ok &= resultado('2b beto no puede sobrescribir', False,
                                         'store() de beto ha funcionado')
                except Exception as e:
                    todo_ok &= resultado('2b beto no puede sobrescribir', True,
                                         type(e).__name__)
                doc_b.close(True)
        finally:
            beto.cerrar()

        doc.close(True)       # ana cierra → UNLOCK
    finally:
        ana.cerrar()

    # 3. Reabrir en un puesto nuevo: se lee la versión que guardó ana.
    otro = Puesto('reapertura')
    try:
        doc = otro.abrir(URLS['beto'])
        todo_ok &= resultado('3 la edición persiste al reabrir',
                             'PÁRRAFO AÑADIDO POR ANA VÍA WEBDAV' in texto(doc),
                             f'solo lectura={doc.isReadonly()}')
        # Guardar sin cambios. No es un requisito sino una observación: si
        # LibreOffice reescribiera bytes idénticos, el sha256 bastaría para no
        # crear versiones vacías; si no, hace falta otro criterio.
        n = len(versiones())
        doc.store()
        resultado('3b (observación) guardar sin cambios', True,
                  'mismos bytes, no crea versión' if len(versiones()) == n
                  else 'bytes distintos: crea versión (ver comparar_versiones.py)')
        doc.close(True)

        # 4. Esquema vnd.sun.star.webdav:// (el nativo de LibreOffice).
        url_dav = URLS['beto'].replace('http://', 'vnd.sun.star.webdav://', 1)
        doc = otro.abrir(url_dav)
        anadir_parrafo(doc, 'PÁRRAFO DE BETO POR vnd.sun.star.webdav')
        doc.store()
        vs = versiones()
        todo_ok &= resultado('4 esquema vnd.sun.star.webdav://', vs[-1]['usuario'] == 'beto',
                             f'última versión de {vs[-1]["usuario"]}')
        doc.close(True)

        # 5. Token caducado: no se abre.
        try:
            d = otro.abrir(URLS['caducado'])
            todo_ok &= resultado('5 token caducado rechazado', d is None,
                                 'se ha abierto' if d is not None else 'devuelve None')
        except Exception as e:
            todo_ok &= resultado('5 token caducado rechazado', True, type(e).__name__)
    finally:
        otro.cerrar()

    # 7. Edición larga: ana tiene el documento abierto más tiempo del que dura el
    # bloqueo (el servidor lo limita con POC_LOCK_MAX). Si LibreOffice lo renueva,
    # beto sigue encontrándolo bloqueado y el guardado de ana entra.
    espera = int(os.environ.get('POC_ESPERA_LARGA', '0'))
    if espera:
        ana = Puesto('ana_larga')
        beto = Puesto('beto_larga')
        try:
            doc = ana.abrir(URLS['ana'])
            anadir_parrafo(doc, 'EDICIÓN LARGA DE ANA')
            time.sleep(espera)
            doc_b = beto.abrir(URLS['beto'])
            todo_ok &= resultado(f'7a tras {espera}s, el bloqueo de ana sigue vivo',
                                 doc_b.isReadonly(), f'beto solo lectura={doc_b.isReadonly()}')
            doc_b.close(True)
            doc.store()
            vs = versiones()
            todo_ok &= resultado('7b ana guarda al final de la edición larga',
                                 vs[-1]['usuario'] == 'ana', f'última versión de {vs[-1]["usuario"]}')
            doc.close(True)
        finally:
            beto.cerrar()
            ana.cerrar()

    # 6. Integridad: el blob vigente coincide con lo que sirve GET.
    with urllib.request.urlopen(URLS['beto']) as r:
        import hashlib
        sha = hashlib.sha256(r.read()).hexdigest()
    todo_ok &= resultado('6 GET sirve el blob vigente', sha == versiones()[-1]['sha256'])

    print('\nVersiones:')
    for v in versiones():
        print(f"  v{v['n']}  {v['usuario']:<10} {v['origen']:<9} {v['tamano']:>7} B  {v['sha256'][:12]}")
    sys.exit(0 if todo_ok else 1)


if __name__ == '__main__':
    main()

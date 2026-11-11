"""Ejecutor de un expediente-tipo de interfaz: recorre su lista de pasos con `--desde` / `--hasta` / `--nuevo`.

Cada expediente-tipo (`analisis_doc_dos_vueltas/`) aporta un módulo `escenario` con:

    CODIGO, CARPETA, DIAS_ESCENARIO      identidad y cuántos días atrás empieza el calendario
    datos_alta(fecha_base, opts)         los `DatosAlta` del formulario
    PASOS                                [(nombre, función(c)), …], sin el alta, que es el paso 0 y la pone el ejecutor

y su `__main__.py` llama a `ejecutar(escenario)`.

Estado: `docs_prueba/ui_dummy/<CARPETA>/estado.json` guarda el expediente y los pasos hechos. Sin `--nuevo` se retoma
en el primero que falta; con `--nuevo` se recicla el expediente anterior (`[RECICLAR]`, que recoge
`limpiar_reciclables.py`) y se empieza otro desde el alta. Los pasos son sucesivos sobre el mismo expediente y no se
repiten sobre él: `--desde` fuerza el arranque (y la responsabilidad es tuya).
"""
import argparse
import sys
from datetime import date, timedelta

from .alta import alta
from .contexto import Contexto, cargar_estado
from .pasos import reciclar
from .sesion import SALIDAS, Sesion, anadir_opciones_comunes, exigir_credenciales


def _parser(escenario):
    p = argparse.ArgumentParser(description=escenario.__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    anadir_opciones_comunes(p)
    p.add_argument('--lista', action='store_true', help='muestra los pasos y sale')
    p.add_argument('--nuevo', action='store_true',
                   help='empieza un expediente nuevo (recicla el de la ejecución anterior)')
    p.add_argument('--sin-reciclar', action='store_true', help='con --nuevo, no marca [RECICLAR] el anterior')
    p.add_argument('--desde', help='primer paso a ejecutar (por defecto, el primero que no esté hecho)')
    p.add_argument('--hasta', help='último paso a ejecutar (por defecto, el último)')
    p.add_argument('--dias', type=int, default=escenario.DIAS_ESCENARIO,
                   help='cuántos días atrás se fija el reloj (fecha base = hoy − dias); por defecto %(default)s')
    p.add_argument('--responsable', help='texto del responsable en el desplegable del alta (por defecto, el usuario del login)')
    p.add_argument('--titular', help='texto del titular en la lista del alta (por defecto, el primero)')
    return p


def ejecutar(escenario, argv=None):
    """Devuelve el código de salida (0 si todos los pasos salieron bien)."""
    opts = _parser(escenario).parse_args(argv)

    fecha_base = date.today() - timedelta(days=opts.dias)

    def paso_alta(c):
        alta(c, escenario.datos_alta(fecha_base, opts), fecha_base)

    pasos = [('alta', paso_alta), *escenario.PASOS]
    nombres = [n for n, _ in pasos]
    if opts.lista:
        print('pasos:', ' → '.join(nombres))
        return 0
    for n in (opts.desde, opts.hasta):
        if n and n not in nombres:
            sys.exit(f'No existe el paso «{n}». Pasos: {", ".join(nombres)}')
    exigir_credenciales(opts)

    carpeta = SALIDAS / escenario.CARPETA
    previo = cargar_estado(carpeta)
    nuevo = opts.nuevo or previo is None
    if nuevo and opts.desde not in (None, 'alta'):
        sys.exit('No hay un expediente en curso (o has pedido --nuevo): se empieza por el paso «alta».')
    estado = {'hecho': [], 'ids': {}} if nuevo else previo
    hecho = estado.setdefault('hecho', [])

    if nuevo:
        desde = 0
    elif opts.desde:
        desde = nombres.index(opts.desde)
    else:
        desde = next((i for i, n in enumerate(nombres) if n not in hecho), None)
    hasta = nombres.index(opts.hasta) if opts.hasta else len(nombres) - 1
    if desde is None:
        sys.exit(f'Nada que hacer: el expediente {estado.get("at")} ya tiene todos los pasos hechos (usa --nuevo).')
    if desde > hasta:
        sys.exit(f'Nada que hacer: «{nombres[desde]}» va después de «{nombres[hasta]}».')

    destino = 'expediente nuevo' if nuevo else f'{estado.get("at")} (id {estado.get("id")})'
    print(f'{escenario.CODIGO} sobre {destino}: {nombres[desde]} → {nombres[hasta]}')

    s = Sesion(opts, carpeta)
    c = Contexto(s, opts, carpeta, estado)
    codigo = 0
    try:
        with s.paso('login (dos pasos)', 'CSS por name + selector de rol'):
            s.login()
        if nuevo and previo and not opts.sin_reciclar:
            print('— reciclar el expediente anterior')
            reciclar(c, previo, escenario.MARCA)
        for nombre, fn in pasos[desde:hasta + 1]:
            print(f'— {nombre}')
            try:
                fn(c)
            finally:
                c.guardar()   # los ids de lo creado a medias también se conservan
            if nombre not in hecho:
                hecho.append(nombre)
            c.guardar()
            s.captura(f'paso-{nombre}')
    except Exception:  # noqa: BLE001
        codigo = 1
        alertas = [a.strip() for a in s.page.locator('.alert').all_text_contents()]
        if alertas:
            print('  alertas en pantalla:', ' || '.join(' '.join(a.split()) for a in alertas))
    ok, total = s.cerrar('diario')
    print(f'\n{ok}/{total} acciones correctas.')
    return codigo

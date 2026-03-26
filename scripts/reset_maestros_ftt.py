"""
reset_maestros_ftt.py — Sincroniza los maestros FTT de BD con ESTRUCTURA_FTT.json

Lee docs/ESTRUCTURA_FTT.json y reconstruye desde cero las tablas:
  tipos_fases, tipos_tramites, fases_tramites

Los IDs se asignan por orden de aparición en el JSON — deterministas y reproducibles.
RECEPCION_INFORME (y cualquier trámite compartido entre fases) se inserta una sola vez
y se referencia en fases_tramites tantas veces como sea necesario.

Uso:
    cd /d/BDDAT
    source venv/Scripts/activate
    python scripts/reset_maestros_ftt.py           # solo maestros FTT
    python scripts/reset_maestros_ftt.py --full    # + datos operativos (dev completo)

ADVERTENCIA --full: borra expedientes, solicitudes, fases, trámites, tareas,
documentos y entidades. Solo para entorno de desarrollo.
"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db

FULL = '--full' in sys.argv

JSON_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         'docs', 'ESTRUCTURA_FTT.json')


def cargar_estructura():
    with open(JSON_PATH, encoding='utf-8') as f:
        data = json.load(f)

    version = data['metadata']['version']
    fases = data['FASES']

    # Trámites únicos en orden de primera aparición
    tramites_idx = {}   # codigo -> id (1-based)
    tramites_lista = [] # [{codigo, nombre}, ...]
    for fase in fases:
        for t in fase['tramites']:
            if t['codigo'] not in tramites_idx:
                tramites_idx[t['codigo']] = len(tramites_lista) + 1
                tramites_lista.append({'codigo': t['codigo'], 'nombre': t['nombre']})

    # Pares fase_id -> tramite_id
    pares = []
    for fi, fase in enumerate(fases, 1):
        for t in fase['tramites']:
            pares.append((fi, tramites_idx[t['codigo']]))

    return version, fases, tramites_lista, pares


def ejecutar(version, fases, tramites_lista, pares):
    with db.engine.begin() as conn:
        if FULL:
            print("  Borrando datos operativos...")
            for tabla in [
                'tareas', 'tramites', 'fases', 'documentos',
                'historico_titulares_expediente', 'solicitudes', 'expedientes',
                'municipios_proyecto', 'documentos_proyecto', 'proyectos',
                'autorizados_titular', 'direcciones_notificacion', 'entidades',
            ]:
                conn.execute(db.text(f'DELETE FROM public.{tabla}'))

        # Maestros dependientes
        print("  Borrando maestros FTT...")
        conn.execute(db.text('DELETE FROM public.fases_tramites'))
        conn.execute(db.text('DELETE FROM public.tipos_fases'))
        conn.execute(db.text('DELETE FROM public.tipos_tramites'))
        conn.execute(db.text('ALTER SEQUENCE public.tipos_fases_id_seq RESTART WITH 1'))
        conn.execute(db.text('ALTER SEQUENCE public.tipos_tramites_id_seq RESTART WITH 1'))

        print(f"  Insertando {len(fases)} tipos_fases...")
        for fase in fases:
            conn.execute(db.text(
                'INSERT INTO public.tipos_fases (codigo, nombre) VALUES (:c, :n)'
            ), {'c': fase['codigo'], 'n': fase['nombre']})

        print(f"  Insertando {len(tramites_lista)} tipos_tramites...")
        for t in tramites_lista:
            conn.execute(db.text(
                'INSERT INTO public.tipos_tramites (codigo, nombre) VALUES (:c, :n)'
            ), {'c': t['codigo'], 'n': t['nombre']})

        print(f"  Insertando {len(pares)} pares fases_tramites...")
        for tf_id, tt_id in pares:
            conn.execute(db.text(
                'INSERT INTO public.fases_tramites (tipo_fase_id, tipo_tramite_id) VALUES (:f, :t)'
            ), {'f': tf_id, 't': tt_id})

        # Verificación
        n_fases = conn.execute(db.text('SELECT COUNT(*) FROM public.tipos_fases')).scalar()
        n_tram  = conn.execute(db.text('SELECT COUNT(*) FROM public.tipos_tramites')).scalar()
        n_pares = conn.execute(db.text('SELECT COUNT(*) FROM public.fases_tramites')).scalar()

        errores = []
        if n_fases != len(fases):
            errores.append(f'tipos_fases: esperados {len(fases)}, hay {n_fases}')
        if n_tram != len(tramites_lista):
            errores.append(f'tipos_tramites: esperados {len(tramites_lista)}, hay {n_tram}')
        if n_pares != len(pares):
            errores.append(f'fases_tramites: esperados {len(pares)}, hay {n_pares}')

        if errores:
            raise RuntimeError('Verificación fallida:\n  ' + '\n  '.join(errores))

    return n_fases, n_tram, n_pares


app = create_app()
with app.app_context():
    print(f"Cargando {JSON_PATH}...")
    version, fases, tramites_lista, pares = cargar_estructura()
    print(f"  FTT v{version}: {len(fases)} fases, {len(tramites_lista)} trámites únicos, {len(pares)} pares")

    modo = 'FULL (operativos + maestros)' if FULL else 'maestros FTT'
    print(f"Ejecutando reset [{modo}]...")
    n_fases, n_tram, n_pares = ejecutar(version, fases, tramites_lista, pares)

    print(f"\nReset completado — FTT v{version}:")
    print(f"  tipos_fases    : {n_fases}")
    print(f"  tipos_tramites : {n_tram}")
    print(f"  fases_tramites : {n_pares}")

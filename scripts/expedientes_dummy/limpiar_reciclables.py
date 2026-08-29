"""Limpieza de expedientes dummy marcados [RECICLAR] (#814).

Contrapartida genérica de los scripts de expediente-tipo de esta carpeta: ellos
nunca borran —solo marcan `Solicitud.observaciones` con el prefijo
`[RECICLAR]`— y este borra lo marcado. La separación es deliberada y ya ha
pagado: el vestigio AT-15 fue lo que permitió reconstruir *qué* había pasado en
una ejecución defectuosa, en vez de tener que recordarlo.

No conoce ningún expediente-tipo concreto: trabaja sobre la marca, así que sirve
para cualquier script futuro de `scripts/expedientes_dummy/`.

SQL directo, a diferencia del script de creación (que recorre el circuito real):
esto es mantenimiento de una BD de desarrollo, no un acto de tramitación. El
circuito real no puede hacerlo —`mutaciones_arbol.borrar_*` borra hoja a hoja y
`check_invariante('BORRAR', …)` bloquea a propósito la evidencia notificada
(#722)—, que es justo lo que hay que retirar aquí.

Salvaguardas:
    - Dry-run por defecto: sin `--borrar` solo informa.
    - Solo entra un expediente si TODAS sus solicitudes están marcadas.
    - `--at` acota a números de expediente concretos.
    - Los ficheros del pool (`FILESYSTEM_BASE/AT-N/`) solo se tocan con
      `--con-ficheros`; por defecto se informa de que quedan y no se borran.
    - Comprobación dinámica del esquema antes de tocar nada: si alguien añade
      una tabla que apunta a las que aquí se borran y no está contemplada, el
      script aborta en vez de dejar filas colgando en silencio.
    - Una transacción por expediente: si algo falla, ese expediente queda intacto.

Uso:
    venv/Scripts/python.exe scripts/expedientes_dummy/limpiar_reciclables.py
    venv/Scripts/python.exe scripts/expedientes_dummy/limpiar_reciclables.py --borrar
    venv/Scripts/python.exe scripts/expedientes_dummy/limpiar_reciclables.py --borrar --at 12,13 --si
    venv/Scripts/python.exe scripts/expedientes_dummy/limpiar_reciclables.py --borrar --con-ficheros --si
"""
import argparse
import os
import shutil
import sys

sys.path.insert(0, r"D:\BDDAT")

MARCA = '[RECICLAR]'

from app import create_app, db  # noqa: E402

app = create_app()


# ---------------------------------------------------------------------------
# Comprobación de cobertura del esquema
# ---------------------------------------------------------------------------

# Tablas cuyo borrado dispara este script, directa o transitivamente. Toda FK
# que apunte a una de ellas tiene que estar resuelta: por la propia BD (CASCADE
# o SET NULL) o por una sentencia explícita de `_borrar_expediente`.
TABLAS_VIGILADAS = (
    'expedientes', 'proyectos', 'solicitudes', 'fases', 'tramites', 'tareas',
    'documentos', 'organismos_expediente', 'notificaciones', 'diagnosticos',
    'certificados', 'certificados_fase', 'informaciones_publicas', 'resoluciones',
    'alegantes', 'interesados_expediente', 'activos_expediente',
    'historico_titulares_expediente', 'documentos_tarea', 'tramites_organismos',
    'requerimientos_tarea', 'coberturas_item_tecnico', 'documentos_requisito',
    'municipios_proyecto', 'documentos_proyecto',
)

# FKs sin borrado automático que este script resuelve a mano, como
# '<tabla_hija>.<columna>'. Si aparece una que no está aquí, abortamos: el orden
# de borrado de abajo habría dejado de ser completo.
FK_TRATADAS_A_MANO = frozenset({
    # Referencias a documentos que hay que neutralizar antes de borrarlos
    'fases.documento_resultado_id',
    'solicitudes.documento_cierre_id',
    'organismos_expediente.documento_id',
    'organismos_expediente.condicionados_doc_id',
    'interesados_expediente.fuente_doc_id',
    # Hijos de documentos que se borran explícitamente
    'certificados.documento_id',
    'diagnosticos.documento_id',
    'documentos_requisito.documento_id',
    # Colgados de fase/expediente sin cascada
    'certificados_fase.expediente_id',
    'certificados_fase.fase_id',
    'informaciones_publicas.fase_id',
    'resoluciones.fase_id',
    # Cadena principal, borrada en orden explícito
    'documentos.expediente_id',
    'solicitudes.expediente_id',
    'expedientes.proyecto_id',
    # Auto-referencias / históricos: se comprueban o se borran antes
    'historico_titulares_expediente.solicitud_cambio_id',
    'solicitudes.solicitud_afectada_id',
})

SQL_FKS = """
SELECT c.conrelid::regclass::text AS hija,
       a.attname                  AS col,
       c.confrelid::regclass::text AS padre,
       c.confdeltype              AS regla
FROM pg_constraint c
JOIN unnest(c.conkey) WITH ORDINALITY AS k(attnum, ord) ON true
JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = k.attnum
WHERE c.contype = 'f'
  AND c.confrelid::regclass::text = ANY(:tablas)
"""


def _verificar_cobertura_esquema():
    """Aborta si el esquema tiene una FK hacia lo que borramos que ni la BD
    resuelve sola ni contempla `FK_TRATADAS_A_MANO`."""
    filas = db.session.execute(
        db.text(SQL_FKS), {'tablas': list(TABLAS_VIGILADAS)}
    ).mappings().all()

    huerfanas = []
    for f in filas:
        if f['regla'] in ('c', 'n', 'd'):      # CASCADE / SET NULL / SET DEFAULT
            continue
        clave = f"{f['hija']}.{f['col']}"
        if clave not in FK_TRATADAS_A_MANO:
            huerfanas.append(f"{clave} → {f['padre']}")

    if huerfanas:
        print('ABORTADO: el esquema tiene FKs sin borrado automático que este script no trata:')
        for h in sorted(huerfanas):
            print(f'  - {h}')
        print('Añádelas al orden de borrado y a FK_TRATADAS_A_MANO antes de seguir.')
        sys.exit(1)


# ---------------------------------------------------------------------------
# Localización de expedientes reciclables
# ---------------------------------------------------------------------------

def _expedientes_reciclables(ats_filtro):
    """Expedientes cuyas solicitudes están TODAS marcadas [RECICLAR].

    Un expediente con alguna solicitud viva se descarta con aviso: la marca es
    por solicitud, pero el borrado arrastra el expediente entero.
    """
    filas = db.session.execute(db.text("""
        SELECT e.id AS expediente_id, e.numero_at, e.proyecto_id,
               count(*)                                            AS n_solicitudes,
               count(*) FILTER (WHERE s.observaciones LIKE :marca) AS n_marcadas
        FROM public.expedientes e
        JOIN public.solicitudes s ON s.expediente_id = e.id
        GROUP BY e.id, e.numero_at, e.proyecto_id
        HAVING count(*) FILTER (WHERE s.observaciones LIKE :marca) > 0
        ORDER BY e.numero_at
    """), {'marca': f'{MARCA}%'}).mappings().all()

    candidatos = []
    for f in filas:
        if ats_filtro and f['numero_at'] not in ats_filtro:
            continue
        if f['n_marcadas'] != f['n_solicitudes']:
            print(f"  AT-{f['numero_at']}: OMITIDO — {f['n_marcadas']} de {f['n_solicitudes']} "
                  f"solicitudes marcadas; el borrado arrastraría solicitudes vivas.")
            continue
        candidatos.append(dict(f))
    return candidatos


def _inventario(expediente_id):
    """Recuento de lo que se llevaría por delante el borrado, por tabla."""
    return db.session.execute(db.text("""
        WITH s AS (SELECT id FROM public.solicitudes WHERE expediente_id = :eid),
             f AS (SELECT id FROM public.fases WHERE solicitud_id IN (SELECT id FROM s)),
             t AS (SELECT id FROM public.tramites WHERE fase_id IN (SELECT id FROM f)),
             ta AS (SELECT id FROM public.tareas WHERE tramite_id IN (SELECT id FROM t)),
             d AS (SELECT id FROM public.documentos WHERE expediente_id = :eid)
        SELECT (SELECT count(*) FROM s)  AS solicitudes,
               (SELECT count(*) FROM f)  AS fases,
               (SELECT count(*) FROM t)  AS tramites,
               (SELECT count(*) FROM ta) AS tareas,
               (SELECT count(*) FROM d)  AS documentos,
               (SELECT count(*) FROM public.documentos_tarea WHERE tarea_id IN (SELECT id FROM ta)) AS vinculos,
               (SELECT count(*) FROM public.notificaciones   WHERE tarea_id IN (SELECT id FROM ta)) AS notificaciones,
               (SELECT count(*) FROM public.diagnosticos     WHERE documento_id IN (SELECT id FROM d)) AS diagnosticos,
               (SELECT count(*) FROM public.organismos_expediente WHERE expediente_id = :eid) AS organismos
    """), {'eid': expediente_id}).mappings().one()


def _ruta_pool(numero_at):
    base = app.config.get('FILESYSTEM_BASE') or ''
    if not base:
        return None
    ruta = os.path.join(base, f'AT-{numero_at}')
    return ruta if os.path.isdir(ruta) else None


# ---------------------------------------------------------------------------
# Borrado
# ---------------------------------------------------------------------------

# Tablas cuyas filas pueden tener rastro en bitacora (que no tiene FK: guarda
# tabla + registro_id sueltos, así que hay que limpiarla a mano).
TABLAS_CON_BITACORA = ('expedientes', 'solicitudes', 'fases', 'tramites', 'tareas', 'documentos')


def _borrar_expediente(exp, con_ficheros):
    """Borra un expediente completo. Una transacción: o entero o nada."""
    eid = exp['expediente_id']
    numero_at = exp['numero_at']
    p = {'eid': eid}

    ex = db.session.execute

    # Ids implicados, recogidos ANTES de borrar (los necesita la bitácora, que
    # no tiene FK que la arrastre).
    ids = {
        'solicitudes': [r[0] for r in ex(db.text(
            "SELECT id FROM public.solicitudes WHERE expediente_id = :eid"), p)],
        'documentos': [r[0] for r in ex(db.text(
            "SELECT id FROM public.documentos WHERE expediente_id = :eid"), p)],
    }
    ids['fases'] = [r[0] for r in ex(db.text(
        "SELECT id FROM public.fases WHERE solicitud_id = ANY(:v)"),
        {'v': ids['solicitudes'] or [0]})]
    ids['tramites'] = [r[0] for r in ex(db.text(
        "SELECT id FROM public.tramites WHERE fase_id = ANY(:v)"),
        {'v': ids['fases'] or [0]})]
    ids['tareas'] = [r[0] for r in ex(db.text(
        "SELECT id FROM public.tareas WHERE tramite_id = ANY(:v)"),
        {'v': ids['tramites'] or [0]})]
    ids['expedientes'] = [eid]

    # Referencias entrantes desde fuera del expediente: si existen, no borramos
    # (sería un borrado silencioso de algo que otro expediente usa).
    ajenas = ex(db.text("""
        SELECT count(*) FROM public.solicitudes
        WHERE solicitud_afectada_id = ANY(:sols) AND expediente_id <> :eid
    """), {'sols': ids['solicitudes'] or [0], 'eid': eid}).scalar()
    if ajenas:
        raise RuntimeError(
            f'{ajenas} solicitud(es) de otros expedientes apuntan a este por '
            'solicitud_afectada_id — resuélvelo a mano antes de borrar.')

    try:
        # 1. Neutralizar las referencias a documentos que sobreviven al borrado
        #    de la cadena (todas NO ACTION: sin esto, el DELETE de documentos falla).
        ex(db.text("UPDATE public.fases SET documento_resultado_id = NULL "
                   "WHERE solicitud_id = ANY(:v)"), {'v': ids['solicitudes'] or [0]})
        ex(db.text("UPDATE public.solicitudes SET documento_cierre_id = NULL, "
                   "documento_solicitud_id = NULL WHERE expediente_id = :eid"), p)
        ex(db.text("UPDATE public.organismos_expediente SET documento_id = NULL, "
                   "condicionados_doc_id = NULL WHERE expediente_id = :eid"), p)
        ex(db.text("UPDATE public.interesados_expediente SET fuente_doc_id = NULL "
                   "WHERE expediente_id = :eid"), p)

        # 2. Hijos de documentos sin cascada
        for tabla in ('certificados', 'diagnosticos', 'documentos_requisito'):
            ex(db.text(f"DELETE FROM public.{tabla} WHERE documento_id = ANY(:v)"),
               {'v': ids['documentos'] or [0]})

        # 3. Colgados de fase/expediente sin cascada
        ex(db.text("DELETE FROM public.resoluciones WHERE fase_id = ANY(:v)"),
           {'v': ids['fases'] or [0]})
        ex(db.text("DELETE FROM public.informaciones_publicas WHERE fase_id = ANY(:v)"),
           {'v': ids['fases'] or [0]})
        ex(db.text("DELETE FROM public.certificados_fase WHERE expediente_id = :eid"), p)

        # 4. Histórico de titulares: apunta a solicitudes sin cascada
        ex(db.text("DELETE FROM public.historico_titulares_expediente "
                   "WHERE expediente_id = :eid OR solicitud_cambio_id = ANY(:v)"),
           {'eid': eid, 'v': ids['solicitudes'] or [0]})

        # 5. Cadena principal: solicitudes arrastra fases → trámites → tareas →
        #    documentos_tarea / notificaciones / organismos / alegantes (CASCADE).
        ex(db.text("DELETE FROM public.solicitudes WHERE expediente_id = :eid"), p)
        ex(db.text("DELETE FROM public.documentos WHERE expediente_id = :eid"), p)
        ex(db.text("DELETE FROM public.expedientes WHERE id = :eid"), p)

        # 6. Proyecto: solo si no lo comparte otro expediente.
        if exp['proyecto_id']:
            otros = ex(db.text("SELECT count(*) FROM public.expedientes WHERE proyecto_id = :pid"),
                       {'pid': exp['proyecto_id']}).scalar()
            if otros == 0:
                ex(db.text("DELETE FROM public.proyectos WHERE id = :pid"),
                   {'pid': exp['proyecto_id']})
            else:
                print(f"    proyecto {exp['proyecto_id']} conservado: lo usan {otros} expediente(s) más.")

        # 7. Bitácora (sin FK: se limpia por tabla + registro_id).
        n_bitacora = 0
        for tabla in TABLAS_CON_BITACORA:
            r = ex(db.text("DELETE FROM public.bitacora WHERE tabla = :t AND registro_id = ANY(:v)"),
                   {'t': tabla, 'v': ids.get(tabla) or [0]})
            n_bitacora += r.rowcount or 0

        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    print(f"  AT-{numero_at} borrado (expediente {eid}); {n_bitacora} fila(s) de bitácora.")

    # 8. Ficheros físicos, fuera de la transacción y solo bajo petición expresa.
    ruta = _ruta_pool(numero_at)
    if ruta and con_ficheros:
        shutil.rmtree(ruta)
        print(f"    ficheros borrados: {ruta}")
    elif ruta:
        print(f"    ficheros CONSERVADOS en {ruta} (usa --con-ficheros para borrarlos)")


# ---------------------------------------------------------------------------
# Entrada
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=f'Borra expedientes dummy marcados {MARCA}.')
    parser.add_argument('--borrar', action='store_true',
                        help='ejecuta el borrado (por defecto solo informa)')
    parser.add_argument('--at', default='',
                        help='limita a estos números de expediente, separados por comas')
    parser.add_argument('--con-ficheros', action='store_true',
                        help='borra también FILESYSTEM_BASE/AT-N/ (irreversible)')
    parser.add_argument('--si', action='store_true',
                        help='no pide confirmación interactiva')
    args = parser.parse_args()

    ats_filtro = {int(x) for x in args.at.split(',') if x.strip()} if args.at else set()

    with app.app_context():
        _verificar_cobertura_esquema()

        candidatos = _expedientes_reciclables(ats_filtro)
        if not candidatos:
            print(f'No hay expedientes marcados {MARCA}' +
                  (f' entre AT-{sorted(ats_filtro)}.' if ats_filtro else '.'))
            return

        print(f'\nExpedientes marcados {MARCA}:')
        for exp in candidatos:
            inv = _inventario(exp['expediente_id'])
            ruta = _ruta_pool(exp['numero_at'])
            print(f"  AT-{exp['numero_at']} (id={exp['expediente_id']}): "
                  f"{inv['solicitudes']} solicitud(es), {inv['fases']} fase(s), "
                  f"{inv['tramites']} trámite(s), {inv['tareas']} tarea(s), "
                  f"{inv['documentos']} documento(s), {inv['vinculos']} vínculo(s), "
                  f"{inv['notificaciones']} notificación(es), {inv['diagnosticos']} diagnóstico(s), "
                  f"{inv['organismos']} organismo(s)"
                  + (f" · ficheros en {ruta}" if ruta else ' · sin carpeta de ficheros'))

        if not args.borrar:
            print('\nSimulación: no se ha borrado nada. Añade --borrar para ejecutar.')
            return

        if not args.si:
            print(f'\nSe van a borrar {len(candidatos)} expediente(s), sin vuelta atrás.')
            if input('Escribe BORRAR para confirmar: ').strip() != 'BORRAR':
                print('Cancelado.')
                return

        print('')
        fallidos = 0
        for exp in candidatos:
            try:
                _borrar_expediente(exp, args.con_ficheros)
            except Exception as e:      # un expediente que falla no aborta el resto
                fallidos += 1
                print(f"  AT-{exp['numero_at']}: ERROR — {e}")
        print(f'\nHecho: {len(candidatos) - fallidos} borrado(s), {fallidos} con error.')


if __name__ == '__main__':
    main()

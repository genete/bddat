"""
Tests issue #395 — ConsultaNombrada 'organismos_consulta'.

Bloques:
  A) Seed — el registro existe en BD con los campos correctos.
  B) SQL  — la consulta se ejecuta sin errores y devuelve las columnas esperadas.

Todos los tests requieren app_ctx (BD real) porque leen datos insertados
por la migración seed.

El fixture `organismos_data` inserta datos de prueba en un SAVEPOINT y
los descarta al salir, sin dejar rastro en la BD.
"""
from types import SimpleNamespace

import pytest
from sqlalchemy import text


NOMBRE = 'organismos_consulta'
CAMPOS_ESPERADOS = {
    'organismo_nombre',
    'organismo_nif',
    'organismo_plazo_legal',
    'organismo_resultado',
    'organismo_fecha_envio',
    'organismo_fecha_respuesta',
}


@pytest.fixture()
def organismos_data(app_ctx):
    """
    Inserta en SAVEPOINT dos organismos de prueba sobre el primer expediente
    con fases que encuentre en la BD de desarrollo:
      - ORG1 (Endesa): ciclo completo — separata enviada + respuesta recibida
      - ORG2 (Sevillana): solo separata enviada, sin respuesta

    Todos los IDs (expediente/fase, organismos, catálogo de trámite/tarea)
    se resuelven por consulta, no por PK fija (#814 — el AT-2001 fijo que
    usaba esta fixture ya no existe, y hardcodear otro PK volvería a ser
    igual de frágil).

    Hace ROLLBACK al salir — no deja rastro en la BD.
    Devuelve el expediente_id usado.
    """
    from app import db

    conn = db.engine.connect()
    sp = conn.begin_nested()
    try:
        exp_id, fase_id = conn.execute(text(
            "SELECT e.id, f.id FROM expedientes e "
            "JOIN solicitudes s ON s.expediente_id = e.id "
            "JOIN fases f ON f.solicitud_id = s.id "
            "ORDER BY e.id, f.id LIMIT 1"
        )).first() or (None, None)
        if exp_id is None:
            pytest.skip('No hay expedientes con fases en la BD de desarrollo')

        # Dos organismos cualesquiera de los que se consultan, por rol y no por
        # NIF concreto (#849): los de la base de desarrollo no están en la de
        # tests, y clavarlos aquí saltaba los cuatro tests que usan el fixture.
        organismos = conn.execute(text(
            "SELECT id, nif FROM entidades WHERE rol_consultado IS TRUE "
            "AND activo IS TRUE ORDER BY id LIMIT 2"
        )).all()
        assert len(organismos) == 2, (
            'la semilla debe traer al menos dos entidades con rol_consultado')
        (org1_id, nif1), (org2_id, nif2) = organismos

        tipo_tramite_id = conn.execute(text(
            "SELECT id FROM tipos_tramites WHERE codigo = 'CONSULTA_SEPARATA'"
        )).scalar()
        tipo_notificar_id = conn.execute(text(
            "SELECT id FROM tipos_tareas WHERE codigo = 'NOTIFICAR'"
        )).scalar()
        tipo_analizar_id = conn.execute(text(
            "SELECT id FROM tipos_tareas WHERE codigo = 'ANALIZAR'"
        )).scalar()

        _EXP_ID, _FASE_ID = exp_id, fase_id
        _ORG1_ID, _ORG2_ID = org1_id, org2_id
        _TIPO_TRAMITE_ID, _TIPO_NOTIFICAR_ID, _TIPO_ANALIZAR_ID = (
            tipo_tramite_id, tipo_notificar_id, tipo_analizar_id
        )

        # ── Organismo 1: ciclo completo ──────────────────────────────────
        tr1 = conn.execute(text(
            "INSERT INTO public.tramites (fase_id, tipo_tramite_id) "
            "VALUES (:f,:tt) RETURNING id"
        ), {"f": _FASE_ID, "tt": _TIPO_TRAMITE_ID}).scalar()

        doc_notif1 = conn.execute(text(
            "INSERT INTO public.documentos (expediente_id, url, fecha_administrativa) "
            "VALUES (:e,'test://sep_endesa.docx','2026-03-01') RETURNING id"
        ), {"e": _EXP_ID}).scalar()

        doc_resp1 = conn.execute(text(
            "INSERT INTO public.documentos (expediente_id, url, fecha_administrativa) "
            "VALUES (:e,'test://resp_endesa.pdf','2026-03-20') RETURNING id"
        ), {"e": _EXP_ID}).scalar()

        # NOTIFICAR de ORG1 — vínculo PRODUCIDO en documentos_tarea (ADR-010)
        t_notif1 = conn.execute(text(
            "INSERT INTO public.tareas (tramite_id, tipo_tarea_id) "
            "VALUES (:tr,:tt) RETURNING id"
        ), {"tr": tr1, "tt": _TIPO_NOTIFICAR_ID}).scalar()
        conn.execute(text(
            "INSERT INTO public.documentos_tarea (tarea_id, documento_id, rol) "
            "VALUES (:t,:d,'PRODUCIDO')"
        ), {"t": t_notif1, "d": doc_notif1})

        # ANALIZAR de ORG1 — vínculo CONSUMIDO en documentos_tarea
        t_anal1 = conn.execute(text(
            "INSERT INTO public.tareas (tramite_id, tipo_tarea_id) "
            "VALUES (:tr,:tt) RETURNING id"
        ), {"tr": tr1, "tt": _TIPO_ANALIZAR_ID}).scalar()
        conn.execute(text(
            "INSERT INTO public.documentos_tarea (tarea_id, documento_id, rol) "
            "VALUES (:t,:d,'CONSUMIDO')"
        ), {"t": t_anal1, "d": doc_resp1})

        oe1 = conn.execute(text(
            "INSERT INTO public.organismos_expediente "
            "(expediente_id, fase_id, organismo_id, via, resultado, plazo_legal_dias) "
            "VALUES (:e,:f,:o,'consulta','cerrado_favorable',30) RETURNING id"
        ), {"e": _EXP_ID, "f": _FASE_ID, "o": _ORG1_ID}).scalar()
        conn.execute(text(
            "INSERT INTO public.tramites_organismos (tramite_id, organismo_expediente_id) "
            "VALUES (:tr,:oe)"
        ), {"tr": tr1, "oe": oe1})

        # ── Organismo 2: sin respuesta ───────────────────────────────────
        tr2 = conn.execute(text(
            "INSERT INTO public.tramites (fase_id, tipo_tramite_id) "
            "VALUES (:f,:tt) RETURNING id"
        ), {"f": _FASE_ID, "tt": _TIPO_TRAMITE_ID}).scalar()

        doc_notif2 = conn.execute(text(
            "INSERT INTO public.documentos (expediente_id, url, fecha_administrativa) "
            "VALUES (:e,'test://sep_sevillana.docx','2026-03-01') RETURNING id"
        ), {"e": _EXP_ID}).scalar()

        # NOTIFICAR de ORG2 — vínculo PRODUCIDO en documentos_tarea
        t_notif2 = conn.execute(text(
            "INSERT INTO public.tareas (tramite_id, tipo_tarea_id) "
            "VALUES (:tr,:tt) RETURNING id"
        ), {"tr": tr2, "tt": _TIPO_NOTIFICAR_ID}).scalar()
        conn.execute(text(
            "INSERT INTO public.documentos_tarea (tarea_id, documento_id, rol) "
            "VALUES (:t,:d,'PRODUCIDO')"
        ), {"t": t_notif2, "d": doc_notif2})

        # Sin resultado (NULL): ciclo en curso — separata enviada, aún sin respuesta.
        oe2 = conn.execute(text(
            "INSERT INTO public.organismos_expediente "
            "(expediente_id, fase_id, organismo_id, via, plazo_legal_dias) "
            "VALUES (:e,:f,:o,'consulta',30) RETURNING id"
        ), {"e": _EXP_ID, "f": _FASE_ID, "o": _ORG2_ID}).scalar()
        conn.execute(text(
            "INSERT INTO public.tramites_organismos (tramite_id, organismo_expediente_id) "
            "VALUES (:tr,:oe)"
        ), {"tr": tr2, "oe": oe2})

        yield SimpleNamespace(exp_id=_EXP_ID, conn=conn,
                              nif_ciclo_completo=nif1, nif_sin_respuesta=nif2)

    finally:
        sp.rollback()
        conn.close()


# ───────────────────────────────────────────────────────────────────────────────
# A) Seed
# ───────────────────────────────────────────────────────────────────────────────

class TestSeedOrganismosConsulta:

    def test_registro_existe(self, app_ctx):
        from app.models.consultas_nombradas import ConsultaNombrada
        cn = ConsultaNombrada.query.filter_by(nombre=NOMBRE).first()
        assert cn is not None, f"Falta el registro '{NOMBRE}' en consultas_nombradas"

    def test_activo(self, app_ctx):
        from app.models.consultas_nombradas import ConsultaNombrada
        cn = ConsultaNombrada.query.filter_by(nombre=NOMBRE).first()
        assert cn.activo is True

    def test_descripcion_no_vacia(self, app_ctx):
        from app.models.consultas_nombradas import ConsultaNombrada
        cn = ConsultaNombrada.query.filter_by(nombre=NOMBRE).first()
        assert cn.descripcion and len(cn.descripcion) > 5

    def test_columnas_declara_seis_campos(self, app_ctx):
        from app.models.consultas_nombradas import ConsultaNombrada
        cn = ConsultaNombrada.query.filter_by(nombre=NOMBRE).first()
        campos = {c['campo'] for c in cn.columnas}
        assert campos == CAMPOS_ESPERADOS

    def test_sql_contiene_expediente_id(self, app_ctx):
        from app.models.consultas_nombradas import ConsultaNombrada
        cn = ConsultaNombrada.query.filter_by(nombre=NOMBRE).first()
        assert ':expediente_id' in cn.sql

    def test_sql_contiene_organismos_expediente(self, app_ctx):
        from app.models.consultas_nombradas import ConsultaNombrada
        cn = ConsultaNombrada.query.filter_by(nombre=NOMBRE).first()
        assert 'organismos_expediente' in cn.sql


# ───────────────────────────────────────────────────────────────────────────────
# B) SQL
# ───────────────────────────────────────────────────────────────────────────────

class TestSQLOrganismosConsulta:

    def _ejecutar(self, conn, expediente_id):
        """Ejecuta la consulta almacenada usando la misma conexión del SAVEPOINT."""
        sql_text = conn.execute(text(
            "SELECT sql FROM public.consultas_nombradas WHERE nombre = :n"
        ), {"n": NOMBRE}).scalar()
        assert sql_text, f"Consulta '{NOMBRE}' no encontrada"
        return conn.execute(
            text(sql_text), {"expediente_id": expediente_id}
        ).mappings().all()

    def test_sql_ejecuta_sin_error(self, app_ctx):
        """Con expediente_id=0 la consulta devuelve lista vacía sin lanzar excepción."""
        from app import db
        from app.models.consultas_nombradas import ConsultaNombrada
        cn = ConsultaNombrada.query.filter_by(nombre=NOMBRE).first()
        rows = db.session.execute(
            text(cn.sql), {"expediente_id": 0}
        ).mappings().all()
        assert isinstance(rows, list)

    def test_columnas_resultado_coinciden_con_declaradas(self, organismos_data):
        """Las claves del resultado coinciden exactamente con los campos declarados."""
        rows = self._ejecutar(organismos_data.conn, organismos_data.exp_id)
        assert rows, "El fixture no devolvió filas"
        assert set(rows[0].keys()) == CAMPOS_ESPERADOS

    def test_resultado_es_lista_unica_por_organismo(self, organismos_data):
        """Cada organismo aparece exactamente una vez (no hay duplicados por tarea)."""
        rows = self._ejecutar(organismos_data.conn, organismos_data.exp_id)
        nombres = [r['organismo_nombre'] for r in rows]
        assert len(nombres) == len(set(nombres)), (
            f"Duplicados detectados: {nombres} — posible producto cartesiano"
        )

    def test_dos_organismos_devueltos(self, organismos_data):
        """El fixture inserta 2 organismos; la consulta devuelve exactamente 2 filas."""
        rows = self._ejecutar(organismos_data.conn, organismos_data.exp_id)
        assert len(rows) == 2

    def test_campos_ciclo_completo(self, organismos_data):
        """El organismo con ciclo completo tiene ambas fechas; el otro solo fecha_envio."""
        rows = self._ejecutar(organismos_data.conn, organismos_data.exp_id)
        by_nif = {r['organismo_nif']: r for r in rows}

        completo = by_nif[organismos_data.nif_ciclo_completo]
        assert completo['organismo_resultado'] == 'cerrado_favorable'
        assert completo['organismo_fecha_envio'] == '01/03/2026'
        assert completo['organismo_fecha_respuesta'] == '20/03/2026'

        sin_respuesta = by_nif[organismos_data.nif_sin_respuesta]
        assert sin_respuesta['organismo_resultado'] is None
        assert sin_respuesta['organismo_fecha_envio'] == '01/03/2026'
        assert sin_respuesta['organismo_fecha_respuesta'] is None

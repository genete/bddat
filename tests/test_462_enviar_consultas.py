"""
Tests #462 / #396 bloque 5 — calcular_plazo_consulta (lee catalogo_plazos real)
y enviar_consultas() / crear_traslado() con ResultadoMutacion.

Patrón: BD real bajo `app_ctx` (SAVEPOINT, revierte todo al terminar). Desde el
bloque 5, calcular_plazo_consulta() ya no admite MagicMocks puros: consulta
TipoTarea/TipoTramite/catalogo_plazos reales y evalúa las variables del motor
(es_solicitud_aac_pura, tiene_solicitud_aap_favorable) sobre un
ExpedienteContext real — es justo el mecanismo que sustituye a la copia manual
de la norma que había antes.
"""
import pytest


def _tipo(modelo, valor, campo='codigo'):
    fila = modelo.query.filter_by(**{campo: valor}).first()
    if fila is None:
        pytest.skip(f'{modelo.__name__} {campo}={valor!r} no está en el catálogo de esta BD')
    return fila


def _expediente():
    from app.models.expedientes import Expediente
    exp = Expediente.query.first()
    if exp is None:
        pytest.skip('No hay expedientes en la BD de desarrollo')
    return exp


def _entidad():
    from app.models.entidad import Entidad
    ent = Entidad.query.first()
    if ent is None:
        pytest.skip('No hay entidades en la BD de desarrollo')
    return ent


def _solicitud(db, expediente, siglas):
    from app.models.solicitudes import Solicitud
    from app.models.tipos_solicitudes import TipoSolicitud
    tipo = _tipo(TipoSolicitud, siglas, campo='siglas')
    sol = Solicitud(expediente_id=expediente.id, entidad_id=_entidad().id,
                     tipo_solicitud_id=tipo.id)
    db.session.add(sol)
    db.session.flush()
    return sol


def _fase(db, solicitud, codigo_tipo_fase):
    from app.models.fases import Fase
    from app.models.tipos_fases import TipoFase
    tipo = _tipo(TipoFase, codigo_tipo_fase)
    fase = Fase(solicitud_id=solicitud.id, tipo_fase_id=tipo.id)
    db.session.add(fase)
    db.session.flush()
    return fase


def _cerrar_fase_resolucion(db, expediente, solicitud, codigo_resultado):
    """Fase RESOLUCION (finalizadora) de `solicitud`, cerrada con `codigo_resultado`."""
    from app.models.documentos import Documento
    from app.models.tipos_documentos import TipoDocumento
    from app.models.tipos_resultados_fases import TipoResultadoFase

    fase = _fase(db, solicitud, 'RESOLUCION')
    tipo_doc = TipoDocumento.query.first()
    if tipo_doc is None:
        pytest.skip('No hay tipos de documento en la BD de desarrollo')
    doc = Documento(expediente_id=expediente.id, tipo_doc_id=tipo_doc.id,
                     url='bddat://test-396-bloque5/resultado-resolucion')
    db.session.add(doc)
    db.session.flush()
    fase.resultado_fase_id = _tipo(TipoResultadoFase, codigo_resultado).id
    fase.documento_resultado_id = doc.id
    db.session.flush()
    return fase


class TestCalcularPlazoConsulta:
    """calcular_plazo_consulta(fase): 30 días general, 15 si AAC pura + AAP
    previa con RESOLUCION favorable (art. 131.1 párr. 2 RD 1955/2000)."""

    def test_plazo_general_aap(self, app_ctx):
        from app import db
        from app.services.consultas_organismos import calcular_plazo_consulta
        exp = _expediente()
        sol = _solicitud(db, exp, 'AAP')
        fase_consultas = _fase(db, sol, 'CONSULTAS')
        assert calcular_plazo_consulta(fase_consultas) == 30

    def test_plazo_general_aap_aac_combinado(self, app_ctx):
        from app import db
        from app.services.consultas_organismos import calcular_plazo_consulta
        exp = _expediente()
        sol = _solicitud(db, exp, 'AAP+AAC')
        fase_consultas = _fase(db, sol, 'CONSULTAS')
        assert calcular_plazo_consulta(fase_consultas) == 30

    def test_plazo_general_aac_sin_aap_previa(self, app_ctx):
        from app import db
        from app.services.consultas_organismos import calcular_plazo_consulta
        exp = _expediente()
        sol = _solicitud(db, exp, 'AAC')
        fase_consultas = _fase(db, sol, 'CONSULTAS')
        assert calcular_plazo_consulta(fase_consultas) == 30

    def test_plazo_reducido_aac_pura_con_aap_favorable(self, app_ctx):
        """AAC pura + AAP previa (mismo expediente) con RESOLUCION FAVORABLE → 15."""
        from app import db
        from app.services.consultas_organismos import calcular_plazo_consulta
        exp = _expediente()
        sol_aac = _solicitud(db, exp, 'AAC')
        sol_aap = _solicitud(db, exp, 'AAP')
        _cerrar_fase_resolucion(db, exp, sol_aap, 'FAVORABLE')
        fase_consultas = _fase(db, sol_aac, 'CONSULTAS')
        assert calcular_plazo_consulta(fase_consultas) == 15

    def test_plazo_reducido_con_favorable_condicionado(self, app_ctx):
        """FAVORABLE_CONDICIONADO también reduce a 15 (RESULTADO_FASE_FAVORABLE_CODIGOS)."""
        from app import db
        from app.services.consultas_organismos import calcular_plazo_consulta
        exp = _expediente()
        sol_aac = _solicitud(db, exp, 'AAC')
        sol_aap = _solicitud(db, exp, 'AAP')
        _cerrar_fase_resolucion(db, exp, sol_aap, 'FAVORABLE_CONDICIONADO')
        fase_consultas = _fase(db, sol_aac, 'CONSULTAS')
        assert calcular_plazo_consulta(fase_consultas) == 15

    def test_dup_excluye_reduccion(self, app_ctx):
        """AAC+DUP no es AAC pura → 30 días aunque haya AAP previa favorable."""
        from app import db
        from app.services.consultas_organismos import calcular_plazo_consulta
        exp = _expediente()
        sol_aac_dup = _solicitud(db, exp, 'AAC+DUP')
        sol_aap = _solicitud(db, exp, 'AAP')
        _cerrar_fase_resolucion(db, exp, sol_aap, 'FAVORABLE')
        fase_consultas = _fase(db, sol_aac_dup, 'CONSULTAS')
        assert calcular_plazo_consulta(fase_consultas) == 30

    def test_aap_previa_no_favorable_no_reduce(self, app_ctx):
        """AAP previa existe pero su RESOLUCION cierra DESFAVORABLE → 30."""
        from app import db
        from app.services.consultas_organismos import calcular_plazo_consulta
        exp = _expediente()
        sol_aac = _solicitud(db, exp, 'AAC')
        sol_aap = _solicitud(db, exp, 'AAP')
        _cerrar_fase_resolucion(db, exp, sol_aap, 'DESFAVORABLE')
        fase_consultas = _fase(db, sol_aac, 'CONSULTAS')
        assert calcular_plazo_consulta(fase_consultas) == 30

    def test_aap_previa_sin_cerrar_no_reduce(self, app_ctx):
        """AAP previa existe pero su fase RESOLUCION sigue sin cerrar → 30."""
        from app import db
        from app.services.consultas_organismos import calcular_plazo_consulta
        exp = _expediente()
        sol_aac = _solicitud(db, exp, 'AAC')
        sol_aap = _solicitud(db, exp, 'AAP')
        _fase(db, sol_aap, 'RESOLUCION')  # sin resultado ni documento
        fase_consultas = _fase(db, sol_aac, 'CONSULTAS')
        assert calcular_plazo_consulta(fase_consultas) == 30

    def test_solicitud_actual_no_se_evalua_como_aap_previa(self, app_ctx):
        """La propia solicitud AAP+AAC no cuenta como 'AAP previa' de sí misma."""
        from app import db
        from app.services.consultas_organismos import calcular_plazo_consulta
        exp = _expediente()
        sol = _solicitud(db, exp, 'AAP+AAC')
        _cerrar_fase_resolucion(db, exp, sol, 'FAVORABLE')
        fase_consultas = _fase(db, sol, 'CONSULTAS')
        # No es AAC pura (contiene AAP) → 30 de todos modos, pero además la
        # variable tiene_solicitud_aap_favorable excluye la solicitud actual
        # del recorrido (ver docstring calculado.py).
        assert calcular_plazo_consulta(fase_consultas) == 30


class TestEnviarConsultas:
    """enviar_consultas(fase, form) real, contra BD (antes: reimplementaba el
    filtro sobre MagicMocks sin llamar nunca a la función — #396 bloque 7."""

    def _organismo(self, db, expediente, fase, entidad, via='consulta'):
        from app.models.organismos_expediente import OrganismoExpediente
        oe = OrganismoExpediente(expediente_id=expediente.id, fase_id=fase.id,
                                  organismo_id=entidad.id, via=via,
                                  resultado='exonerado' if via == 'declaracion_responsable' else None)
        db.session.add(oe)
        db.session.flush()
        return oe

    def _entidad_consultada(self):
        from app.models.entidad import Entidad
        ent = Entidad.query.filter_by(rol_consultado=True).first()
        if ent is None:
            pytest.skip('No hay entidades rol_consultado=True en la BD de desarrollo')
        return ent

    def test_crea_separata_por_organismo_pendiente(self, app_ctx):
        from app import db
        from app.services.consultas_organismos import enviar_consultas
        exp = _expediente()
        sol = _solicitud(db, exp, 'AAP')
        fase = _fase(db, sol, 'CONSULTAS')
        ent = self._entidad_consultada()
        oe = self._organismo(db, exp, fase, ent)

        res = enviar_consultas(fase, {})

        assert res.ok, res.error
        assert len(res.ids) == 1
        from app.models.tramites_organismos import TramiteOrganismo
        vinculo = TramiteOrganismo.query.filter_by(organismo_expediente_id=oe.id).first()
        assert vinculo is not None
        assert vinculo.tramite_id == res.ids[0]
        assert oe.plazo_legal_dias == 30

    def test_idempotente_no_duplica_separata(self, app_ctx):
        """Segunda llamada tras la primera: el organismo ya no está pendiente."""
        from app import db
        from app.services.consultas_organismos import enviar_consultas
        exp = _expediente()
        sol = _solicitud(db, exp, 'AAP')
        fase = _fase(db, sol, 'CONSULTAS')
        ent = self._entidad_consultada()
        self._organismo(db, exp, fase, ent)

        primero = enviar_consultas(fase, {})
        assert primero.ok and len(primero.ids) == 1

        segundo = enviar_consultas(fase, {})
        assert segundo.ok
        assert segundo.ids == []

    def test_declaracion_responsable_no_se_envia(self, app_ctx):
        """via=declaracion_responsable nunca genera separata."""
        from app import db
        from app.services.consultas_organismos import enviar_consultas
        exp = _expediente()
        sol = _solicitud(db, exp, 'AAP')
        fase = _fase(db, sol, 'CONSULTAS')
        ent = self._entidad_consultada()
        self._organismo(db, exp, fase, ent, via='declaracion_responsable')

        res = enviar_consultas(fase, {})
        assert res.ok
        assert res.ids == []

    def test_sin_pendientes_ok_vacio(self, app_ctx):
        from app import db
        from app.services.consultas_organismos import enviar_consultas
        exp = _expediente()
        sol = _solicitud(db, exp, 'AAP')
        fase = _fase(db, sol, 'CONSULTAS')

        res = enviar_consultas(fase, {})
        assert res.ok
        assert res.ids == []

    def test_bypass_sin_justificacion_falla(self, app_ctx):
        from app import db
        from app.services.consultas_organismos import enviar_consultas
        exp = _expediente()
        sol = _solicitud(db, exp, 'AAP')
        fase = _fase(db, sol, 'CONSULTAS')

        res = enviar_consultas(fase, {'bypass': True})
        assert not res.ok
        assert 'justificacion' in res.error

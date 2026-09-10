"""Tests issue #470 — CERT_FIN_IP_CONSULTAS: bug fix fase_ip_finalizada,
reglas motor y servicio de generación del certificado."""


# ---------------------------------------------------------------------------
# Stubs mínimos de duck-typing
# ---------------------------------------------------------------------------

class _StubTipoFase:
    def __init__(self, codigo): self.codigo = codigo


class _StubDoc:
    def __init__(self, fecha=None):
        self.fecha_administrativa = fecha


class _StubFase:
    def __init__(self, codigo, finalizada=False, doc_resultado=None, id=1, reformado_id=None):
        self.id = id
        self.tipo_fase = _StubTipoFase(codigo)
        self.finalizada = finalizada
        self.documento_resultado = doc_resultado
        self.reformado_id = reformado_id


class _StubSolicitud:
    def __init__(self, fases): self.fases = fases


class _StubCtxConSolicitud:
    def __init__(self, fases):
        self.solicitud = _StubSolicitud(fases)


# ---------------------------------------------------------------------------
# A) Bug fix fase_ip_finalizada — ahora usa ctx.solicitud
# ---------------------------------------------------------------------------

def _get_variable(nombre):
    import app.services.variables.calculado  # noqa: F401
    from app.services.variables import _REGISTRY
    fn = _REGISTRY.get(nombre)
    assert fn is not None, f'Variable {nombre!r} no encontrada en _REGISTRY'
    return fn


def test_fase_ip_finalizada_sin_solicitud_en_ctx():
    """Sin solicitud en contexto → False."""
    class _CtxSinSolicitud:
        solicitud = None

    assert _get_variable('fase_ip_finalizada')(_CtxSinSolicitud()) is False


def test_fase_ip_finalizada_solicitud_sin_ip():
    """Solicitud sin fase IP → False."""
    ctx = _StubCtxConSolicitud([
        _StubFase('CONSULTAS', finalizada=True),
    ])
    assert _get_variable('fase_ip_finalizada')(ctx) is False


def test_fase_ip_finalizada_ip_no_finalizada():
    """Fase IP existe pero no está finalizada → False."""
    ctx = _StubCtxConSolicitud([
        _StubFase('INFORMACION_PUBLICA', finalizada=False),
    ])
    assert _get_variable('fase_ip_finalizada')(ctx) is False


def test_fase_ip_finalizada_ip_finalizada():
    """Fase IP finalizada → True."""
    ctx = _StubCtxConSolicitud([
        _StubFase('INFORMACION_PUBLICA', finalizada=True),
        _StubFase('CONSULTAS', finalizada=True),
    ])
    assert _get_variable('fase_ip_finalizada')(ctx) is True


def test_fase_ip_finalizada_solo_mira_solicitud_en_ctx():
    """La variable NO recorre otras solicitudes del expediente — solo ctx.solicitud."""
    # ctx.solicitud no tiene IP; en una segunda solicitud hipotética sí habría IP.
    # La variable debe devolver False (no busca en ctx.expediente.solicitudes).
    ctx = _StubCtxConSolicitud([
        _StubFase('CONSULTAS', finalizada=True),
    ])
    assert _get_variable('fase_ip_finalizada')(ctx) is False


def test_fase_ip_finalizada_universal_con_reformado():
    """ADR-044 R5: con la IP de la versión inicial cerrada y la del reformado
    todavía abierta, la variable tiene que decir False — antes (existencial)
    decía True en cuanto encontraba la primera cerrada, y dejaba pasar la
    resolución mientras la segunda ronda de exposición pública seguía viva."""
    ctx = _StubCtxConSolicitud([
        _StubFase('INFORMACION_PUBLICA', finalizada=True, reformado_id=None, id=1),
        _StubFase('INFORMACION_PUBLICA', finalizada=False, reformado_id=7, id=2),
    ])
    assert _get_variable('fase_ip_finalizada')(ctx) is False


def test_fase_ip_finalizada_universal_dos_rondas_cerradas():
    """Con las dos rondas de IP cerradas, universal y existencial coinciden."""
    ctx = _StubCtxConSolicitud([
        _StubFase('INFORMACION_PUBLICA', finalizada=True, reformado_id=None, id=1),
        _StubFase('INFORMACION_PUBLICA', finalizada=True, reformado_id=7, id=2),
    ])
    assert _get_variable('fase_ip_finalizada')(ctx) is True


# ---------------------------------------------------------------------------
# A bis) existe_fase_finalizadora_cerrada — mismo patrón, huérfana hoy
# ---------------------------------------------------------------------------

class _StubTipoFaseFinalizadora(_StubTipoFase):
    def __init__(self, codigo, es_finalizadora=False):
        super().__init__(codigo)
        self.es_finalizadora = es_finalizadora


def test_existe_fase_finalizadora_cerrada_sin_solicitud():
    class _CtxSinSolicitud:
        solicitud = None
    assert _get_variable('existe_fase_finalizadora_cerrada')(_CtxSinSolicitud()) is False


def test_existe_fase_finalizadora_cerrada_sin_finalizadora():
    fase = _StubFase('ANALISIS_SOLICITUD', finalizada=True)
    fase.tipo_fase = _StubTipoFaseFinalizadora('ANALISIS_SOLICITUD', es_finalizadora=False)
    ctx = _StubCtxConSolicitud([fase])
    assert _get_variable('existe_fase_finalizadora_cerrada')(ctx) is False


def test_existe_fase_finalizadora_cerrada_universal_una_abierta():
    """Dos finalizadoras (ADR-045: AAP+AAC y DUP), solo una cerrada → False."""
    fase_cerrada = _StubFase('RESOLUCION', finalizada=True, id=1)
    fase_cerrada.tipo_fase = _StubTipoFaseFinalizadora('RESOLUCION', es_finalizadora=True)
    fase_abierta = _StubFase('RESOLUCION', finalizada=False, id=2)
    fase_abierta.tipo_fase = _StubTipoFaseFinalizadora('RESOLUCION', es_finalizadora=True)
    ctx = _StubCtxConSolicitud([fase_cerrada, fase_abierta])
    assert _get_variable('existe_fase_finalizadora_cerrada')(ctx) is False


def test_existe_fase_finalizadora_cerrada_todas_cerradas():
    fase_1 = _StubFase('RESOLUCION', finalizada=True, id=1)
    fase_1.tipo_fase = _StubTipoFaseFinalizadora('RESOLUCION', es_finalizadora=True)
    ctx = _StubCtxConSolicitud([fase_1])
    assert _get_variable('existe_fase_finalizadora_cerrada')(ctx) is True


# ---------------------------------------------------------------------------
# B) Servicio crear_cert_fin_ip_consultas — tests unitarios con stubs
# ---------------------------------------------------------------------------

def test_construir_datos_dos_fases():
    from app.services.cert_fin_ip_consultas import _construir_datos
    fases_info = [
        {'codigo': 'INFORMACION_PUBLICA', 'fase_id': 1, 'fecha_fin': '2026-03-10'},
        {'codigo': 'CONSULTAS',           'fase_id': 2, 'fecha_fin': '2026-04-05'},
    ]
    datos = _construir_datos(fases_info)
    assert datos['fecha_fin_ultima_fase'] == '2026-04-05'
    assert len(datos['fases_habilitantes']) == 2


def test_construir_datos_una_fase_sin_fecha():
    from app.services.cert_fin_ip_consultas import _construir_datos
    fases_info = [
        {'codigo': 'CONSULTAS', 'fase_id': 3, 'fecha_fin': None},
    ]
    datos = _construir_datos(fases_info)
    assert datos['fecha_fin_ultima_fase'] is None


def test_recoger_fases_solo_finalizadas():
    from app.services.cert_fin_ip_consultas import _recoger_fases

    doc_con_fecha = _StubDoc(fecha=None)
    doc_con_fecha.fecha_administrativa = None

    fases = [
        _StubFase('INFORMACION_PUBLICA', finalizada=True,
                  doc_resultado=_StubDoc()),
        _StubFase('CONSULTAS', finalizada=False),
        _StubFase('ANALISIS_SOLICITUD', finalizada=True),
    ]
    sol = _StubSolicitud(fases)
    resultado = _recoger_fases(sol)
    assert len(resultado) == 1
    assert resultado[0]['codigo'] == 'INFORMACION_PUBLICA'


def test_recoger_fases_vacio_si_ninguna_habilitante():
    from app.services.cert_fin_ip_consultas import _recoger_fases
    sol = _StubSolicitud([_StubFase('RESOLUCION', finalizada=True)])
    assert _recoger_fases(sol) == []


# ---------------------------------------------------------------------------
# B bis) Re-emisión por ronda (ADR-044 R5, #901)
# ---------------------------------------------------------------------------

class _StubReformado:
    def __init__(self, id): self.id = id


def test_recoger_fases_solo_la_ronda_pedida():
    """Con dos rondas de IP+Consultas, _recoger_fases de la ronda 2 no incluye
    las de la ronda 1 — cada certificado habla de su propia ronda."""
    from app.services.cert_fin_ip_consultas import _recoger_fases

    fases = [
        _StubFase('INFORMACION_PUBLICA', finalizada=True, reformado_id=None, id=1),
        _StubFase('CONSULTAS', finalizada=True, reformado_id=None, id=2),
        _StubFase('INFORMACION_PUBLICA', finalizada=True, reformado_id=7, id=3),
        _StubFase('CONSULTAS', finalizada=True, reformado_id=7, id=4),
    ]
    sol = _StubSolicitud(fases)

    ronda_2 = _recoger_fases(sol, _StubReformado(7))
    assert {f['fase_id'] for f in ronda_2} == {3, 4}

    ronda_1 = _recoger_fases(sol, None)
    assert {f['fase_id'] for f in ronda_1} == {1, 2}


def test_buscar_existente_no_confunde_solicitudes_ni_rondas(app_ctx):
    """El defecto de fondo (ADR-044 R5): antes de #901 se buscaba solo por
    expediente_id + tipo_doc_id, así que dos solicitudes del mismo expediente
    —o dos rondas de la misma solicitud— compartían certificado por error."""
    from app import db
    from app.services.cert_fin_ip_consultas import _buscar_existente
    from app.models.certificados import Certificado
    from app.models.documentos import Documento
    from app.models.tipos_documentos import TipoDocumento

    tipo_doc = TipoDocumento.query.filter_by(codigo='CERT_FIN_IP_CONSULTAS').first()
    assert tipo_doc is not None, 'catálogo sin CERT_FIN_IP_CONSULTAS — ¿migración aplicada?'

    from tests.conftest import ArbolESFTT
    arbol = ArbolESFTT(db)
    sol_a = arbol.solicitud_nueva()
    sol_b = arbol.solicitud_nueva()

    doc = Documento(expediente_id=sol_a.expediente_id, tipo_doc_id=tipo_doc.id,
                    url='bddat://certificados/0')
    db.session.add(doc)
    db.session.flush()
    cert_a = Certificado(documento_id=doc.id, solicitud_id=sol_a.id, reformado_id=None,
                         datos={})
    db.session.add(cert_a)
    db.session.flush()

    # Otra solicitud del mismo expediente: no ve el certificado de sol_a.
    assert _buscar_existente(sol_b.id, None) is None
    # La misma solicitud pero otra ronda: tampoco lo ve.
    assert _buscar_existente(sol_a.id, _StubReformado(99)) is None
    # La suya propia, sí.
    assert _buscar_existente(sol_a.id, None) is not None


# ---------------------------------------------------------------------------
# C) Motor: reglas BLOQUEAR presentes en BD
# ---------------------------------------------------------------------------

def test_reglas_bloquear_en_bd(app_ctx):
    """Las dos reglas BLOQUEAR para ANY/ANY/RESOLUCION están activas en BD."""
    from app.models.motor_reglas import ReglaMotor
    reglas = ReglaMotor.query.filter_by(
        accion='CREAR', sujeto='ANY/ANY/RESOLUCION', efecto='BLOQUEAR', activa=True,
    ).all()
    descripciones = {r.descripcion for r in reglas}
    assert 'Hay organismos pendientes de respuesta o análisis' in descripciones
    assert 'La fase de Información Pública no ha concluido' in descripciones


def test_regla_organismos_tiene_condicion(app_ctx):
    from app.models.motor_reglas import ReglaMotor
    regla = ReglaMotor.query.filter_by(
        descripcion='Hay organismos pendientes de respuesta o análisis',
        sujeto='ANY/ANY/RESOLUCION',
    ).first()
    assert regla is not None
    nombres = [c.variable.nombre for c in regla.condiciones]
    assert 'organismos_todos_terminados' in nombres


def test_regla_ip_tiene_dos_condiciones(app_ctx):
    from app.models.motor_reglas import ReglaMotor
    regla = ReglaMotor.query.filter_by(
        descripcion='La fase de Información Pública no ha concluido',
        sujeto='ANY/ANY/RESOLUCION',
    ).first()
    assert regla is not None
    nombres = [c.variable.nombre for c in regla.condiciones]
    assert 'fase_ip_finalizada' in nombres
    # #814: la condición de tipo (antes tipo_solicitud IN [2 combinaciones a
    # mano]) pasó a solicitud_incluye_dup — cubre cualquier combinación con
    # DUP, no solo las listadas. La exención de IP (DL 26/2021 DF 4ª) exige
    # además "sin AAU", cubierto por la regla hermana con instrumento_ambiental.
    assert 'solicitud_incluye_dup' in nombres

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
    def __init__(self, codigo, finalizada=False, doc_resultado=None, id=1):
        self.id = id
        self.tipo_fase = _StubTipoFase(codigo)
        self.finalizada = finalizada
        self.documento_resultado = doc_resultado


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
    assert 'tipo_solicitud' in nombres

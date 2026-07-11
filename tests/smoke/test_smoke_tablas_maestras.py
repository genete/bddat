"""Smoke test — catálogos estructurales ESFTT (/tablas_maestras/, #171).

Cubre listado (acceso universal, 4 roles), alta y edición (restringidas a
SUPERVISOR/ADMIN), inmutabilidad del campo identificador tras el alta, y el
catálogo cerrado de Tarea (sin alta, para nadie).

Corre contra la BD real de desarrollo — las filas de prueba se marcan con el
prefijo 'SMOKE171_' en el campo identificador y se borran en el fixture
autouse de abajo.
"""
import pytest

_PREFIJO = 'SMOKE171_'


@pytest.fixture(autouse=True)
def _limpiar_datos_prueba(app):
    yield
    with app.app_context():
        from app import db
        from app.models.tipos_expedientes import TipoExpediente
        from app.models.tipos_fases import TipoFase
        from app.models.tipos_solicitudes import TipoSolicitud
        from app.models.tipos_tramites import TipoTramite
        from app.models.tramites_tareas import TramiteTarea
        from app.models.tramites_tareas_documentos import TramiteTareaDocumento
        TipoExpediente.query.filter(TipoExpediente.tipo.like(f'{_PREFIJO}%')).delete(synchronize_session=False)
        TipoFase.query.filter(TipoFase.codigo.like(f'{_PREFIJO}%')).delete(synchronize_session=False)
        TipoSolicitud.query.filter(TipoSolicitud.siglas.like(f'{_PREFIJO}%')).delete(synchronize_session=False)
        tramites_ids = [t.id for t in TipoTramite.query.filter(TipoTramite.codigo.like(f'{_PREFIJO}%')).all()]
        if tramites_ids:
            TramiteTareaDocumento.query.filter(TramiteTareaDocumento.tipo_tramite_id.in_(tramites_ids)) \
                .delete(synchronize_session=False)
            TramiteTarea.query.filter(TramiteTarea.tipo_tramite_id.in_(tramites_ids)) \
                .delete(synchronize_session=False)
            TipoTramite.query.filter(TipoTramite.id.in_(tramites_ids)).delete(synchronize_session=False)
        db.session.commit()


# ---------------------------------------------------------------------------
# Listado — acceso universal (4 roles)
# ---------------------------------------------------------------------------

def test_listado_render_supervisor(usuario_supervisor):
    r = usuario_supervisor.get('/tablas_maestras/', follow_redirects=True)
    assert r.status_code == 200
    assert b'class="app-main"' in r.data


def test_listado_accesible_tramitador(usuario_tramitador):
    r = usuario_tramitador.get('/tablas_maestras/', follow_redirects=True)
    assert r.status_code == 200


def test_listado_accesible_administrativo(usuario_administrativo):
    r = usuario_administrativo.get('/tablas_maestras/', follow_redirects=True)
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# Alta — solo SUPERVISOR/ADMIN, campo identificador se fija y no se toca más
# ---------------------------------------------------------------------------

def test_supervisor_puede_crear_expediente(usuario_supervisor, app):
    r = usuario_supervisor.post('/tablas_maestras/expediente/crear', data={
        'tipo': f'{_PREFIJO}Autoconsumo',
        'descripcion': 'Tipo de prueba (#171 smoke)',
    }, follow_redirects=False)
    assert r.status_code == 302

    with app.app_context():
        from app.models.tipos_expedientes import TipoExpediente
        creado = TipoExpediente.query.filter_by(tipo=f'{_PREFIJO}Autoconsumo').first()
        assert creado is not None
        assert creado.descripcion == 'Tipo de prueba (#171 smoke)'


def test_tramitador_no_puede_crear(usuario_tramitador):
    r = usuario_tramitador.post('/tablas_maestras/expediente/crear', data={
        'tipo': f'{_PREFIJO}NoAutorizado',
    }, follow_redirects=False)
    assert r.status_code == 302
    assert '/perfil' in r.headers.get('Location', '')


def test_tarea_no_permite_alta_ni_para_supervisor(usuario_supervisor):
    """Catálogo cerrado (#171): estado_dominio.py asume exactamente 4 códigos."""
    r = usuario_supervisor.post('/tablas_maestras/tarea/crear', data={
        'codigo': f'{_PREFIJO}NUEVA',
    }, follow_redirects=False)
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Edición — campo identificador inmutable aunque llegue en el POST
# ---------------------------------------------------------------------------

def _crear_fase_para_editar(app):
    from app import db
    from app.models.tipos_fases import TipoFase
    with app.app_context():
        fase = TipoFase(codigo=f'{_PREFIJO}FASE', nombre='Fase de prueba (#171 smoke)')
        db.session.add(fase)
        db.session.commit()
        return fase.id


def test_supervisor_puede_editar_nombre(usuario_supervisor, app):
    fase_id = _crear_fase_para_editar(app)
    r = usuario_supervisor.post(f'/tablas_maestras/fase/{fase_id}/editar', data={
        'nombre': 'Fase renombrada (#171 smoke)',
        'abrev': 'FR',
    }, follow_redirects=False)
    assert r.status_code == 302

    with app.app_context():
        from app.models.tipos_fases import TipoFase
        editada = TipoFase.query.get(fase_id)
        assert editada.nombre == 'Fase renombrada (#171 smoke)'
        assert editada.abrev == 'FR'


def test_codigo_no_cambia_aunque_llegue_en_el_post(usuario_supervisor, app):
    fase_id = _crear_fase_para_editar(app)
    r = usuario_supervisor.post(f'/tablas_maestras/fase/{fase_id}/editar', data={
        'codigo': f'{_PREFIJO}INTENTO_CAMBIO',
        'nombre': 'Fase de prueba (#171 smoke)',
    }, follow_redirects=False)
    assert r.status_code == 302

    with app.app_context():
        from app.models.tipos_fases import TipoFase
        editada = TipoFase.query.get(fase_id)
        assert editada.codigo == f'{_PREFIJO}FASE'


def test_tramitador_no_puede_editar(usuario_tramitador, app):
    fase_id = _crear_fase_para_editar(app)
    r = usuario_tramitador.post(f'/tablas_maestras/fase/{fase_id}/editar', data={
        'nombre': 'Intento no autorizado (#171 smoke)',
    }, follow_redirects=False)
    assert r.status_code == 302
    assert '/perfil' in r.headers.get('Location', '')


# ---------------------------------------------------------------------------
# Editor anidado de pasos (tramites_tareas + tramites_tareas_documentos)
# ---------------------------------------------------------------------------

def _crear_tramite_para_editar(app):
    from app import db
    from app.models.tipos_tramites import TipoTramite
    with app.app_context():
        tramite = TipoTramite(codigo=f'{_PREFIJO}TRAMITE', nombre='Trámite de prueba (#171 smoke)')
        db.session.add(tramite)
        db.session.commit()
        return tramite.id


def test_supervisor_puede_guardar_secuencia_de_pasos(usuario_supervisor, app):
    import json
    tramite_id = _crear_tramite_para_editar(app)

    with app.app_context():
        from app.models.tipos_tareas import TipoTarea
        analizar_id = TipoTarea.query.filter_by(codigo='ANALIZAR').first().id
        notificar_id = TipoTarea.query.filter_by(codigo='NOTIFICAR').first().id

    pasos = [
        {'tipo_tarea_id': analizar_id, 'documentos': []},
        {'tipo_tarea_id': notificar_id, 'documentos': [
            {'rol': 'SALIDA', 'tipo_documento_id': None, 'obligatorio': True},
        ]},
    ]
    r = usuario_supervisor.post(f'/tablas_maestras/tramite/{tramite_id}/editar', data={
        'nombre': 'Trámite de prueba (#171 smoke)',
        'pasos_json': json.dumps(pasos),
    }, follow_redirects=False)
    assert r.status_code == 302

    with app.app_context():
        from app.models.tramites_tareas import TramiteTarea
        from app.models.tramites_tareas_documentos import TramiteTareaDocumento
        filas = TramiteTarea.query.filter_by(tipo_tramite_id=tramite_id).order_by(TramiteTarea.orden).all()
        assert [f.orden for f in filas] == [1, 2]
        assert [f.tipo_tarea_id for f in filas] == [analizar_id, notificar_id]

        docs = TramiteTareaDocumento.query.filter_by(tipo_tramite_id=tramite_id).all()
        assert len(docs) == 1
        assert docs[0].orden_tarea == 2
        assert docs[0].rol == 'SALIDA'
        assert docs[0].tipo_documento_id is None
        assert docs[0].obligatorio is True


def test_guardar_pasos_reemplaza_secuencia_anterior(usuario_supervisor, app):
    """Reeditar la secuencia sustituye la anterior por completo (#171)."""
    import json
    tramite_id = _crear_tramite_para_editar(app)

    with app.app_context():
        from app.models.tipos_tareas import TipoTarea
        analizar_id = TipoTarea.query.filter_by(codigo='ANALIZAR').first().id
        elaborar_id = TipoTarea.query.filter_by(codigo='ELABORAR').first().id

    usuario_supervisor.post(f'/tablas_maestras/tramite/{tramite_id}/editar', data={
        'nombre': 'Trámite de prueba (#171 smoke)',
        'pasos_json': json.dumps([{'tipo_tarea_id': analizar_id, 'documentos': []}]),
    })
    usuario_supervisor.post(f'/tablas_maestras/tramite/{tramite_id}/editar', data={
        'nombre': 'Trámite de prueba (#171 smoke)',
        'pasos_json': json.dumps([{'tipo_tarea_id': elaborar_id, 'documentos': []}]),
    })

    with app.app_context():
        from app.models.tramites_tareas import TramiteTarea
        filas = TramiteTarea.query.filter_by(tipo_tramite_id=tramite_id).all()
        assert len(filas) == 1
        assert filas[0].tipo_tarea_id == elaborar_id


def test_pasos_con_tarea_invalida_no_guarda_nada(usuario_supervisor, app):
    import json
    tramite_id = _crear_tramite_para_editar(app)

    r = usuario_supervisor.post(f'/tablas_maestras/tramite/{tramite_id}/editar', data={
        'nombre': 'Trámite de prueba (#171 smoke)',
        'pasos_json': json.dumps([{'tipo_tarea_id': 999999, 'documentos': []}]),
    }, follow_redirects=False)
    assert r.status_code == 302

    with app.app_context():
        from app.models.tramites_tareas import TramiteTarea
        assert TramiteTarea.query.filter_by(tipo_tramite_id=tramite_id).count() == 0

"""Smoke tests — inspector de expedientes (ADR-023 / ADR-024 / #543)."""

import json
import pytest


# ── Redirects ADR-023 §9 ──────────────────────────────────────────────────────

def test_expediente_detalle_redirige_a_listado(usuario_supervisor, expediente_seed):
    """GET /expedientes/<id> redirige a /expedientes/?sel=<id> (ADR-023 §9)."""
    r = usuario_supervisor.get(f'/expedientes/{expediente_seed}')
    assert r.status_code == 302
    assert f'sel={expediente_seed}' in r.location


def test_expediente_editar_get_redirige(usuario_supervisor, expediente_seed):
    """GET /expedientes/<id>/editar redirige al listado con sel= (ADR-023 §9)."""
    r = usuario_supervisor.get(f'/expedientes/{expediente_seed}/editar')
    assert r.status_code == 302
    assert f'sel={expediente_seed}' in r.location


# ── Fragmento inspector — lectura ─────────────────────────────────────────────

def test_expediente_fragmento_supervisor(usuario_supervisor, expediente_seed):
    """GET /expedientes/<id>/fragmento → 200 para SUPERVISOR."""
    r = usuario_supervisor.get(f'/expedientes/{expediente_seed}/fragmento')
    assert r.status_code == 200
    assert b'AT-' in r.data


def test_expediente_fragmento_tramitador(usuario_tramitador, expediente_seed):
    """GET /expedientes/<id>/fragmento → 200 para TRAMITADOR."""
    r = usuario_tramitador.get(f'/expedientes/{expediente_seed}/fragmento')
    assert r.status_code == 200


def test_expediente_fragmento_admin(usuario_admin, expediente_seed):
    """GET /expedientes/<id>/fragmento → 200 para ADMIN."""
    r = usuario_admin.get(f'/expedientes/{expediente_seed}/fragmento')
    assert r.status_code == 200


def test_expediente_fragmento_contiene_secciones(usuario_supervisor, expediente_seed):
    """El fragmento incluye la sección de datos del proyecto y el botón Tramitar."""
    r = usuario_supervisor.get(f'/expedientes/{expediente_seed}/fragmento')
    assert r.status_code == 200
    assert b'Tramitar' in r.data
    assert b'Datos del proyecto' in r.data


# ── Fragmento edición ─────────────────────────────────────────────────────────

def test_expediente_editar_fragmento_render(usuario_supervisor, expediente_seed):
    """GET /expedientes/<id>/editar-fragmento → 200 con formulario."""
    r = usuario_supervisor.get(f'/expedientes/{expediente_seed}/editar-fragmento')
    assert r.status_code == 200
    assert b'titulo' in r.data


def test_expediente_editar_xhr_success(usuario_supervisor, expediente_seed, app):
    """POST editar con XHR y datos válidos → JSON {ok: true}.

    Reenvía los valores que ya tiene el expediente: el test corre contra la BD de
    desarrollo y `expediente_seed` es un expediente real (`Expediente.query.first()`,
    sin ORDER BY: cuál toca es indeterminado), así que nunca debe cambiar su estado.
    """
    with app.app_context():
        from app.models.expedientes import Expediente
        exp = Expediente.query.get(expediente_seed)
        form_data = {
            'titulo':      exp.proyecto.titulo if exp.proyecto else 'Test',
            'finalidad':   exp.proyecto.finalidad if exp.proyecto else 'Test',
            'emplazamiento': exp.proyecto.emplazamiento if exp.proyecto else 'Test',
            'responsable_id': exp.responsable_id or '',
        }

    r = usuario_supervisor.post(
        f'/expedientes/{expediente_seed}/editar',
        data=form_data,
        headers={'X-Requested-With': 'XMLHttpRequest'},
    )
    assert r.status_code == 200
    body = json.loads(r.data)
    assert body['ok'] is True


def test_expediente_editar_parcial_no_vacia_lo_que_no_menciona(
        usuario_supervisor, expediente_seed, app):
    """Un POST parcial no toca los campos que no envía (#832).

    Regresión del bug que vació `tipo_expediente_id`, `ia_id`, los tres flags
    técnicos y `max_tension_nominal_kv` de tres expedientes: la ruta trataba
    "campo ausente" como "vaciar campo". El `finally` restaura el estado aunque
    el fix esté roto — este test corre contra la BD de desarrollo.
    """
    from app import db
    from app.models.expedientes import Expediente

    def _estado():
        with app.app_context():
            exp = Expediente.query.get(expediente_seed)
            p = exp.proyecto
            return {
                'tipo_expediente_id': exp.tipo_expediente_id,
                'heredado': exp.heredado,
                'responsable_id': exp.responsable_id,
                'ia_id': p.ia_id if p else None,
                'es_modificacion': p.es_modificacion if p else None,
                'sin_linea_aerea': p.sin_linea_aerea if p else None,
                'solo_suelo_urbano_urbanizable': p.solo_suelo_urbano_urbanizable if p else None,
                'max_tension_nominal_kv': p.max_tension_nominal_kv if p else None,
                'titulo': p.titulo if p else None,
            }

    previo = _estado()
    try:
        # Cuerpo parcial: solo el título, con su valor actual. Todo lo demás calla.
        r = usuario_supervisor.post(
            f'/expedientes/{expediente_seed}/editar',
            data={'titulo': previo['titulo'] or 'Test'},
            headers={'X-Requested-With': 'XMLHttpRequest'},
        )
        assert r.status_code == 200
        assert json.loads(r.data)['ok'] is True
        assert _estado() == previo
    finally:
        with app.app_context():
            exp = Expediente.query.get(expediente_seed)
            exp.tipo_expediente_id = previo['tipo_expediente_id']
            exp.heredado = previo['heredado']
            exp.responsable_id = previo['responsable_id']
            if exp.proyecto:
                for campo in ('ia_id', 'es_modificacion', 'sin_linea_aerea',
                              'solo_suelo_urbano_urbanizable', 'max_tension_nominal_kv',
                              'titulo'):
                    setattr(exp.proyecto, campo, previo[campo])
            db.session.commit()


def test_expediente_editar_no_admite_vaciar_un_not_null(
        usuario_supervisor, expediente_seed):
    """Título presente pero vacío → 400 con el mensaje del alta, no NULL (#832)."""
    r = usuario_supervisor.post(
        f'/expedientes/{expediente_seed}/editar',
        data={'titulo': '   '},
        headers={'X-Requested-With': 'XMLHttpRequest'},
    )
    assert r.status_code == 400
    body = json.loads(r.data)
    assert body['ok'] is False
    assert 'El título del proyecto es obligatorio.' in body['errors']


def test_expediente_editar_fragmento_declara_form_completo(
        usuario_supervisor, expediente_seed):
    """El formulario del inspector lleva el centinela que habilita las casillas (#832)."""
    r = usuario_supervisor.get(f'/expedientes/{expediente_seed}/editar-fragmento')
    assert r.status_code == 200
    assert b'name="_form_completo"' in r.data


# ── Modal municipios ──────────────────────────────────────────────────────────

def test_expediente_gestionar_municipios_render(usuario_supervisor, expediente_seed):
    """GET /expedientes/<id>/gestionar-municipios → 200 con formulario de municipios."""
    r = usuario_supervisor.get(f'/expedientes/{expediente_seed}/gestionar-municipios')
    assert r.status_code == 200
    assert b'gm-form' in r.data


# ── Redirects proyectos/* → expedientes/* (ADR-024 §1) ───────────────────────

def test_proyectos_index_redirige(usuario_supervisor):
    """GET /proyectos/ → 302 a /expedientes/."""
    r = usuario_supervisor.get('/proyectos/')
    assert r.status_code == 302
    assert '/expedientes/' in r.location


def test_proyectos_detalle_redirige(usuario_supervisor, expediente_seed, app):
    """GET /proyectos/<proyecto_id> → 302 a /expedientes/?sel=<expediente_id>."""
    with app.app_context():
        from app.models.expedientes import Expediente
        exp = Expediente.query.get(expediente_seed)
        if exp is None or exp.proyecto_id is None:
            pytest.skip('Expediente seed sin proyecto asociado')
        proyecto_id = exp.proyecto_id

    r = usuario_supervisor.get(f'/proyectos/{proyecto_id}')
    assert r.status_code == 302
    assert f'sel={expediente_seed}' in r.location


def test_proyectos_editar_redirige(usuario_supervisor, expediente_seed, app):
    """GET /proyectos/<proyecto_id>/editar → 302 a /expedientes/?sel=<expediente_id>."""
    with app.app_context():
        from app.models.expedientes import Expediente
        exp = Expediente.query.get(expediente_seed)
        if exp is None or exp.proyecto_id is None:
            pytest.skip('Expediente seed sin proyecto asociado')
        proyecto_id = exp.proyecto_id

    r = usuario_supervisor.get(f'/proyectos/{proyecto_id}/editar')
    assert r.status_code == 302
    assert f'sel={expediente_seed}' in r.location


# ── Listado con nuevos filtros ────────────────────────────────────────────────

def test_expedientes_listado_con_filtro_ia(usuario_supervisor):
    """GET /expedientes/?ia_id=1 → 200 con estructura de listado."""
    r = usuario_supervisor.get('/expedientes/?ia_id=1', follow_redirects=True)
    assert r.status_code == 200
    assert b'class="app-main"' in r.data


def test_expedientes_listado_con_filtro_tipo(usuario_supervisor):
    """GET /expedientes/?tipo_expediente_id=1 → 200."""
    r = usuario_supervisor.get('/expedientes/?tipo_expediente_id=1', follow_redirects=True)
    assert r.status_code == 200
    assert b'class="app-main"' in r.data

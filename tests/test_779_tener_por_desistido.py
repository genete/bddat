"""Tests issue #779 — el vencimiento de la subsanación produce TENER_POR_DESISTIDO.

El único punto de fondo es de dato: la fila de catalogo_plazos del art. 68.1
(subsanación) apuntaba a PERDIDA_TRAMITE (art. 73.3, pérdida de trámite no
indispensable) cuando lo que produce es que se tenga al solicitante por
desistido de su solicitud. #779 da de alta TENER_POR_DESISTIDO en
efectos_plazo y reasigna esa fila; nada más cambia de efecto.

Corre contra la BD real de desarrollo (mismo patrón que el resto de la
suite de catalogo_plazos, p. ej. test_778_medida_unica.py).
"""


def test_fila_subsanacion_usa_tener_por_desistido(app):
    with app.app_context():
        from app.models.catalogo_plazos import CatalogoPlazo

        fila = CatalogoPlazo.query.filter_by(
            tipo_elemento='TAREA',
            camino='ANY/ANY/ANY/REQUERIMIENTO_SUBSANACION/ESPERAR_PLAZO',
        ).one()

        assert fila.efecto_plazo.codigo == 'TENER_POR_DESISTIDO'


def test_ninguna_otra_fila_usa_perdida_tramite(app):
    with app.app_context():
        from app.models.catalogo_plazos import CatalogoPlazo
        from app.models.efectos_plazo import EfectoPlazo

        filas = (
            CatalogoPlazo.query
            .join(EfectoPlazo, CatalogoPlazo.efecto_vencimiento_id == EfectoPlazo.id)
            .filter(EfectoPlazo.codigo == 'PERDIDA_TRAMITE')
            .all()
        )

        assert filas == []


def test_efecto_tener_por_desistido_es_unico_en_catalogo(app):
    with app.app_context():
        from app.models.efectos_plazo import EfectoPlazo

        efectos = EfectoPlazo.query.filter_by(codigo='TENER_POR_DESISTIDO').all()
        assert len(efectos) == 1

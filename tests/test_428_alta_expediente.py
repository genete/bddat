"""Tests #428 — el alta de expediente y su ancla documental.

Cada test **se fabrica lo que necesita** y no busca nada en la base: ni
`expediente_seed` ni `Query.first()` sobre filas de negocio. Es lo que exige #849
para que la suite siga valiendo cuando el interruptor apunte a la base de tests,
donde no hay expedientes, solicitudes ni entidades. Del catálogo sí se lee —eso lo
siembran las migraciones— pero con `assert`, no con `pytest.skip`: en una base
sembrada por nosotros, que falte un tipo de expediente es un defecto de la
semilla, no una razón para no probar.

`fs_tmp` no es opcional aquí: el alta escribe un fichero real en `AT-N/pool/` y el
sistema de ficheros no revierte con el SAVEPOINT de `app_ctx`. Sin él, cada pasada
dejaría basura en el servidor de ficheros de desarrollo — y el test de limpieza no
podría comprobar nada.
"""
import os
from datetime import timedelta

import pytest

from app import db
from app.services.alta_expediente import DocumentoSolicitud, MENSAJE_SIN_ANCLA
from tests.conftest import (
    CONTENIDO_SOLICITUD_PRUEBA as CONTENIDO, crear_expediente_de_prueba,
)


@pytest.fixture
def alta(alta_propia):
    """Un alta completa y recién hecha. Se revierte al salir.

    Es la fixture compartida `alta_propia` con otro nombre: la fábrica vive en
    `conftest` porque media suite la necesita, no solo estos tests.
    """
    return alta_propia


# ---------------------------------------------------------------------------
# El alta completa
# ---------------------------------------------------------------------------

class TestAltaCompleta:

    def test_crea_expediente_proyecto_y_solicitud(self, alta):
        assert alta.expediente.id is not None
        assert alta.expediente.numero_at == alta.numero_at
        assert alta.solicitud.expediente_id == alta.expediente.id
        assert alta.expediente.proyecto_id is not None

    def test_la_solicitud_queda_anclada_al_documento(self, alta):
        assert alta.solicitud.documento_solicitud_id == alta.documento.id

    def test_el_documento_es_un_modelo_de_solicitud_con_su_fecha(self, alta):
        assert alta.documento.tipo_doc.codigo == 'MODELO_SOLICITUD'
        assert alta.documento.fecha_administrativa is not None

    def test_el_fichero_existe_en_el_pool_del_expediente(self, alta, fs_tmp):
        ruta = alta.documento.ruta_absoluta()
        assert os.path.isfile(ruta)
        assert os.path.basename(os.path.dirname(ruta)) == 'pool'
        assert f'AT-{alta.numero_at}' in ruta
        with open(ruta, 'rb') as f:
            assert f.read() == CONTENIDO

    def test_el_titular_queda_acreditado_por_ese_documento(self, alta):
        """El signal deja la fila TITULAR sin acreditativo porque el documento aún
        no existe; el servicio la completa en la misma transacción (#374/#428)."""
        from app.models.interesados_expediente import InteresadoExpediente

        titular = InteresadoExpediente.query.filter_by(
            expediente_id=alta.expediente.id, tipo_origen='TITULAR').one()
        assert titular.documento_acreditativo_id == alta.documento.id

    def test_el_plazo_de_la_solicitud_arranca(self, alta):
        """El motivo de todo el issue: sin ancla el art. 128 constaba SIN_PLAZO."""
        from app.services.plazos import obtener_estado_plazo_solicitud

        estado = obtener_estado_plazo_solicitud(alta.solicitud)
        assert estado.estado != 'SIN_PLAZO'
        assert estado.fecha_disparo == alta.documento.fecha_administrativa
        assert estado.fecha_limite is not None


# ---------------------------------------------------------------------------
# El invariante: sin documento no hay expediente
# ---------------------------------------------------------------------------

class TestSinAncla:

    def test_sin_documento_no_hay_alta(self, app_ctx, fs_tmp):
        with pytest.raises(ValueError) as exc:
            crear_expediente_de_prueba(documento=None)
        assert str(exc.value) == MENSAJE_SIN_ANCLA

    def test_con_fichero_vacio_tampoco(self, app_ctx, fs_tmp):
        from app.services.reloj_simulado import hoy

        vacio = DocumentoSolicitud(
            contenido=b'', nombre_original='vacio.pdf', fecha_registro=hoy())

        with pytest.raises(ValueError) as exc:
            crear_expediente_de_prueba(documento=vacio)
        assert str(exc.value) == MENSAJE_SIN_ANCLA

    def test_el_rechazo_no_consume_numero_de_expediente(self, app_ctx, fs_tmp):
        """El contador es gapless: un alta rechazada no puede gastar un AT."""
        antes = db.session.execute(
            db.text('SELECT valor FROM public.contador_numero_at')).scalar()

        with pytest.raises(ValueError):
            crear_expediente_de_prueba(documento=None)

        despues = db.session.execute(
            db.text('SELECT valor FROM public.contador_numero_at')).scalar()
        assert despues == antes


# ---------------------------------------------------------------------------
# Fecha administrativa futura (#824) — la valida el modelo, la sufre el alta
# ---------------------------------------------------------------------------

class TestFechaFutura:

    def test_fecha_de_registro_futura_rechaza_el_alta(self, app_ctx, fs_tmp):
        from app.services.reloj_simulado import hoy

        with pytest.raises(ValueError) as exc:
            crear_expediente_de_prueba(fecha_registro=hoy() + timedelta(days=1))
        assert 'no puede ser futura' in str(exc.value)

    def test_el_alta_rechazada_por_fecha_no_deja_fichero(self, app_ctx, fs_tmp):
        """La fecha se valida al construir el Documento, y eso ocurre después de
        crear `AT-N/pool/`: el caso real que ejercita la limpieza del `except`."""
        from app.services.reloj_simulado import hoy

        with pytest.raises(ValueError):
            crear_expediente_de_prueba(fecha_registro=hoy() + timedelta(days=1))

        # Ni el fichero ni la carpeta del expediente que no llegó a existir.
        restos = [d for d in os.listdir(str(fs_tmp)) if d.startswith('AT-')]
        assert restos == [], f'el alta fallida dejó {restos} en el disco'


# ---------------------------------------------------------------------------
# 2ª vía: solicitud adicional sobre un expediente que ya existe
# ---------------------------------------------------------------------------

def _documento_en_pool(expediente, *, fecha, nombre='escrito.pdf'):
    """Deja un documento en el pool del expediente por la vía real."""
    from app.services.ingesta_pool import ingestar_en_pool
    from app.models.tipos_documentos import TipoDocumento

    tipo = TipoDocumento.query.filter_by(codigo='MODELO_SOLICITUD').first()
    assert tipo is not None, "la semilla debe traer el TipoDocumento 'MODELO_SOLICITUD'"

    resultado = ingestar_en_pool(
        expediente, b'%PDF-1.4 escrito adicional', nombre,
        tipo_doc_id=tipo.id, fecha_administrativa=fecha, asunto='Escrito de prueba')
    db.session.flush()
    return resultado.documento


class TestSolicitudAdicional:
    """`mutaciones_arbol.crear_solicitud` exige el mismo ancla que el alta (#428).

    Aquí el expediente ya existe, así que el escrito no se sube con el alta: se
    elige del pool. Lo que no cambia es el invariante — sin él la solicitud nace
    SIN_PLAZO, que es justo el estado que este issue vino a hacer imposible.
    """

    def _tipo_aap(self):
        from app.models.tipos_solicitudes import TipoSolicitud
        tipo = TipoSolicitud.query.filter_by(siglas='AAP').first()
        assert tipo is not None, "la semilla debe traer el TipoSolicitud 'AAP'"
        return tipo

    def test_sin_ancla_no_crea_la_solicitud(self, alta_propia):
        import app.services.mutaciones_arbol as svc

        res = svc.crear_solicitud(
            alta_propia.expediente, [self._tipo_aap()],
            alta_propia.expediente.titular_id, documento_solicitud_id=None)

        assert res.ok is False
        assert res.error == svc.MENSAJE_SIN_ANCLA_SOLICITUD

    def test_con_ancla_la_solicitud_nace_anclada(self, alta_propia):
        import app.services.mutaciones_arbol as svc
        from app.models.solicitudes import Solicitud
        from app.services.reloj_simulado import hoy

        doc = _documento_en_pool(alta_propia.expediente, fecha=hoy())

        res = svc.crear_solicitud(
            alta_propia.expediente, [self._tipo_aap()],
            alta_propia.expediente.titular_id, documento_solicitud_id=doc.id)

        assert res.ok is True, res.error
        nueva = Solicitud.query.get(res.ids[0])
        assert nueva.documento_solicitud_id == doc.id

    def test_el_plazo_de_la_solicitud_adicional_arranca(self, alta_propia):
        import app.services.mutaciones_arbol as svc
        from app.models.solicitudes import Solicitud
        from app.services.plazos import obtener_estado_plazo_solicitud
        from app.services.reloj_simulado import hoy

        doc = _documento_en_pool(alta_propia.expediente, fecha=hoy())
        res = svc.crear_solicitud(
            alta_propia.expediente, [self._tipo_aap()],
            alta_propia.expediente.titular_id, documento_solicitud_id=doc.id)
        assert res.ok is True, res.error

        estado = obtener_estado_plazo_solicitud(Solicitud.query.get(res.ids[0]))
        assert estado.estado != 'SIN_PLAZO'

    def test_documento_de_otro_expediente_rechazado(self, app_ctx, fs_tmp):
        """La FK sola no lo impediría: `Documento` solo conoce su expediente, y
        nada ata ese expediente al de la solicitud."""
        import app.services.mutaciones_arbol as svc
        from app.services.reloj_simulado import hoy
        from tests.conftest import crear_expediente_de_prueba

        propio = crear_expediente_de_prueba()
        ajeno = crear_expediente_de_prueba()

        res = svc.crear_solicitud(
            propio.expediente, [self._tipo_aap()], propio.expediente.titular_id,
            documento_solicitud_id=_documento_en_pool(ajeno.expediente, fecha=hoy()).id)

        assert res.ok is False
        assert 'no pertenece a este expediente' in res.error

    def test_documento_sin_fecha_rechazado(self, alta_propia):
        """Un ancla sin fecha no ancla nada: el plazo seguiría SIN_PLAZO con la FK
        puesta, que es peor que sin ella — parece resuelto y no lo está."""
        import app.services.mutaciones_arbol as svc

        doc = _documento_en_pool(alta_propia.expediente, fecha=None, nombre='sin_fecha.pdf')

        res = svc.crear_solicitud(
            alta_propia.expediente, [self._tipo_aap()],
            alta_propia.expediente.titular_id, documento_solicitud_id=doc.id)

        assert res.ok is False
        assert 'fecha de registro de entrada' in res.error

    def test_el_bypass_del_motor_no_exime_del_ancla(self, alta_propia):
        """El escape de #324 es para las reglas de catálogo, no para la integridad
        documental: con justificación y todo, sin ancla no hay solicitud."""
        import app.services.mutaciones_arbol as svc

        res = svc.crear_solicitud(
            alta_propia.expediente, [self._tipo_aap()],
            alta_propia.expediente.titular_id, documento_solicitud_id=None,
            justificacion='Me la juego')

        assert res.ok is False
        assert res.error == svc.MENSAJE_SIN_ANCLA_SOLICITUD

    def test_varios_tipos_comparten_el_mismo_escrito(self, alta_propia):
        """Un mismo escrito puede pedir varios actos administrativos."""
        import app.services.mutaciones_arbol as svc
        from app.models.solicitudes import Solicitud
        from app.models.tipos_solicitudes import TipoSolicitud
        from app.services.reloj_simulado import hoy

        aac = TipoSolicitud.query.filter_by(siglas='AAC').first()
        assert aac is not None, "la semilla debe traer el TipoSolicitud 'AAC'"

        doc = _documento_en_pool(alta_propia.expediente, fecha=hoy())
        res = svc.crear_solicitud(
            alta_propia.expediente, [self._tipo_aap(), aac],
            alta_propia.expediente.titular_id, documento_solicitud_id=doc.id)

        assert res.ok is True, res.error
        assert len(res.ids) == 2
        for sol_id in res.ids:
            assert Solicitud.query.get(sol_id).documento_solicitud_id == doc.id


class TestConstraintYBorrado:
    """El NOT NULL y la regla de borrado que hubo que cambiar con él (#428).

    La FK nació `ON DELETE SET NULL`, y esa combinación con NOT NULL es
    incoherente: borrar el documento intentaría escribir NULL en una columna que no
    lo admite. La migración la recreó como NO ACTION, igual que sus dos hermanas.
    """

    def test_no_se_puede_crear_una_solicitud_sin_ancla(self, alta_propia):
        """La última red: aunque alguien esquive los dos servicios, la base dice no."""
        from sqlalchemy.exc import IntegrityError
        from app.models.solicitudes import Solicitud

        db.session.add(Solicitud(
            expediente_id=alta_propia.expediente.id,
            entidad_id=alta_propia.expediente.titular_id,
            tipo_solicitud_id=alta_propia.solicitud.tipo_solicitud_id,
        ))
        with pytest.raises(IntegrityError):
            db.session.flush()
        db.session.rollback()

    def _soltar_acreditativo(self, expediente_id):
        """Lo que hace `limpiar_reciclables.py` antes de borrar documentos.

        El escrito de solicitud lo referencian DOS tablas desde #428: la solicitud
        que ancla y el interesado TITULAR al que acredita. Esta segunda sí se
        neutraliza con un UPDATE, porque su columna sigue siendo nullable.
        """
        db.session.execute(
            db.text('UPDATE public.interesados_expediente '
                    'SET documento_acreditativo_id = NULL WHERE expediente_id = :exp'),
            {'exp': expediente_id})

    def test_borrar_el_documento_anclado_falla_en_vez_de_desanclar(self, alta_propia):
        """Con la regla vieja el DELETE habría puesto NULL en una columna NOT NULL.

        Ahora la base se niega y nombra la FK de la solicitud, que es lo que
        corresponde. El pool además lo explica antes de llegar aquí, diciendo qué
        solicitud lo usa (`_motivo_ancla`, #838).
        """
        from sqlalchemy.exc import IntegrityError
        from app.models.documentos import Documento

        self._soltar_acreditativo(alta_propia.expediente.id)
        doc_id = alta_propia.documento.id

        with pytest.raises(IntegrityError) as exc:
            db.session.execute(
                db.text('DELETE FROM public.documentos WHERE id = :doc'), {'doc': doc_id})
        assert 'fk_solicitudes_documento_solicitud' in str(exc.value)
        db.session.rollback()

        assert Documento.query.get(doc_id) is not None

    def test_borrando_antes_la_solicitud_el_documento_sale(self, alta_propia):
        """El orden que usa `limpiar_reciclables.py`: solicitudes y luego documentos.

        Es lo que sustituye al `UPDATE ... = NULL` sobre `documento_solicitud_id`
        que el script hacía antes y que con la columna NOT NULL habría reventado.
        """
        doc_id = alta_propia.documento.id

        self._soltar_acreditativo(alta_propia.expediente.id)
        db.session.execute(
            db.text('DELETE FROM public.solicitudes WHERE id = :sol'),
            {'sol': alta_propia.solicitud.id})
        db.session.execute(
            db.text('DELETE FROM public.documentos WHERE id = :doc'), {'doc': doc_id})

        # Con SELECT y no con `Documento.query.get`: el ORM devolvería el objeto
        # que sigue en su identity map, sin volver a preguntar a la base.
        sigue = db.session.execute(
            db.text('SELECT count(*) FROM public.documentos WHERE id = :doc'),
            {'doc': doc_id}).scalar()
        assert sigue == 0


class TestRutaSolicitudAdicional:
    """La ruta del árbol pasa el ancla al servicio (#428)."""

    def test_la_ruta_propaga_el_documento(self, usuario_supervisor, expediente_seed):
        from unittest.mock import patch
        from app.services.mutaciones_arbol import ResultadoMutacion

        with patch('app.routes.api_expedientes.svc.crear_solicitud') as mock_crear:
            mock_crear.return_value = ResultadoMutacion(ok=True, ids=[1])
            r = usuario_supervisor.post(
                f'/api/expedientes/{expediente_seed}/nodo/expediente/{expediente_seed}/hijos',
                json={'tipo_id': 1, 'documento_solicitud_id': 4242})

        assert r.status_code == 201
        assert mock_crear.call_args.kwargs['documento_solicitud_id'] == 4242

    def test_sin_documento_en_el_body_llega_none(self, usuario_supervisor, expediente_seed):
        """Y el servicio lo rechaza — la ruta no adivina ni inventa un ancla."""
        from unittest.mock import patch
        from app.services.mutaciones_arbol import ResultadoMutacion

        with patch('app.routes.api_expedientes.svc.crear_solicitud') as mock_crear:
            mock_crear.return_value = ResultadoMutacion(ok=True, ids=[1])
            r = usuario_supervisor.post(
                f'/api/expedientes/{expediente_seed}/nodo/expediente/{expediente_seed}/hijos',
                json={'tipo_id': 1})

        assert r.status_code == 201
        assert mock_crear.call_args.kwargs['documento_solicitud_id'] is None

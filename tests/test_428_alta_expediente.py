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
from app.services.alta_expediente import (
    DatosAlta, DocumentoSolicitud, MENSAJE_SIN_ANCLA, alta_expediente,
)


CONTENIDO = b'%PDF-1.4 escrito de solicitud de prueba #428'


# ---------------------------------------------------------------------------
# Andamiaje: catálogo por código + una entidad titular propia
# ---------------------------------------------------------------------------

def _catalogo():
    """Las filas de catálogo que el alta necesita, por clave natural."""
    from app.models.municipios import Municipio
    from app.models.tipos_expedientes import TipoExpediente
    from app.models.tipos_solicitudes import TipoSolicitud

    tipo_exp = TipoExpediente.query.order_by(TipoExpediente.id).first()
    assert tipo_exp is not None, 'la semilla debe traer algún TipoExpediente'

    tipo_sol = TipoSolicitud.query.filter_by(siglas='AAP').first()
    assert tipo_sol is not None, "la semilla debe traer el TipoSolicitud 'AAP'"

    municipio = Municipio.query.order_by(Municipio.id).first()
    assert municipio is not None, 'la semilla debe traer municipios'

    return tipo_exp, tipo_sol, municipio


def _entidad_titular():
    """Entidad titular fabricada por el test — nunca una de la base."""
    from app.models.entidad import Entidad
    entidad = Entidad(
        nombre_completo='Titular de prueba #428, S.L.',
        nif='B00004280',
        rol_titular=True,
        rol_consultado=False,
        rol_publicador=False,
        activo=True,
    )
    db.session.add(entidad)
    db.session.flush()
    return entidad


def _datos(entidad, tipo_exp, tipo_sol, municipio, *,
           documento='normal', fecha_registro=None):
    """`DatosAlta` listo para usar. `documento=None` prueba el alta sin ancla.

    Las fechas salen de `reloj_simulado.hoy()` y nunca de `date.today()`: bajo
    `app_ctx` el validador del documento (#824) compara contra el reloj de
    desarrollo, así que una fecha de hoy real es futura para él si el reloj quedó
    atrasado —y lo queda casi siempre, lo deja ahí el script de expediente-tipo—.
    `hoy()` acierta en los dos mundos: con la base de tests DEBUG está apagado y
    devuelve la fecha real.
    """
    from app.services.reloj_simulado import hoy

    if documento == 'normal':
        documento = DocumentoSolicitud(
            contenido=CONTENIDO,
            nombre_original='solicitud_428.pdf',
            fecha_registro=fecha_registro or hoy(),
        )
    return DatosAlta(
        tipo_expediente_id=tipo_exp.id,
        responsable_id=None,
        heredado=False,
        titulo='Línea subterránea de prueba #428',
        descripcion='Expediente fabricado por la suite para probar el alta.',
        finalidad='Distribución de energía eléctrica',
        emplazamiento='T.M. de prueba',
        fecha_proyecto=hoy() - timedelta(days=30),
        ia_id=None,
        municipios_ids=[municipio.id],
        titular_id=entidad.id,
        tipo_solicitud_id=tipo_sol.id,
        solicitante_id=entidad.id,
        observaciones='[TEST #428]',
        documento=documento,
    )


@pytest.fixture
def alta(app_ctx, fs_tmp):
    """Un alta completa y recién hecha, con su andamiaje. Se revierte al salir."""
    entidad = _entidad_titular()
    datos = _datos(entidad, *_catalogo())
    return alta_expediente(datos)


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
        entidad = _entidad_titular()
        datos = _datos(entidad, *_catalogo(), documento=None)

        with pytest.raises(ValueError) as exc:
            alta_expediente(datos)
        assert str(exc.value) == MENSAJE_SIN_ANCLA

    def test_con_fichero_vacio_tampoco(self, app_ctx, fs_tmp):
        from app.services.reloj_simulado import hoy

        entidad = _entidad_titular()
        vacio = DocumentoSolicitud(
            contenido=b'', nombre_original='vacio.pdf', fecha_registro=hoy())
        datos = _datos(entidad, *_catalogo(), documento=vacio)

        with pytest.raises(ValueError) as exc:
            alta_expediente(datos)
        assert str(exc.value) == MENSAJE_SIN_ANCLA

    def test_el_rechazo_no_consume_numero_de_expediente(self, app_ctx, fs_tmp):
        """El contador es gapless: un alta rechazada no puede gastar un AT."""
        entidad = _entidad_titular()
        antes = db.session.execute(
            db.text('SELECT valor FROM public.contador_numero_at')).scalar()

        with pytest.raises(ValueError):
            alta_expediente(_datos(entidad, *_catalogo(), documento=None))

        despues = db.session.execute(
            db.text('SELECT valor FROM public.contador_numero_at')).scalar()
        assert despues == antes


# ---------------------------------------------------------------------------
# Fecha administrativa futura (#824) — la valida el modelo, la sufre el alta
# ---------------------------------------------------------------------------

class TestFechaFutura:

    def test_fecha_de_registro_futura_rechaza_el_alta(self, app_ctx, fs_tmp):
        from app.services.reloj_simulado import hoy

        entidad = _entidad_titular()
        datos = _datos(entidad, *_catalogo(),
                       fecha_registro=hoy() + timedelta(days=1))

        with pytest.raises(ValueError) as exc:
            alta_expediente(datos)
        assert 'no puede ser futura' in str(exc.value)

    def test_el_alta_rechazada_por_fecha_no_deja_fichero(self, app_ctx, fs_tmp):
        """El documento se escribe a disco antes de que el modelo lo valide, así
        que este es el caso real que ejercita la limpieza del `except`."""
        from app.services.reloj_simulado import hoy

        entidad = _entidad_titular()
        datos = _datos(entidad, *_catalogo(),
                       fecha_registro=hoy() + timedelta(days=1))

        with pytest.raises(ValueError):
            alta_expediente(datos)

        # Ni el fichero ni la carpeta del expediente que no llegó a existir.
        restos = [d for d in os.listdir(str(fs_tmp)) if d.startswith('AT-')]
        assert restos == [], f'el alta fallida dejó {restos} en el disco'

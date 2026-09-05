"""test_348_instalacion_limpia — el catálogo estructural, tras las migraciones

#348 decidió que todo dato de catálogo entra por migración y que
`flask db upgrade` sobre una base vacía debe dejar el sistema utilizable. Este
test era su regresión, y llevaba desactivado desde entonces:

    @pytest.mark.skip(reason="CI desactivado hasta limpiar migraciones — requiere BD limpia")

Apagado el testigo, la promesa se rompió sin que nadie lo viera: en #849 se
descubrió que el upgrade sobre base vacía moría a la vigésima migración, por
secuencias que los seeds no ajustaban y por el ancho de `alembic_version`.
También arrastraba cifras obsoletas —esperaba 7 tipos de tarea cuando hay 4, y
24 tipos de trámite cuando hay 31— y una fixture `db_session` que no existe en
esta suite. Vuelve corregido.

Qué comprueba y qué no: aquí se verifica **el contenido** del catálogo, y vale
igual contra desarrollo o contra la base de tests, porque desde #849 las dos
coinciden fila a fila. Que el upgrade *desde cero* funcione lo comprueba
`scripts/preparar_bd_test.py --recrear`, que es quien construye la base vacía.

Los recuentos son deliberadamente exactos. Son un golden: si cambian, es porque
alguien tocó el catálogo estructural, y eso debe verse y actualizarse aquí a
conciencia — no pasar inadvertido.
"""


class TestCatalogoBaseTrasUpgrade:
    """El catálogo que las migraciones deben dejar puesto."""

    def test_roles(self, app_ctx):
        from app.models.usuarios import Rol
        assert Rol.query.count() == 4

    def test_tipos_expedientes(self, app_ctx):
        from app.models.tipos_expedientes import TipoExpediente
        assert TipoExpediente.query.count() == 8

    def test_tipos_ia(self, app_ctx):
        from app.models.tipos_ia import TipoIA
        assert TipoIA.query.count() == 5

    def test_tipos_fases(self, app_ctx):
        from app.models.tipos_fases import TipoFase
        assert TipoFase.query.count() == 9

    def test_tipos_tramites(self, app_ctx):
        from app.models.tipos_tramites import TipoTramite
        assert TipoTramite.query.count() == 31

    def test_tipos_tareas(self, app_ctx):
        from app.models.tipos_tareas import TipoTarea
        assert TipoTarea.query.count() == 4

    def test_tipos_solicitudes(self, app_ctx):
        from app.models.tipos_solicitudes import TipoSolicitud
        assert TipoSolicitud.query.count() == 21

    def test_tipos_resultados_fases(self, app_ctx):
        from app.models.tipos_resultados_fases import TipoResultadoFase
        assert TipoResultadoFase.query.count() == 7

    def test_tipos_documentos(self, app_ctx):
        from app.models.tipos_documentos import TipoDocumento
        assert TipoDocumento.query.count() == 64


class TestCodigosQueElCodigoEspera:
    """Lo que de verdad importa: que estén los códigos de los que depende el sistema.

    Por CÓDIGO y nunca por id: los ids de catálogo no coinciden entre
    instalaciones —MODELO_SOLICITUD es 146 en desarrollo y 56 en una base
    construida desde cero—, así que una comprobación por id solo valdría en la
    máquina donde se escribió. La versión anterior de este fichero lo hacía.
    """

    def test_validar_catalogo_no_echa_nada_en_falta(self, app_ctx):
        """El manifiesto de #347, que es la lista viva de lo que el código exige."""
        from app.checks.catalogo_requerido import validar_catalogo
        assert validar_catalogo() == []

    def test_tarea_analizar_existe(self, app_ctx):
        from app.models.tipos_tareas import TipoTarea
        assert TipoTarea.query.filter_by(codigo='ANALIZAR').first() is not None

    def test_normas_base_sembradas(self, app_ctx):
        from app.models.motor_reglas import Norma
        codigos = {n.codigo for n in Norma.query.all()}
        assert {'RD1955_2000', 'D9_2011'} <= codigos

    def test_municipios_cargados(self, app_ctx):
        """Sin municipios no se puede dar de alta un proyecto (#849)."""
        from app.models.municipios import Municipio
        assert Municipio.query.count() > 8000

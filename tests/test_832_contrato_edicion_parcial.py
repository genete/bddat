"""Contrato de las rutas de edición: campo ausente ≠ campo vacío (#832).

Una petición HTTP tiene tres estados por campo —ausente, presente y vacío,
presente con valor— y `request.form.get('x') or None` solo distingue dos. Cualquier
cuerpo parcial borra entonces lo que no menciona. Así se vaciaron
`tipo_expediente_id`, `ia_id`, tres flags técnicos y la tensión de tres
expedientes, y las observaciones de tres solicitudes.

Este test existe porque **documentarlo no bastó**: #641 ya había descubierto el
mismo mecanismo, lo dejó escrito en el docstring de un smoke test, arregló el campo
concreto que le dolía (`responsable_id`) y dejó los otros ocho de la misma función.
Meses después reincidió en #832. La regla vive ahora en `REGLAS_DESARROLLO.md`
(«Rutas que editan un registro existente») y el camino cómodo en
`app/utils/formularios.py`; esto es lo que impide volver a olvidarlo.

Funciona como `app/checks/catalogo_requerido.py`: un manifiesto explícito de lo que
se acepta hoy, de forma que lo que falta sea visible en vez de invisible (patrón de
ADR-030). El manifiesto se vacía según avance #834; cuando llegue a cero, este test
pasa a ser puramente preventivo.

PUNTO CIEGO CONOCIDO
--------------------
El detector busca asignaciones `objeto.campo = <algo del cuerpo de la petición>`.
**No ve el segundo vector de #832**: `api_expedientes.editar_nodo` no asigna
atributos, pasa `data.get(...)` como argumento a `mutaciones_arbol.editar_*`, cuyo
contrato es "esto es el estado completo deseado". Ese era el más grave de los dos
—`editar_tarea` diffea los vínculos documentales y libera lo que sobre, llevándose
el disparo del plazo (#825)—, y aquí no saltaría.

Es decir: este test cubre el patrón de formulario HTML y **no** el de API JSON. Para
cerrar ese flanco habría que añadir al detector una segunda regla (llamadas con
kwargs `data.get(...)` a funciones de servicio). Mientras tanto, en las rutas de
API el criterio se sostiene solo con la revisión y la regla escrita.
"""
import pytest

from scripts.auditar_escrituras_parciales import recopilar


# Funciones de edición que HOY vacían un campo por omisión y se aceptan como
# deuda conocida — el barrido está en #834. Cada entrada es (fichero, función).
# Ninguna ha causado daño: sus formularios son completos y sus tests fabrican su
# propia fila (comprobado por `xmin` en el diagnóstico de #832).
#
# NO añadir entradas aquí para hacer pasar el test. Si una ruta nueva aparece en
# rojo, el arreglo es `app/utils/formularios.py`, no el manifiesto.
DEUDA_CONOCIDA_834 = {
    ('app/modules/admin_plantillas/routes.py', '_rellenar_plantilla'),
    ('app/modules/admin_plantillas/routes.py', '_plantilla_form_provisional'),
    ('app/modules/admin_requisitos/routes.py', '_rellenar_requisito'),
    ('app/modules/catalogo_plazos/routes.py', '_rellenar_catalogo_plazo'),
    ('app/modules/configuracion_motor/routes.py', '_rellenar_regla'),
    ('app/modules/configuracion_motor/routes.py', '_rellenar_excepcion'),
    ('app/modules/items_tecnicos/routes.py', '_rellenar_item'),
    ('app/modules/normas_variables/routes.py', '_rellenar_norma'),
    ('app/modules/tipos_documentos/routes.py', '_rellenar_tipo'),
    ('app/routes/api_expedientes.py', 'patch_notas_tarea'),
    ('app/routes/api_expedientes.py', 'patch_notificar'),
}

_AYUDA = (
    "Usa app/utils/formularios.py: `leer`/`aplicar_*` solo escriben si el campo "
    "viaja, y `aplicar_checkbox` exige el centinela `_form_completo` porque una "
    "casilla desmarcada no se envía. Ver REGLAS_DESARROLLO.md, "
    "«Rutas que editan un registro existente»."
)


def _funciones_con_vaciado_por_omision():
    """{(fichero, función)} de las que editan un registro y lo vacían por omisión."""
    return {
        (fich, fn)
        for fich, fn, _rutas, naturaleza, asigns in recopilar()
        if naturaleza in ('EDITA', 'MIXTA')
        and any(clase in ('BORRA', 'FALSEA') for _linea, clase, _destino in asigns)
    }


def test_ninguna_ruta_nueva_vacia_por_omision():
    """Una ruta de edición nueva no puede borrar los campos que el cuerpo no envía."""
    nuevas = _funciones_con_vaciado_por_omision() - DEUDA_CONOCIDA_834
    assert not nuevas, (
        "Estas funciones de edición vacían campos que el cuerpo de la petición no "
        f"menciona (#832):\n" +
        '\n'.join(f'  - {fich} :: {fn}()' for fich, fn in sorted(nuevas)) +
        f"\n\n{_AYUDA}"
    )


def test_el_manifiesto_no_tiene_entradas_obsoletas():
    """Lo que ya se arregló sale del manifiesto — así se vacía solo con #834."""
    resueltas = DEUDA_CONOCIDA_834 - _funciones_con_vaciado_por_omision()
    assert not resueltas, (
        "Estas entradas de DEUDA_CONOCIDA_834 ya no tienen el defecto; bórralas "
        "del manifiesto (o de la función, si es que se renombró):\n" +
        '\n'.join(f'  - {fich} :: {fn}()' for fich, fn in sorted(resueltas))
    )


@pytest.mark.parametrize('modulo,funcion', [
    ('app/modules/expedientes/routes.py', 'editar'),
    ('app/modules/perfil/routes.py', 'editar'),
])
def test_las_rutas_arregladas_no_reinciden(modulo, funcion):
    """Guarda explícita sobre las dos que se arreglaron en #832.

    Redundante con el test general mientras el manifiesto siga completo, pero
    sobrevive a él: cuando #834 lo vacíe, estas dos seguirán nombradas.
    """
    assert (modulo, funcion) not in _funciones_con_vaciado_por_omision(), (
        f"{modulo} :: {funcion}() ha vuelto a vaciar campos por omisión. "
        f"Es la regresión exacta de #832.\n\n{_AYUDA}"
    )

"""Lectura de formularios y cuerpos JSON que distingue AUSENTE de VACÍO (#832).

El problema que resuelve
------------------------
Una petición HTTP tiene tres estados posibles para cada campo:

    ausente          el cliente no habla de ese campo
    presente y vacío el usuario lo ha vaciado a propósito
    presente con valor

`request.form.get('x') or None` colapsa los dos primeros en `None`, de modo que
un cliente que envíe un cuerpo parcial **borra en silencio** todo lo que no
menciona. Eso es lo que corrompió `tipo_expediente_id` / `ia_id` /
`solicitudes.observaciones` de varios expedientes de desarrollo en #832, y lo
que obligó a #825 a releer y reponer los CONSUMIDO de una tarea antes de
guardarla.

El criterio
-----------
    ausente          → no se toca el campo (edición parcial legítima)
    presente y vacío → NULL si la columna lo admite; error si es obligatoria
    presente         → se escribe

Checkboxes: en HTML un checkbox desmarcado NO se envía, así que su ausencia es
la forma legítima de decir False y `campo in form` no puede distinguirla de un
cuerpo parcial. Por eso los formularios completos declaran un centinela oculto
(`CENTINELA_FORM_COMPLETO`) y solo entonces se interpreta la ausencia de una
casilla como "desmarcada" — ver `aplicar_checkbox`.
"""
from datetime import date

# Marcador de "el cliente no ha enviado este campo". No usar None: None es un
# valor legítimo en los cuerpos JSON (`{"observaciones": null}` = vaciar).
AUSENTE = object()

# Campo oculto que un formulario HTML completo incluye para declararse como tal.
CENTINELA_FORM_COMPLETO = '_form_completo'


def form_completo(form) -> bool:
    """True si el formulario declara enviar todos sus campos (centinela)."""
    return CENTINELA_FORM_COMPLETO in form


def leer(form, campo):
    """Valor del campo tal cual viene, o `AUSENTE` si no viaja en la petición."""
    if campo not in form:
        return AUSENTE
    return form.get(campo)


def leer_json(data, clave, actual):
    """Valor de `clave` en el cuerpo JSON, o `actual` si la clave no viaja.

    Pensado para las rutas que reenvían el cuerpo a un servicio cuyo contrato es
    "esto es el estado completo deseado" (`mutaciones_arbol.editar_*`): rellenar
    con el valor actual convierte una petición parcial en una equivalente
    completa, sin cambiar la firma del servicio.
    """
    if clave not in data:
        return actual
    return data[clave]


# ---------------------------------------------------------------------------
# Aplicadores — escriben en el objeto solo si el campo viaja
# ---------------------------------------------------------------------------

def aplicar_texto(form, campo, obj, atributo=None):
    """Texto opcional: vacío → NULL. No toca nada si el campo no viaja."""
    valor = leer(form, campo)
    if valor is AUSENTE:
        return
    setattr(obj, atributo or campo, (valor or '').strip() or None)


def aplicar_texto_obligatorio(form, campo, obj, mensaje, errores, atributo=None):
    """Texto de columna NOT NULL: vacío → error de validación, no NULL.

    `errores` es la lista que la ruta acumula y devuelve al cliente, mismo
    patrón que `entidades._recoger_datos_direccion`.
    """
    valor = leer(form, campo)
    if valor is AUSENTE:
        return
    limpio = (valor or '').strip()
    if not limpio:
        errores.append(mensaje)
        return
    setattr(obj, atributo or campo, limpio)


def aplicar_fk(form, campo, obj, atributo=None):
    """Clave foránea opcional: vacío → NULL, valor → int."""
    valor = leer(form, campo)
    if valor is AUSENTE:
        return
    setattr(obj, atributo or campo, int(valor) if valor else None)


def aplicar_numero(form, campo, obj, mensaje, errores, atributo=None, tipo=float):
    """Número opcional: vacío → NULL. Valor no convertible → error."""
    valor = leer(form, campo)
    if valor is AUSENTE:
        return
    crudo = (valor or '').strip()
    if not crudo:
        setattr(obj, atributo or campo, None)
        return
    try:
        setattr(obj, atributo or campo, tipo(crudo))
    except ValueError:
        errores.append(mensaje)


def aplicar_fecha_obligatoria(form, campo, obj, mensaje, errores, atributo=None):
    """Fecha de columna NOT NULL: vacía o inválida → error, nunca NULL."""
    valor = leer(form, campo)
    if valor is AUSENTE:
        return
    crudo = (valor or '').strip()
    if not crudo:
        errores.append(mensaje)
        return
    try:
        setattr(obj, atributo or campo, date.fromisoformat(crudo))
    except ValueError:
        errores.append(mensaje)


def aplicar_checkbox(form, campo, obj, completo, atributo=None):
    """Casilla de verificación. Solo escribe si el formulario es completo.

    En un cuerpo parcial la ausencia de la casilla no significa "desmarcada",
    significa "no la menciona": desmarcarla exige el centinela (`form_completo`).
    """
    if not completo:
        return
    setattr(obj, atributo or campo, form.get(campo) == 'on')

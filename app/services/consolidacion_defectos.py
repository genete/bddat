"""
Consolidación de defectos para el contenedor de la tarea ANALIZAR (#442).

Agrega las contribuciones de los tres proveedores que se enchufan al
contenedor: check documental (#495), check de ítems técnicos (#581) y
selector de requerimientos (#440). Ninguno existe todavía — cada uno es un
issue propio, fuera de alcance de #442 (ver "Orden de construcción" del
issue). Mientras no existan, degrada de forma permisiva: lista vacía y
completo=True, mismo criterio que evaluar_requisitos (#347) — la ausencia
de un proveedor nunca bloquea el contenedor.

FORMA DEL ITEM (cuando existan los proveedores):
    {'texto': str, 'origen': 'documental'|'tecnico'|'requerimiento', 'tarea_id': int}

CAMPO 'completo':
    Señal para el gate de producción del documento de diagnóstico. Cuando
    #495/#581 aterricen, será el AND de "¿queda algo sin revisar?" de cada
    uno — distinto de "sin cubrir" (CoberturaItemTecnico ya distingue
    NO_REVISADO de DESFAVORABLE; lo primero es trabajo pendiente, lo
    segundo es un defecto ya evaluado). Hoy no hay nada que revisar, así
    que degrada a True.
"""
from __future__ import annotations


def consolidar_defectos(tarea) -> dict:
    """
    Consolida los defectos aplicables a la tarea ANALIZAR dada.

    Returns:
        {'items': list, 'completo': bool, 'error': bool}
    """
    return {'items': [], 'completo': True, 'error': False}

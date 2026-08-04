# Módulo "Seguimiento y Huérfanos" (#630 ADR-038). El blueprint vive en
# routes.py y lo autodescubre ModuleRegistry (carpeta con routes.py +
# metadata.json). Hub propio del TRAMITADOR — resuelve el tercer caso de la
# "Deuda conocida" de ADR-017 (antes vista prestada en
# /expedientes/seguimiento/). Dos pestañas: Seguimiento (contenido movido tal
# cual) y Huérfanos (radar nuevo, ADR-027 §2).

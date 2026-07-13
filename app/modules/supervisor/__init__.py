# Módulo "Control y Gestión" (#579 ADR-028, universalizado #588 ADR-029). El
# blueprint vive en routes.py y ModuleRegistry lo autodescubre y registra.
# Tiene metadata.json propio (ADR-029 §2, enmienda ADR-028 §1: antes
# deliberadamente sin él) — genera su propia entrada de sidebar. "Mi trabajo"
# sigue delegando aquí para SUPERVISOR/ADMIN (redundancia asumida).

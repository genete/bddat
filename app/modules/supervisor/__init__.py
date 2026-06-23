# Módulo "Mi trabajo del supervisor" (#579, ADR-028). El blueprint vive en
# routes.py y ModuleRegistry lo autodescubre y registra. Deliberadamente SIN
# metadata.json: así no genera una entrada propia de sidebar — la entrada sigue
# siendo "Mi trabajo" (role-adaptive, ADR-013), que delega aquí para el supervisor.

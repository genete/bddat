# Módulo "Mi Perfil" (migrado desde app/routes/perfil.py en #589, ADR-029).
# El blueprint vive en routes.py y lo autodescubre ModuleRegistry. Sin
# metadata.json: no es ni página-destino de rol ni objeto de dominio (ADR-029
# §1 revisado) — se alcanza por el menú de usuario del topbar, no por sidebar
# ni Command Palette. La tarjeta del dashboard sigue hardcodeada junto a
# "Inicio" (única excepción a la proyección 1:1 de module_nav).

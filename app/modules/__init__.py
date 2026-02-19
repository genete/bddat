"""
Registro de módulos de la aplicación.

Fase 3: registro manual. Auto-discovery queda para Fase 4.

El ModuleRegistry complementa el sistema de blueprints existente en app/routes/.
Los módulos listados en MODULES se registran si su routes.py expone un blueprint 'bp'.
"""
import importlib


class ModuleRegistry:
    """Registro central de módulos de la aplicación."""

    # Lista explícita de módulos. Fase 4 implementará auto-discovery.
    MODULES = ['expedientes', 'entidades']

    @classmethod
    def register_all(cls, app):
        """
        Registra los blueprints de todos los módulos en la app Flask.

        Solo registra módulos cuyo routes.py exponga un blueprint 'bp' no nulo.
        En Fase 3, mientras se produce la migración, un módulo puede estar
        registrado tanto aquí como en app/routes/ — en ese caso routes.py
        debe devolver bp = None para evitar el doble registro.
        """
        for module_name in cls.MODULES:
            module = importlib.import_module(f'app.modules.{module_name}.routes')
            if hasattr(module, 'bp') and module.bp is not None:
                app.register_blueprint(module.bp)

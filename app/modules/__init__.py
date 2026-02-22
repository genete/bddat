"""
Registro de módulos de la aplicación.

Fase 4: auto-discovery por escaneo de directorio + sistema metadata-driven.
Añadir un módulo nuevo = crear carpeta con routes.py y metadata.json,
sin tocar código central.
"""
import importlib
import json
from pathlib import Path


class ModuleRegistry:
    """
    Registro central de módulos.

    Descubre automáticamente los módulos en app/modules/,
    carga sus metadatos y expone la navegación filtrada por rol.
    """

    _metadata_cache: dict = {}

    @classmethod
    def _discover_modules(cls) -> list[str]:
        """
        Escanea app/modules/ y devuelve los nombres de módulos válidos,
        ordenados alfabéticamente.

        Un directorio es un módulo válido si contiene routes.py.
        Los directorios que empiezan por '_' (como __pycache__) se omiten.
        """
        modules_dir = Path(__file__).parent
        return sorted([
            d.name for d in modules_dir.iterdir()
            if d.is_dir()
            and not d.name.startswith('_')
            and (d / 'routes.py').exists()
        ])

    @classmethod
    def register_all(cls, app) -> None:
        """
        Registra los blueprints de todos los módulos descubiertos.

        Solo registra módulos cuyo routes.py exponga un blueprint 'bp' no nulo.
        """
        for module_name in cls._discover_modules():
            module = importlib.import_module(f'app.modules.{module_name}.routes')
            if hasattr(module, 'bp') and module.bp is not None:
                app.register_blueprint(module.bp)

    @classmethod
    def get_metadata(cls, module_name: str) -> dict | None:
        """
        Devuelve el metadata.json del módulo, con caché en memoria.
        Retorna None si el fichero no existe.
        """
        if module_name not in cls._metadata_cache:
            metadata_path = Path(__file__).parent / module_name / 'metadata.json'
            if metadata_path.exists():
                with open(metadata_path, encoding='utf-8') as f:
                    cls._metadata_cache[module_name] = json.load(f)
            else:
                cls._metadata_cache[module_name] = None
        return cls._metadata_cache[module_name]

    @classmethod
    def get_navigation(cls, user_roles: list[str] | None = None) -> list[dict]:
        """
        Devuelve los items de navegación ordenados por 'order',
        filtrados por el permiso 'list' del módulo.

        Args:
            user_roles: Lista de nombres de rol del usuario actual.
                        Si es None o vacía, no se aplica filtro de permisos.

        Returns:
            Lista de dicts con: label, route, icon, order, module.
        """
        nav_items = []

        for module_name in cls._discover_modules():
            metadata = cls.get_metadata(module_name)
            if not metadata:
                continue

            # Filtrar por permiso 'list' si se proporcionan roles
            if user_roles:
                allowed_roles = metadata.get('permissions', {}).get('list', [])
                if not any(r in allowed_roles for r in user_roles):
                    continue

            nav = metadata.get('navigation', {})
            nav_items.append({
                'label':  nav.get('label', module_name.capitalize()),
                'route':  nav.get('route', ''),
                'icon':   metadata.get('icon', 'fa-circle'),
                'order':  metadata.get('order', 99),
                'module': module_name,
            })

        return sorted(nav_items, key=lambda x: x['order'])

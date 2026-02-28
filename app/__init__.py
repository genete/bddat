"""
Factory pattern para crear la aplicación Flask.

Responsabilidades:
- Inicialización de extensiones (db, migrate, login_manager)
- Registro de blueprints
- Configuración de Jinja2
- Manejo de errores HTTP
"""
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from app.config import config

# Instancias de extensiones (sin vincular a app aún)
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()


def create_app(config_name='development'):
    """
    Factory para crear instancia de Flask con configuración.

    Args:
        config_name: Nombre del entorno ('development', 'production') o clase de configuración

    Returns:
        Flask: Instancia configurada de la aplicación
    """
    app = Flask(__name__)

    # Soporte para string o clase de configuración
    if isinstance(config_name, str):
        app.config.from_object(config[config_name])
    else:
        app.config.from_object(config_name)

    # Inicializar extensiones con la app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Configuración de Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Debe iniciar sesión para acceder a esta página.'
    login_manager.login_message_category = 'warning'

    # User loader para Flask-Login
    from app.models.usuarios import Usuario

    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    # Registrar blueprints - Rutas principales
    from app.routes import auth, dashboard, usuarios, perfil

    app.register_blueprint(auth.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(usuarios.bp)
    app.register_blueprint(perfil.bp)

    # Registrar blueprints - Wizards
    from app.routes import wizard_expediente

    app.register_blueprint(wizard_expediente.bp)  # Issue #67

    # Registrar blueprints - APIs
    from app.routes import api_expedientes, api_municipios, vista3, api_entidades, api_proyectos

    app.register_blueprint(api_expedientes.api_bp)          # usa 'api_bp'
    app.register_blueprint(api_municipios.bp)               # usa 'bp'
    app.register_blueprint(vista3.bp)                       # usa 'bp'
    app.register_blueprint(api_entidades.api_entidades_bp)  # usa 'api_entidades_bp' — Issue #61
    app.register_blueprint(api_proyectos.api_proyectos_bp)  # usa 'api_proyectos_bp' — Issue #123

    # Registrar módulos (app/modules/) — Fase 4: auto-discovery
    from app.modules import ModuleRegistry
    ModuleRegistry.register_all(app)

    # Context processor — inyecta navegación de módulos en todos los templates
    @app.context_processor
    def inject_module_nav():
        user_roles = (
            [r.nombre for r in current_user.roles]
            if current_user.is_authenticated else []
        )
        return {
            'module_nav':    ModuleRegistry.get_navigation(user_roles),
            'active_module': request.blueprint,
        }

    # Configuración de Jinja2
    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True

    # Filtros Jinja2 para iconos/colores en V3 tabs (issue #150)
    def _icono_solicitud(estado):
        return {
            'EN_TRAMITE': 'fa-solid fa-file-contract',
            'RESUELTA':   'fa-solid fa-file-circle-check',
            'DESISTIDA':  'fa-solid fa-file-circle-xmark',
            'ARCHIVADA':  'fa-regular fa-file',
        }.get(estado, 'fa-regular fa-file')

    def _color_solicitud(estado):
        return {'EN_TRAMITE': 'text-warning', 'RESUELTA': 'text-success'}.get(estado, 'text-secondary')

    def _icono_fase(estado):
        return {
            'En curso':   'fa-solid fa-sitemap',
            'Finalizada': 'fa-solid fa-sitemap',
        }.get(estado, 'fa-solid fa-sitemap')

    def _color_fase(estado):
        return {'En curso': 'text-warning', 'Finalizada': 'text-success'}.get(estado, 'text-secondary')

    def _icono_tramite(estado):
        return {
            'En curso':   'fa-solid fa-clipboard-list',
            'Finalizado': 'fa-solid fa-clipboard-check',
        }.get(estado, 'fa-regular fa-clipboard')

    def _color_tramite(estado):
        return {'En curso': 'text-warning', 'Finalizado': 'text-success'}.get(estado, 'text-secondary')

    def _icono_tarea(estado):
        return {
            'En curso':   'fa-solid fa-pen-to-square',
            'Finalizada': 'fa-solid fa-square-check',
        }.get(estado, 'fa-regular fa-square')

    def _color_tarea(estado):
        return {'En curso': 'text-warning', 'Finalizada': 'text-success'}.get(estado, 'text-secondary')

    app.jinja_env.filters.update({
        'icono_solicitud': _icono_solicitud, 'color_solicitud': _color_solicitud,
        'icono_fase':      _icono_fase,      'color_fase':      _color_fase,
        'icono_tramite':   _icono_tramite,   'color_tramite':   _color_tramite,
        'icono_tarea':     _icono_tarea,     'color_tarea':     _color_tarea,
    })

    # Manejadores de errores HTTP
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    return app

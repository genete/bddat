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
    from app.routes import auth, dashboard, perfil

    app.register_blueprint(auth.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(perfil.bp)

    # Registrar blueprints - Wizards
    from app.routes import wizard_expediente

    app.register_blueprint(wizard_expediente.bp)  # Issue #67

    # Registrar blueprints - APIs
    from app.routes import api_expedientes, api_municipios, vista3, api_entidades, api_proyectos, api_escritos

    app.register_blueprint(api_expedientes.api_bp)          # usa 'api_bp'
    app.register_blueprint(api_municipios.bp)               # usa 'bp'
    app.register_blueprint(vista3.bp)                       # usa 'bp'
    app.register_blueprint(api_entidades.api_entidades_bp)  # usa 'api_entidades_bp' — Issue #61
    app.register_blueprint(api_proyectos.api_proyectos_bp)  # usa 'api_proyectos_bp' — Issue #123
    app.register_blueprint(api_escritos.api_escritos_bp)    # usa 'api_escritos_bp' — Issue #167

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
        nav = ModuleRegistry.get_navigation(user_roles)

        return {
            'module_nav':    nav,
            'active_module': request.blueprint,
        }

    # Configuración de Jinja2
    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True

    # Filtros Jinja2 para iconos/colores en V3 tabs (issue #150)
    def _icono_solicitud(estado):
        return {
            'EN_TRAMITE': 'bi bi-file-earmark-text',
            'RESUELTA':   'bi bi-file-earmark-check',
            'DESISTIDA':  'bi bi-file-earmark-x',
            'ARCHIVADA':  'bi bi-file-earmark',
        }.get(estado, 'bi bi-file-earmark')

    def _color_solicitud(estado):
        return {'EN_TRAMITE': 'text-primary', 'RESUELTA': 'text-success', 'DESISTIDA': 'text-danger'}.get(estado, 'text-secondary')

    def _icono_fase(estado):
        return 'bi bi-diagram-3-fill' if estado == 'En curso' else 'bi bi-diagram-3'

    def _color_fase(estado):
        return {'En curso': 'text-warning', 'Finalizada': 'text-success'}.get(estado, 'text-secondary')

    def _icono_tramite(estado):
        return {
            'En curso':   'bi bi-clipboard-pulse',
            'Finalizado': 'bi bi-clipboard-check',
        }.get(estado, 'bi bi-clipboard')

    def _color_tramite(estado):
        return {'En curso': 'text-warning', 'Finalizado': 'text-success'}.get(estado, 'text-secondary')

    def _icono_tarea(estado):
        return {
            'En curso':   'bi bi-pencil-square',
            'Finalizada': 'bi bi-check-square',
        }.get(estado, 'bi bi-square')

    def _icono_tarea_tipo(codigo):
        """Icono semántico por tipo de tarea (mockup icons_ESFTT)."""
        return {
            'ANALISIS':     'bi bi-person-gear',
            'REDACTAR':     'bi bi-pencil',
            'FIRMAR':       'bi bi-pen',
            'NOTIFICAR':    'bi bi-send',
            'PUBLICAR':     'bi bi-megaphone',
            'ESPERAR_PLAZO':'bi bi-hourglass-split',
            'INCORPORAR':   'bi bi-box-arrow-in-down',
        }.get(codigo, 'bi bi-square')

    def _color_tarea(estado):
        return {'En curso': 'text-warning', 'Finalizada': 'text-success'}.get(estado, 'text-secondary')

    def _formato_codigo(s):
        """ADMISIBILIDAD_TECNICA → ADMISIBILIDAD TECNICA (para labels de tab)."""
        return s.replace('_', ' ') if s else ''

    app.jinja_env.filters.update({
        'icono_solicitud':  _icono_solicitud,  'color_solicitud': _color_solicitud,
        'icono_fase':       _icono_fase,       'color_fase':      _color_fase,
        'icono_tramite':    _icono_tramite,    'color_tramite':   _color_tramite,
        'icono_tarea':      _icono_tarea,      'color_tarea':     _color_tarea,
        'icono_tarea_tipo': _icono_tarea_tipo,
        'formato_codigo':   _formato_codigo,
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

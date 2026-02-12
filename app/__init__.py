"""
Factory pattern para crear la aplicación Flask.

Responsabilidades:
- Inicialización de extensiones (db, migrate, login_manager)
- Registro de blueprints
- Configuración de Jinja2
- Manejo de errores HTTP
"""
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from app.config import Config

# Instancias de extensiones (sin vincular a app aún)
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()


def create_app(config_class=Config):
    """
    Factory para crear instancia de Flask con configuración.
    
    Args:
        config_class: Clase de configuración (por defecto app.config.Config)
    
    Returns:
        Flask: Instancia configurada de la aplicación
    """
    app = Flask(__name__)
    app.config.from_object(config_class)
    
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
    
    # Registrar blueprints
    from app.routes import auth, dashboard, expedientes, proyectos, usuarios, perfil
    from app.routes import api_expedientes, api_municipios
    from app.routes import vista3
    
    app.register_blueprint(auth.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(expedientes.bp)
    app.register_blueprint(proyectos.bp)
    app.register_blueprint(usuarios.bp)
    app.register_blueprint(perfil.bp)
    app.register_blueprint(api_expedientes.bp)
    app.register_blueprint(api_municipios.bp)
    app.register_blueprint(vista3.bp)
    
    # Configuración de Jinja2
    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True
    
    # Manejadores de errores HTTP
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    return app

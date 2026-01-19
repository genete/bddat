from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from app.config import config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    # Configuración de Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, inicia sesión para acceder a esta página.'
    login_manager.login_message_category = 'warning'
    
    # User loader para Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.usuarios import Usuario
        return Usuario.query.get(int(user_id))
    
    from app import models
    
    # Registrar blueprints
    from app.routes.usuarios import bp as usuarios_bp
    app.register_blueprint(usuarios_bp)
    
    from app.routes.auth import bp as auth_bp
    app.register_blueprint(auth_bp)
    
    from app.routes.perfil import bp as perfil_bp
    app.register_blueprint(perfil_bp)
    
    from app.routes.expedientes import bp as expedientes_bp
    app.register_blueprint(expedientes_bp)
    
    return app

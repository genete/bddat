import os
from app import create_app

# Seleccionar configuración según entorno
env = os.environ.get('FLASK_ENV', 'development')
app = create_app(env)

if __name__ == '__main__':
    app.run()

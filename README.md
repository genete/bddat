# BDDAT - Sistema de Tramitación de Expedientes AT

Sistema de tramitación de expedientes de autorizaciones de instalaciones de alta tensión desarrollado con PostgreSQL, Flask y Bootstrap.

## Características

- Gestión completa de expedientes de autorización técnica (AT)
- Base de datos PostgreSQL con SQLAlchemy ORM
- Interfaz web desarrollada en Flask
- Frontend con Bootstrap 5

## Requisitos

- Python 3.8+
- PostgreSQL
- Dependencias en `requirements.txt`

## Instalación

```bash
# Clonar el repositorio
git clone https://github.com/genete/bddat.git
cd bddat

# Instalar dependencias
pip install -r requirements.txt

# Configurar base de datos (editar app/config.py)

# Ejecutar la aplicación
python run.py
```

## Estructura del Proyecto

```
bddat/
├── app/
│   ├── models/          # Modelos de datos (SQLAlchemy)
│   ├── __init__.py      # Inicialización de la app
│   └── config.py        # Configuración
├── docs/                # Documentación
├── requirements.txt     # Dependencias Python
└── run.py              # Script de ejecución
```

## Licencia

Proyecto en desarrollo
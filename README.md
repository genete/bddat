# BDDAT - Sistema de Tramitación de Expedientes AT

Sistema de tramitación de expedientes de autorizaciones de instalaciones de alta tensión desarrollado con PostgreSQL, Flask y Bootstrap.

## 🚀 Stack Tecnológico

- **Backend**: Python 3.x + Flask + SQLAlchemy
- **Base de datos**: PostgreSQL
- **Frontend**: Bootstrap 5 + Jinja2 templates
- **Autenticación**: Flask-Login

## 📋 Información Legal

**Desarrollado para**: Consejería de Industria, Energía y Minas, Junta de Andalucía  
**Licencia**: European Union Public Licence (EUPL) v1.2  
**Normativa**: Orden de 21 de febrero de 2005 sobre disponibilidad pública de programas informáticos de la Administración de la Junta de Andalucía (BOJA nº 49, 10/03/2005)

### Propiedad Intelectual

El software desarrollado por empleados públicos de la Junta de Andalucía en el ejercicio de sus funciones es propiedad de la Administración y debe ponerse a disposición de la sociedad mediante la liberación de su código fuente, conforme a la normativa vigente.

### Seguridad y Datos Sensibles

Este repositorio ha sido **revisado y verificado** antes de su publicación para garantizar que no contiene:
- ❌ Credenciales o contraseñas
- ❌ Datos personales reales
- ❌ Información de expedientes reales
- ❌ Detalles de infraestructura interna
- ❌ Secretos de configuración

Ver [SECURITY.md](SECURITY.md) para detalles completos de la revisión de seguridad.


## 📦 Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/[tu-usuario]/bddat.git
cd bddat
```

2. Crear entorno virtual y instalar dependencias:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Configurar variables de entorno:
```bash
cp .env.example .env
# Editar .env con tus credenciales locales
```

4. Inicializar base de datos:
```bash
flask db upgrade
```

5. Ejecutar en desarrollo:
```bash
flask run
```
## 🔧 Configuración

Ver `.env.example` para las variables de entorno requeridas.

**⚠️ IMPORTANTE**: Antes de desplegar en producción:
- Genera una SECRET_KEY segura: `python -c "import secrets; print(secrets.token_hex(32))"`
- Configura credenciales de base de datos apropiadas
- Habilita HTTPS/SSL
- Revisa configuración de seguridad según ENS

## 🤝 Contribuciones

Este proyecto está en desarrollo activo. Las contribuciones son bienvenidas siguiendo estas directrices:

1. Fork del proyecto
2. Crear rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit de cambios (`git commit -m 'feat: añadir nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abrir Pull Request


## 📂 Estructura del Proyecto
```
bddat/
├── app/
│   ├── models/          # Modelos de datos (SQLAlchemy)
│   ├── routes/          # Rutas y controladores
│   ├── templates/       # Plantillas Jinja2
│   ├── static/          # CSS, JS, assets
│   ├── __init__.py      # Inicialización de la app
│   └── config.py        # Configuración
├── migrations/          # Migraciones de base de datos (Alembic)
├── docs/                # Documentación técnica
├── .env.example         # Plantilla de configuración
├── requirements.txt     # Dependencias Python
├── LICENSE              # Licencia EUPL v1.2
├── SECURITY.md          # Política de seguridad
└── run.py              # Script de ejecución
```

## Licencia

Copyright © 2025-2026 Junta de Andalucía

Este proyecto está licenciado bajo la European Union Public Licence (EUPL) v1.2.  
Ver archivo [LICENSE](LICENSE) para detalles.

Texto completo de la licencia: https://joinup.ec.europa.eu/collection/eupl/eupl-text-eupl-12

## ℹ️ Contacto

Para consultas sobre este proyecto, contactar con el equipo de desarrollo usando herramientas de Github.

---

**Desarrollado con** ❤️ **para la Junta de Andalucía**
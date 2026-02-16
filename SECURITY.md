# Política de Seguridad

## Revisión de Seguridad del Repositorio

Este repositorio ha sido revisado antes de su publicación para garantizar que no contiene información sensible.

### ✅ Verificaciones realizadas (Febrero 2026)

Se han realizado las siguientes comprobaciones de seguridad:

1. **Credenciales y secretos**
   - ✅ No hay contraseñas hardcodeadas
   - ✅ SECRET_KEY y DATABASE_URL se cargan desde variables de entorno
   - ✅ Archivo `.env` excluido vía `.gitignore`
   - ✅ `.env.example` proporcionado como plantilla sin datos reales

2. **Información de infraestructura**
   - ✅ No hay IPs internas de la red corporativa
   - ✅ No hay nombres de servidores específicos
   - ✅ No hay referencias a sistemas legacy con información sensible

3. **Datos personales y expedientes**
   - ✅ No hay datos personales reales
   - ✅ No hay información de expedientes reales
   - ✅ Solo datos estructurales públicos (municipios, tipos, clasificaciones)

4. **Tokens y claves API**
   - ✅ No hay tokens de autenticación hardcodeados
   - ✅ Tokens de recuperación de contraseña se generan dinámicamente

### 🔒 Política de Desarrollo Seguro

Este proyecto sigue las siguientes prácticas de seguridad:

- **Variables de entorno**: Todas las credenciales y configuraciones sensibles se gestionan mediante variables de entorno
- **Gitignore**: Archivos sensibles (`.env`, `*.log`, `instance/`) están excluidos del control de versiones
- **Revisión de código**: Todos los commits son revisados antes de merge a `main`
- **Sin datos reales en desarrollo**: Los datos de prueba son ficticios

### 🛡️ Reportar Vulnerabilidades

Si encuentras una vulnerabilidad de seguridad en este código:

1. **NO** abras un issue público
2. Contacta directamente con el equipo de desarrollo
3. Proporciona detalles técnicos y pasos para reproducir
4. Permite tiempo razonable para corregir antes de divulgación pública

### ⚠️ Descargo de Responsabilidad

Este repositorio contiene **código fuente únicamente**. El despliegue en producción requiere:

- Configuración segura de variables de entorno
- SECRET_KEY criptográficamente segura (generada con `secrets.token_hex(32)`)
- Credenciales de base de datos apropiadas
- Configuración de firewall y red según políticas de seguridad corporativas
- Certificados SSL/TLS para HTTPS en producción

### 📋 Cumplimiento Normativo

Este proyecto cumple con:

- **Orden de 21 de febrero de 2005** (Junta de Andalucía): Disponibilidad pública de software
- **EUPL v1.2**: Licencia para administraciones públicas europeas
- **Esquema Nacional de Seguridad (ENS)**: Aplicable según nivel de clasificación del despliegue

---

**Última revisión de seguridad**: Febrero 2026

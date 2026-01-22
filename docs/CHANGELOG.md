# CHANGELOG - BDDAT

Registro de cambios del proyecto de tramitación administrativa de expedientes de autorización de instalaciones de alta tensión.

**Repositorio:** https://github.com/genete/bddat  
**Última actualización:** 22 de enero de 2026  
**Versión actual:** 1.0.0

---

## Índice

- [2026-01-22 - PR #18: Fix Email Duplicado en Usuarios](#2026-01-22---pr-18-fix-email-duplicado-en-usuarios)
- [2026-01-21 - Mejoras UX en Módulo Expedientes](#2026-01-21---mejoras-ux-en-módulo-expedientes)
- [2026-01-21 - Feature: Unificación Listado Expedientes](#2026-01-21---feature-unificación-listado-expedientes)
- [2026-01-21 - Feature: Mis Expedientes](#2026-01-21---feature-mis-expedientes)

---

## 2026-01-22 - PR #18: Fix Email Duplicado en Usuarios

**Issues relacionados:** #12, #13  
**Autor:** genete / IA  
**Rama:** `fix/email-unique-constraint-issues-12-13` → `main`

### Problema Identificado

Al intentar editar usuarios (cambiar siglas, modificar contraseña, etc.) se producía error de constraint UNIQUE violada en el campo `email`:

```
Error: (psycopg2.errors.UniqueViolation) llave duplicada viola restricción de unicidad «usuarios_email_key»
DETAIL: Ya existe la llave (email)=().
```

**Causa raíz:** Múltiples usuarios con `email = ''` (cadena vacía). PostgreSQL considera múltiples cadenas vacías como valores idénticos, violando el constraint UNIQUE.

### Cambios en Base de Datos

- **Migración de datos necesaria:**
  ```sql
  UPDATE usuarios SET email = NULL WHERE email = '';
  ```

### Cambios en Modelos

**Archivo:** `app/models/usuarios.py`

- Convertido campo `email` a property con setter automático
- Setter convierte cadenas vacías (`''`) a `NULL` automáticamente
- PostgreSQL permite múltiples valores `NULL` en campos UNIQUE (no violan constraint)

```python
_email = db.Column('email', db.String(120), unique=True, nullable=True)

@property
def email(self):
    return self._email

@email.setter
def email(self, value):
    """Convierte cadenas vacías a None para evitar violación de constraint UNIQUE"""
    if value == '' or (isinstance(value, str) and value.strip() == ''):
        self._email = None
    else:
        self._email = value
```

### Cambios en Rutas

**Archivo:** `app/routes/usuarios.py`

- Añadida importación: `from sqlalchemy.exc import IntegrityError`
- Captura específica de error `usuarios_email_key` en creación y edición
- Preservación de datos del formulario cuando hay error (no se pierde información ingresada)
- Variable `error_email` para feedback específico al usuario

**Funciones modificadas:**
- `index()` - Creación de usuarios
- `editar()` - Actualización de usuarios

### Cambios en Templates

**Archivo:** `app/templates/usuarios/editar.html`

- Campo email con validación visual Bootstrap
- Clase `is-invalid` cuando hay error de email duplicado
- Mensaje `invalid-feedback` bajo el campo con explicación clara
- Preservación de datos en caso de error

**Archivo:** `app/templates/usuarios/index.html`

- Añadido campo email en modal de creación (antes no existía)
- Validación visual idéntica a formulario de edición
- Placeholder: "usuario@ejemplo.com"

### Comportamiento Antes vs Después

#### Antes del Fix
- ❌ Error al guardar usuario con email vacío
- ❌ Modal/formulario se cierra perdiendo todos los datos
- ❌ Mensaje genérico sin indicar campo responsable
- ❌ Múltiples usuarios con `email = ''` causan conflictos

#### Después del Fix
- ✅ Email vacío se guarda como `NULL` automáticamente
- ✅ Modal/formulario permanece abierto con datos preservados
- ✅ Mensaje claro bajo el campo email responsable
- ✅ Múltiples `NULL` permitidos por PostgreSQL
- ✅ Experiencia no intrusiva (mensaje tipo tooltip Bootstrap)

### Commits
1. `fc190de` - [MODELO] Convertir email vacío a NULL automáticamente
2. `56207bf` - [RUTA] Capturar error email duplicado y mantener diálogo abierto
3. `84d1f67` - [TEMPLATE] Añadir validación visual de email duplicado (edición)
4. `b9f9e39` - [TEMPLATE] Añadir validación de email en modal creación

### Testing Realizado
- ✅ Crear usuario sin email → Se guarda como NULL
- ✅ Editar usuario dejando email vacío → Se guarda como NULL sin errores
- ✅ Crear dos usuarios con mismo email → Error en campo, modal abierto
- ✅ Editar usuario con email existente → Error en campo, formulario abierto
- ✅ Preservación de datos cuando hay error
- ✅ Cambiar siglas + contraseña (Issue #12)
- ✅ Editar usuario sin email (Issue #13)

---

## 2026-01-21 - Mejoras UX en Módulo Expedientes

**Autor:** IA  
**Rama:** `fix/expedientes-ux-improvements` → `main`

### Cambios en Templates

#### 1. Nomenclatura Consistente: "Instrumento Ambiental"

**Problema:** Label inconsistente "Tipo de Instalación de Alta Tensión" confundía el concepto real del campo (almacena Instrumento Ambiental).

**Archivos modificados:**
- `app/templates/expedientes/nuevo.html` (L107: label, L109: placeholder)
- `app/templates/expedientes/editar.html` (L114: label, L116: placeholder)

**Cambios:**
- ✅ Label actualizado a "Instrumento Ambiental"
- ✅ Placeholder: "-- Sin instrumento ambiental --"

#### 2. Instrumento Ambiental como Campo Normal

**Problema:** En `detalle.html` se mostraba como alert amarillo/verde destacado, cuando debería ser un campo más del proyecto.

**Archivo:** `app/templates/expedientes/detalle.html` (L100-112)

**Antes:**
```html
<div class="alert alert-warning">
    <i class="fas fa-exclamation-triangle"></i>
    <strong>Instalación de Alta Tensión:</strong> ...
</div>
```

**Después:**
```html
<h6 class="text-muted">Instrumento Ambiental</h6>
<p>
    <span class="badge bg-success">AAU</span>
    <span>Autorización Ambiental Unificada</span>
</p>
```

#### 3. Flujo de Navegación: Botón Cancelar

**Problema:** En `editar.html`, Cancelar redireccionaba a `detalle` (vista intermedia innecesaria). Usuario esperaba volver al listado.

**Archivo:** `app/templates/expedientes/editar.html` (L132)

**Flujo corregido:**
```
Listado → Editar → [Cancelar] → Listado ✅
Listado → Detalle → Editar → [Cancelar] → Listado ✅
```

**Cambio:** `url_for('expedientes.detalle')` → `url_for('expedientes.index')`

#### 4. Visualización Heredado: Semántica del Listado

**Problema:** `detalle.html` mostraba switch deshabilitado (control de edición en vista de solo lectura).

**Archivo:** `app/templates/expedientes/detalle.html` (L60-65)

**Solución:**
- ✅ **Solo si `heredado == True`**: Mostrar check verde + etiqueta
- ✅ **Si `heredado == False`**: No mostrar nada (no ocupar espacio)
- ✅ Mismo estilo que en tabla listado: `fa-check-circle text-success`

### Resumen de Cambios

| Cambio | Archivos | Líneas |
|--------|----------|--------|
| Nomenclatura IA | nuevo.html, editar.html | 4 |
| IA campo normal | detalle.html | 13 |
| Flujo cancelar | editar.html | 1 |
| Heredado semántico | detalle.html | 6 |
| **TOTAL** | **3 templates** | **24** |

### Commits
5 commits en rama `fix/expedientes-ux-improvements`

---

## 2026-01-21 - Feature: Unificación Listado Expedientes

**Autor:** IA  
**Rama:** `feature/tabla-expedientes-unificada` → `main`

### Objetivo

Unificar completamente el listado de expedientes en una sola vista con filtrado opcional, eliminando duplicación de código y mejorando la experiencia de usuario.

### Cambios en Rutas

**Archivo:** `app/routes/expedientes.py`

- Lógica unificada en `index()` con parámetro opcional `?mis_expedientes=1`
- Filtrado condicional por rol:
  - **TRAMITADOR:** Siempre ve solo sus expedientes
  - **ADMIN/SUPERVISOR:** 
    - Sin parámetro: Ve todos los expedientes
    - Con `?mis_expedientes=1`: Ve solo sus expedientes

**Archivo:** `app/routes/dashboard.py`

- Redirección desde `/mis_expedientes` a `/expedientes/?mis_expedientes=1`
- Mantiene compatibilidad con enlaces existentes

### Cambios en Modelos

**Archivo:** `app/models/proyectos.py`

- Agregada relación `ia` (Instrumento Ambiental) al modelo

### Cambios en Templates

**Archivo:** `app/templates/expedientes/index.html`

#### 1. Estadísticas en la Parte Superior
- Movidas al inicio, debajo del título
- Muestra: Siglas y nombre del usuario + Total de expedientes
- No requiere scroll para ver métricas
- Preparado para futuras estadísticas (activos, heredados, por tipo)

#### 2. Cabeceras Multilinea
- Usa `<br>` para columnas estrechas:
  - "Número<br>AT"
  - "Tipo<br>Expediente"
  - "Instrumento<br>Ambiental"

#### 3. Elipsis en Textos Largos
- **Título proyecto:** max-width 250px con `text-truncate`
- **Finalidad:** max-width 250px con `text-truncate`
- Tooltip muestra texto completo al hover

#### 4. Columna Heredado Simplificada
- Solo muestra icono check verde cuando ES heredado
- Celda vacía cuando NO es heredado (más limpio)
- Color verde (`text-success`) alineado con colores oficiales

#### 5. Colores Unificados
- Cabecera: `table-success` (verde) en todas las vistas
- Badges consistentes (info, success)

#### 6. Columna Responsable Restaurada
- Presente en listado general
- Responsive: `d-none d-xxl-table-cell` (≥1400px)
- Badge "Tú" cuando es el usuario actual

**Archivo eliminado:** `app/templates/dashboard/mis_expedientes.html` (ya no necesario)

### Estructura Final de Tabla

| Columna | Ancho | Responsive | Descripción |
|---------|-------|------------|-------------|
| **Número AT** | Auto | Siempre | `AT-{numero}` enlace azul |
| **Proyecto** | 250px | Siempre | Título bold + Finalidad gris (elipsis) |
| **Tipo Expediente** | Auto | ≥768px | Badge azul info |
| **Instrumento Ambiental** | Auto | ≥992px | Badge verde con siglas |
| **Heredado** | Auto | ≥1200px | Check verde solo si heredado |
| **Responsable** | Auto | ≥1400px | Siglas + badge "Tú" si aplica |
| **Acciones** | Auto | Siempre | Ver/Editar agrupados |

### Ventajas de Esta Arquitectura

1. ✅ **DRY:** Un solo template, una sola lógica
2. ✅ **Mantenibilidad:** Cambios en UN lugar afectan todas las vistas
3. ✅ **Consistencia:** UI/UX idéntica en filtrado y sin filtrar
4. ✅ **SEO-friendly:** URL semántica con query parameter
5. ✅ **Escalable:** Fácil agregar más filtros (por tipo, estado, etc.)
6. ✅ **Performance:** Una sola consulta SQL optimizada

### Commits
7 commits (incluye fix relación IA y refactor completo)

---

## 2026-01-21 - Feature: Mis Expedientes

**Autor:** IA  
**Rama:** `feature/mis-expedientes` → `main`

### Objetivo

Implementar funcionalidad completa para que los usuarios puedan ver los expedientes donde son responsables, con navegación desde el Dashboard.

### Cambios en Rutas

**Archivo:** `app/routes/dashboard.py`

- Añadido import del modelo `Expediente`
- Modificado URL de 'Mis expedientes' de `#` a `dashboard.mis_expedientes`
- Añadida nueva ruta `@bp.route('/mis_expedientes')` con:
  - Filtro por `responsable_id=current_user.id`
  - Ordenamiento por `numero_at` descendente
  - Renderiza template `dashboard/mis_expedientes.html`

### Cambios en Templates

**Archivo creado:** `app/templates/dashboard/mis_expedientes.html`

- Extiende `base.html`
- Breadcrumbs: Inicio → Mis Expedientes
- Contenido:
  - Encabezado con botón "Nuevo Expediente"
  - Tabla responsive con columnas:
    - Número AT (badge azul, enlace a detalle)
    - Proyecto (título + emplazamiento)
    - Tipo de Expediente (badge info)
    - Estado (Heredado/Activo con iconos)
    - Acciones (Ver/Editar)
  - Footer con contador de expedientes
  - Mensaje cuando no hay expedientes asignados
  - Botón "Volver al Dashboard"

### Cambios en Estilos

**Archivo:** `app/static/css/custom.css`

- Efectos hover en items de lista del dashboard
  - Transición suave 0.2s
  - Desplazamiento 4px a la derecha al hover
  - Color azul Bootstrap
- Efecto hover en cards
  - Sombra elevada
  - Transición 0.3s
- Hover en badges de tabla
  - Escala 1.05
  - Sombra sutil
- Hover mejorado en button groups
  - Elevación visual
  - Z-index dinámico

### Funcionalidades Implementadas

1. ✅ Enlace funcional desde Dashboard a "Mis expedientes"
2. ✅ Filtrado automático por usuario logueado
3. ✅ Tabla con información completa del expediente
4. ✅ Navegación con breadcrumbs
5. ✅ Estados visuales diferenciados (Heredado/Activo)
6. ✅ Acciones rápidas (Ver/Editar)
7. ✅ Contador de expedientes asignados
8. ✅ Estado vacío con mensaje informativo
9. ✅ Efectos hover profesionales
10. ✅ Responsive design con Bootstrap 5

### Notas

- **Relación 1:1 confirmada:** Expediente ↔ Proyecto (UNIQUE constraint en `expedientes.proyecto_id`)
- **Filtraje seguro:** Usa `current_user.id` de Flask-Login
- **Naming:** Todo en `snake_case` según convenciones del proyecto
- **Sin migraciones:** No hay cambios en BD, solo lógica de vistas

---

**Documento generado:** 22 de enero de 2026  
**Formato:** Markdown  
**Ubicación:** `docs/CHANGELOG.md`

# CHANGELOG - BDDAT

Registro de cambios del proyecto de tramitación administrativa de expedientes de autorización de instalaciones de alta tensión.

**Repositorio:** https://github.com/genete/bddat  
**Última actualización:** 22 de enero de 2026  
**Versión actual:** 1.0.0

---

## Índice

- [2026-01-22 - PR #19: Arquitectura v3.0 Tipos Individuales + Tabla Puente](#2026-01-22---pr-19-arquitectura-v30-tipos-individuales--tabla-puente)
- [2026-01-22 - PR #18: Fix Email Duplicado en Usuarios](#2026-01-22---pr-18-fix-email-duplicado-en-usuarios)
- [2026-01-21 - Mejoras UX en Módulo Expedientes](#2026-01-21---mejoras-ux-en-módulo-expedientes)
- [2026-01-21 - Feature: Unificación Listado Expedientes](#2026-01-21---feature-unificación-listado-expedientes)
- [2026-01-21 - Feature: Mis Expedientes](#2026-01-21---feature-mis-expedientes)

---

## 2026-01-22 - PR #19: Arquitectura v3.0 Tipos Individuales + Tabla Puente

**Pull Request:** [#19](https://github.com/genete/bddat/pull/19)  
**Autor:** Sistema IA (Perplexity) / genete  
**Rama:** `docs/fuentes-ia-desde-space` → `main`  
**Tipo:** Documentación (sin cambios en código)

### Objetivo

Implementar documentación completa de la **arquitectura v3.0 de tipos de solicitudes individuales**, sustituyendo el sistema de 20+ tipos combinados hardcodeados (AAP+AAC, AAP+DUP, AAP+AAC+DUP, etc.) por:

- **17 tipos individuales** en tabla maestra `tipos_solicitudes`
- **Tabla puente N:M** `solicitudes_tipos` para gestionar combinaciones flexibles
- **Adaptabilidad a nuevas normativas:** RDL 7/2025 (división AAE), RADNE Andalucía, RAIPEE renovables

### Archivos Nuevos

#### 1. `docs/fuentesIA/datos_maestros.sql` (3.3 KB)

**Propósito:** Script SQL con datos iniciales para poblar tablas maestras en BD limpia.

**Contenido:**

- **8 tipos de expedientes:**
  - Particular Línea BT/MT/AT
  - Distribuidora Línea AT
  - Productor Generación Renovable
  - Autoconsumo
  - Transporte (Red Española)
  - Almacenamiento Energético

- **5 tipos de instrumento ambiental:**
  - AAU (Autorización Ambiental Unificada)
  - AAUS (AAU Simplificada)
  - CA (Calificación Ambiental)
  - No sujeto
  - DIA (Declaración Impacto Ambiental - grandes proyectos)

- **11 tipos de fases procedimentales:**
  - ADMISIBILIDAD
  - ANALISIS_TECNICO
  - CONSULTAS
  - INFORMACION_PUBLICA
  - SUBSANACION
  - AUDIENCIA_INTERESADOS
  - RESOLUCION
  - NOTIFICACION
  - ARCHIVO
  - SUSPENSION
  - RECURSO

- **17 tipos de solicitudes individuales (v3.0):**
  - **Fase PREVIA:** AAP
  - **Fase CONSTRUCCIÓN:** AAC
  - **Declaración Utilidad Pública:** DUP
  - **Fase EXPLOTACIÓN:** AAE_PROVISIONAL, AAE_DEFINITIVA (⭐ RDL 7/2025)
  - **Transmisión:** AAT
  - **RAIPEE Renovables:** RAIPEE_PREVIA, RAIPEE_DEFINITIVA
  - **RADNE Autoconsumo:** RADNE (⭐ Obligatorio AT Andalucía desde 2024)
  - **Cierre:** CIERRE
  - **Actos administrativos:** DESISTIMIENTO, RENUNCIA, AMPLIACION_PLAZO, INTERESADO, RECURSO
  - **Otros:** CORRECCION_ERRORES, OTRO

**Uso:** Ejecutar después de `schema.sql` en nueva instalación.

#### 2. `docs/fuentesIA/SOLICITUDES_TIPOS.md` (7.5 KB)

**Propósito:** Documentación completa de tabla puente N:M `solicitudes_tipos`.

**Contenido:**

**Estructura tabla:**
```sql
CREATE TABLE solicitudes_tipos (
  id SERIAL PRIMARY KEY,
  solicitud_id INTEGER NOT NULL REFERENCES solicitudes(id) ON DELETE CASCADE,
  tipo_solicitud_id INTEGER NOT NULL REFERENCES tipos_solicitudes(id),
  UNIQUE (solicitud_id, tipo_solicitud_id)
);
```

**Filosofía arquitectura v3.0:**
- **Antes (v2.0):** Tipos combinados hardcodeados (AAP+AAC, AAP+DUP, AAP+AAC+DUP...)
- **Ahora (v3.0):** Tipos individuales + tabla puente para combinaciones flexibles

**Ejemplos SQL incluidos:**
- Solicitud simple (AAP)
- Solicitud combinada (AAP + AAC)
- Solicitud triple (AAP + AAC + DUP)
- Renovables con RAIPEE (AAP + RAIPEE_PREVIA, AAE_DEFINITIVA + RAIPEE_DEFINITIVA)
- Autoconsumo Andalucía (AAP + AAC + RADNE)
- Explotación RDL 7/2025 (AAE_PROVISIONAL, AAE_DEFINITIVA)

**Consultas típicas documentadas:**
- Obtener todos los tipos de una solicitud
- Verificar si solicitud incluye tipo específico
- Buscar solicitudes con combinación específica
- Contar solicitudes por tipo individual (estadísticas)

**Reglas de negocio:**
- Validación de tipos incompatibles (AAE_PROVISIONAL y AAE_DEFINITIVA excluyentes)
- Validación de secuencias temporales (RAIPEE_DEFINITIVA requiere PREVIA anterior)
- Requisitos legales (DUP requiere AAP/AAC, RADNE obligatorio Andalucía)
- Coherencia con tipo de expediente

**Guía completa de migración desde v2.0:** Scripts SQL para convertir tipos combinados en individuales.

**Ventajas arquitectura v3.0:**
1. Flexibilidad total (cualquier combinación sin modificar maestras)
2. Escalabilidad (nuevos tipos una sola vez, no 10+ combinaciones)
3. Mantenibilidad (17 tipos vs 20+ combinaciones)
4. Adaptabilidad normativa (RDL 7/2025 sin reestructuración)
5. Estadísticas precisas (conteo individual AAP, AAC, DUP, etc.)
6. Validaciones específicas (reglas por tipo, no por combinación)
7. Trazabilidad (histórico claro de qué se solicitó)

#### 3. `docs/fuentesIA/TIPOS_SOLICITUDES_v3.md` (10.2 KB)

**Propósito:** Documentación actualizada de tabla maestra `tipos_solicitudes` con arquitectura v3.0.

**Contenido:**

**Cambio de filosofía:**
- **v2.0:** 20+ tipos combinados (AAP, AAC, AAP+AAC, AAP+DUP, AAC+DUP, AAP+AAC+DUP, AAE+AAT...)
- **v3.0:** 17 tipos individuales + combinaciones mediante tabla puente

**Catálogo completo clasificado por bloques legales:**

1. **Fase PREVIA (art. 53.1.a LSE 24/2013)**
   - AAP: Autorización Administrativa Previa

2. **Fase CONSTRUCCIÓN (art. 53.1.b LSE)**
   - AAC: Autorización Administrativa de Construcción

3. **Declaración Utilidad Pública (art. 54 LSE)**
   - DUP: Declaración de Utilidad Pública (expropiación forzosa)

4. **Fase EXPLOTACIÓN (art. 53.1.c LSE + RDL 7/2025)** ⭐ **NOVEDAD 2025**
   - AAE_PROVISIONAL: Autorización Explotación Provisional para Pruebas (máx. 6 meses)
   - AAE_DEFINITIVA: Autorización Explotación Definitiva (requiere PROVISIONAL previa)

5. **Transmisión de Titularidad (art. 56 LSE)**
   - AAT: Autorización de Transmisión de Titularidad

6. **RAIPEE Renovables (RD 413/2014 art. 37-42)**
   - RAIPEE_PREVIA: Inscripción Previa (reserva punto conexión)
   - RAIPEE_DEFINITIVA: Inscripción Definitiva (instalación construida)

7. **RADNE Autoconsumo (RD 244/2019)** ⭐ **Andalucía 2024: Obligatorio AT**
   - RADNE: Inscripción en Registro de Autoconsumo

8. **Cierre de Instalación (art. 53.1.d LSE)**
   - CIERRE: Autorización de Cierre de Instalación
9. **Actos sobre Solicitudes (art. 94 Ley 39/2015)**
   - DESISTIMIENTO: Desistimiento de la Solicitud
   - RENUNCIA: Renuncia de la Autorización

10. **Gestión de Expedientes**
    - AMPLIACION_PLAZO: Ampliación de Plazo de Ejecución
    - INTERESADO: Condición de Interesado en el Expediente
    - RECURSO: Recurso Administrativo

11. **Otros Procedimientos**
    - CORRECCION_ERRORES: Corrección de Errores en Resolución
    - OTRO: Otro tipo de solicitud

**Combinaciones típicas documentadas:**
- Transporte/Distribución con DUP: AAP + AAC + DUP
- Renovable con RAIPEE: AAP + RAIPEE_PREVIA / AAE_DEFINITIVA + RAIPEE_DEFINITIVA
- Autoconsumo AT Andalucía: AAP + AAC + RADNE
- Explotación nueva normativa: AAE_PROVISIONAL → AAE_DEFINITIVA

**Tipos especiales:**
- DESISTIMIENTO/RENUNCIA: Requieren `SOLICITUD_AFECTADA_ID` NOT NULL
- RAIPEE: Secuencia PREVIA → DEFINITIVA obligatoria
- AAE: Secuencia PROVISIONAL → DEFINITIVA obligatoria (RDL 7/2025)

**Validaciones de combinaciones:**
- DUP requiere AAP o AAC simultánea/previa
- AAE_DEFINITIVA requiere AAE_PROVISIONAL previa
- RAIPEE_DEFINITIVA requiere RAIPEE_PREVIA previa
- RADNE solo para tipo_expediente = 'Autoconsumo'
- RAIPEE solo para tipo_expediente = 'Renovable'

**Marco legal actualizado:**
- LSE 24/2013 (base autorizaciones eléctricas)
- RDL 7/2025 (división AAE provisional/definitiva)
- RD 1955/2000 (procedimiento transporte/distribución/producción)
- RD 413/2014 (RAIPEE renovables)
- RD 244/2019 (RADNE autoconsumo)
- Ley 39/2015 (Procedimiento Administrativo Común)
- Normativa autonómica Andalucía (RADNE obligatorio AT desde 2024)

**Estrategia de migración v2.0 → v3.0:**
- Mantener `SOLICITUDES.TIPO_SOLICITUD_ID` temporalmente
- Poblar `SOLICITUDES_TIPOS` dividiendo combinados en individuales
- Actualizar aplicación para consultar tabla puente
- Deprecar y eliminar campo antiguo en versión futura

### Cambios en Base de Datos (Futuro)

**Nota:** Este PR **solo incluye documentación**. Los cambios en `schema.sql` y migraciones se aplicarán en PR separado posterior.

**Tabla nueva planeada:**
```sql
CREATE TABLE solicitudes_tipos (
  id SERIAL PRIMARY KEY,
  solicitud_id INTEGER NOT NULL REFERENCES solicitudes(id) ON DELETE CASCADE,
  tipo_solicitud_id INTEGER NOT NULL REFERENCES tipos_solicitudes(id),
  UNIQUE (solicitud_id, tipo_solicitud_id)
);

CREATE INDEX idx_solicitudes_tipos_solicitud ON solicitudes_tipos(solicitud_id);
CREATE INDEX idx_solicitudes_tipos_tipo ON solicitudes_tipos(tipo_solicitud_id);
```

**Datos maestros a actualizar:**
- `tipos_solicitudes`: 17 tipos individuales (eliminar combinados)

### Ventajas Arquitectura v3.0

| Aspecto | v2.0 (Antes) | v3.0 (Ahora) |
|---------|--------------|-------------|
| **Número de tipos maestros** | 20+ combinaciones | 17 individuales |
| **Nuevas combinaciones** | Modificar maestra (ej: AAP+AAC+DUP+AAT) | Automático (tabla puente) |
| **Adaptación normativa** | Reestructuración completa | Añadir tipo individual |
| **Estadísticas** | Por combinación completa | Por tipo individual |
| **Validaciones** | Hardcoded por combo | Reglas por tipo |
| **Mantenibilidad** | Baja (duplicación) | Alta (DRY) |
| **Escalabilidad** | Limitada (crecimiento exponencial) | Infinita (crecimiento lineal) |
| **Trazabilidad** | Combo completo | Cada tipo solicitado |

### Novedades Normativas Incorporadas

#### RDL 7/2025: División AAE Provisional/Definitiva

**Problema anterior:** AAE única autorizaba explotación inmediata, pero instalación necesita pruebas previas.

**Solución RDL 7/2025:**
- **AAE_PROVISIONAL:** Autorización temporal (máximo 6 meses) para pruebas de funcionamiento. NO permite facturación comercial.
- **AAE_DEFINITIVA:** Autorización permanente de explotación comercial. Requiere AAE_PROVISIONAL previa concedida.

**Secuencia obligatoria:**
```
AAC concedida → Construcción → AAE_PROVISIONAL → Pruebas (6 meses) → AAE_DEFINITIVA → Explotación comercial
```

**Implementación en v3.0:** Dos tipos individuales independientes con validación de secuencia en motor de reglas.

#### RADNE Autoconsumo Andalucía (Obligatorio desde 2024)

**Contexto:** RD 244/2019 crea Registro Administrativo de Autoconsumo de Energía Eléctrica (RADNE).

**Novedad Andalucía 2024:** Inscripción en RADNE pasa a ser **obligatoria** para instalaciones de autoconsumo en **alta tensión** (antes era voluntario o solo BT).

**Combinación típica:**
```
AAP + AAC + RADNE (simultáneos para autoconsumo AT en Andalucía)
```

**Validación:** RADNE solo aplicable a `tipo_expediente = 'Autoconsumo'`.

#### RAIPEE Renovables (RD 413/2014)

**Contexto:** Registro Administrativo de Instalaciones de Producción de Energía Eléctrica (RAIPEE).

**Secuencia normativa:**
1. **RAIPEE_PREVIA (art. 37-39):** Inscripción previa que reserva punto de conexión. Se solicita con AAP o antes.
2. **RAIPEE_DEFINITIVA (art. 40-42):** Inscripción definitiva tras instalación construida. Se solicita con AAE_DEFINITIVA.

**Validación:** RAIPEE solo aplicable a `tipo_expediente = 'Renovable'`.

### Impacto en Sistema

#### Sin Cambios (Compatibilidad)
- `SOLICITUDES.TIPO_SOLICITUD_ID` sigue funcionando
- Tablas maestras actuales sin modificar
- Formularios actuales sin cambios
- Sin migraciones de BD

#### Futuro (Próximos PRs)
1. **PR Implementación BD:** Crear tabla `solicitudes_tipos`, migrar datos
2. **PR Modelos y Rutas:** SQLAlchemy models, endpoints gestión tipos múltiples
3. **PR Interfaz:** Formularios con selección múltiple, validaciones cliente/servidor
4. **PR Motor de Reglas:** Validaciones de secuencias, incompatibilidades, coherencia con tipo expediente

### Commits

1. `3d9030a` - [DOCS] Añadir documentación tabla SOLICITUDES_TIPOS (puente N:M)
2. `f540436` - [DOCS] Actualizar TIPOS_SOLICITUDES a arquitectura v3.0 (17 tipos individuales)
3. `a0e75f3` - [MERGE] Merge PR #19 `docs/fuentes-ia-desde-space` a `main`

### Testing

**Nota:** Al ser solo documentación, no requiere testing funcional. Testing futuro cuando se implemente en BD:

- [ ] Crear solicitud simple (AAP)
- [ ] Crear solicitud combinada (AAP + AAC)
- [ ] Crear solicitud triple (AAP + AAC + DUP)
- [ ] Validar incompatibilidades (AAE_PROVISIONAL + AAE_DEFINITIVA simultáneas)
- [ ] Validar secuencias (AAE_DEFINITIVA sin PROVISIONAL previa)
- [ ] Validar coherencia tipo expediente (RAIPEE en expediente no-renovable)
- [ ] Migrar datos v2.0 → v3.0 (tipos combinados → individuales)
- [ ] Estadísticas por tipo individual
- [ ] Consultas de combinaciones específicas

### Documentación Actualizada

- ✅ `docs/fuentesIA/datos_maestros.sql` - Datos iniciales tablas maestras
- ✅ `docs/fuentesIA/SOLICITUDES_TIPOS.md` - Tabla puente N:M completa
- ✅ `docs/fuentesIA/TIPOS_SOLICITUDES_v3.md` - Catálogo 17 tipos individuales
- ✅ `docs/CHANGELOG.md` - Esta entrada

### Referencias

- **Pull Request:** https://github.com/genete/bddat/pull/19
- **Marco Legal:**
  - LSE 24/2013: Ley del Sector Eléctrico
  - RDL 7/2025: División AAE provisional/definitiva
  - RD 1955/2000: Procedimiento autorizaciones eléctricas
  - RD 413/2014: Régimen económico renovables (RAIPEE)
  - RD 244/2019: Autoconsumo eléctrico (RADNE)
  - Ley 39/2015: Procedimiento Administrativo Común

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
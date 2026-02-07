# PATRONES UI - BDDAT

Documentación de los 3 patrones de vistas reutilizables para todo el sistema.

---

## 1. VISTA DASHBOARD

### Descripción
Panel de resumen con tarjetas de métricas, gráficos y listas de elementos destacados. Sin sidebar.

### Mockup

```
┌─────────────────────────────────────────────────────────────────┐
│ HEADER (top fijo)                                                │
│ Logo | Inicio > Dashboard           Carlos López | 🔔 | Salir   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  📊 PANEL DE CONTROL                                            │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ 📂 354       │  │ ⏳ 127       │  │ ✅ 103       │         │
│  │ Expedientes  │  │ En trámite   │  │ Finalizados  │         │
│  │ activos      │  │              │  │              │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                  │
│  ┌──────────────────────────────────────────────────┐          │
│  │ EXPEDIENTES RECIENTES                             │          │
│  │                                                    │          │
│  │  AT-2025-0123  │  Endesa SA      │  AAP  │  🟡   │          │
│  │  AT-2025-0124  │  Iberdrola SL   │  DUP  │  🟢   │          │
│  │  AT-2025-0125  │  Viesgo SA      │  AAP  │  🔴   │          │
│  │                                                    │          │
│  │  [Ver todos los expedientes →]                    │          │
│  └──────────────────────────────────────────────────┘          │
│                                                                  │
│  ┌─────────────────────────┐  ┌──────────────────────┐         │
│  │ TAREAS PENDIENTES (8)   │  │ GRÁFICO ESTADOS      │         │
│  │                         │  │                       │         │
│  │  • Revisar AAP-123 (2d)│  │    [Gráfico torta]   │         │
│  │  • Info pública DUP-045│  │                       │         │
│  │  • Subsanar AAP-098    │  │                       │         │
│  │                         │  │                       │         │
│  └─────────────────────────┘  └──────────────────────┘         │
│                                                                  │
└──────────────────────────────────────────────────────────────────┤
│ FOOTER (bottom fijo)                                             │
│ 📊 354 expedientes | 415 solicitudes | 103 finalizados          │
│ © 2026 BDDAT v0.3.2                                             │
└─────────────────────────────────────────────────────────────────┘
```

### Componentes principales
- Tarjetas de métricas (cards con números destacados)
- Lista de expedientes recientes (tabla resumida)
- Lista de tareas pendientes
- Gráfico de estados (torta o barras)
- Botones de acceso rápido

### Navegación
- Header con breadcrumb simple: `Inicio > Dashboard`
- Enlaces directos a vistas de listado completo
- Sin sidebar lateral

---

## 2. VISTA LISTADO SIN SIDEBAR

### Descripción
Tabla completa con filtros, búsqueda y paginación. Usada para buscadores, catálogos y listados generales.

### Mockup

```
┌─────────────────────────────────────────────────────────────────┐
│ HEADER (top fijo)                                                │
│ Logo | Inicio > Expedientes            Carlos López | 🔔 | Salir│
├─────────────────────────────────────────────────────────────────┤
│  BREADCRUMB                                                      │
│  Inicio > Expedientes                                           │
│  ────────────────────────────────────────────────────────────   │
│                                                                  │
│  📂 EXPEDIENTES                                    [+ Nuevo]    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────┐       │
│  │ 🔍 Buscar...        [Filtros ▼]  [Exportar CSV]    │       │
│  └─────────────────────────────────────────────────────┘       │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ N° Expte    │ Titular     │ Tipo │ Estado │ Acciones    │ │
│  ├───────────────────────────────────────────────────────────┤ │
│  │ AT-2025-123 │ Endesa SA   │ AAP  │ 🟡     │ [👁] [✏] [🗑]│ │
│  │ AT-2025-124 │ Iberdrola   │ DUP  │ 🟢     │ [👁] [✏] [🗑]│ │
│  │ AT-2025-125 │ Viesgo SA   │ AAP  │ 🔴     │ [👁] [✏] [🗑]│ │
│  │ ...                                                       │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                  │
│  Mostrando 1-25 de 354    [◀] [1] [2] [3] ... [15] [▶]        │
│                                                                  │
└──────────────────────────────────────────────────────────────────┤
│ FOOTER                                                           │
│ 📊 354 expedientes | 415 solicitudes | 103 finalizados          │
│ © 2026 BDDAT v0.3.2                                             │
└─────────────────────────────────────────────────────────────────┘
```

### Componentes principales
- Barra de búsqueda con input text
- Botones de filtros avanzados (dropdown)
- Tabla con columnas ordenables
- Botones de acción por fila (ver, editar, eliminar)
- Paginación con números de página
- Botón [+ Nuevo] para crear registro
- Opción de exportar datos

### Navegación
- Header con breadcrumb: `Inicio > [Sección]`
- Clic en fila → Vista detalle con sidebar (Vista 3)
- Botón [+ Nuevo] → Formulario modal o página completa
- Sin sidebar lateral

---

## 3. VISTA TRAMITACIÓN (CON SIDEBAR)

### Descripción
Vista de detalle con navegación jerárquica mediante sidebar acordeón. Usada para tramitación de expedientes y navegación por estructura anidada.

### Mockup

```
┌─────────────────────────────────────────────────────────────────┐
│ HEADER (top fijo)                                                │
│ Logo | Inicio > Tramitación > AT-123    Carlos López | 🔔 | Salir│
├────────┬────────────────────────────────────────────────────────┤
│SIDEBAR │  BREADCRUMB                                            │
│250px   │  Expedientes > AT-123 > Solicitud AAP                  │
│resize→ │  ────────────────────────────────────────────────────  │
│        │                                                         │
│Expte   │  SOLICITUD AAP - 15/01/2026                           │
│AT-123  │                                                         │
│        │  Tabs: [Datos] [Documentos] [Historial]              │
│Sol.    │                                                         │
│AAP ●   │  Solicitante: Endesa SA                               │
│├ Fase 1│  Tipo: AAP                                             │
│├ Fase 2│  Fecha presentación: 15/01/2026                       │
│└ Fase 3│  Estado: Completa                                      │
│        │                                                         │
│Sol.    │  ───────────────────────────────────────────────────  │
│DUP     │                                                         │
│        │  FASES (3)  [+ Nueva Fase]                            │
│Proyecto│                                                         │
│        │  1. Información Pública                               │
│        │     Estado: En curso (quedan 15 días)                 │
│        │     Inicio: 20/01/2026                                │
│        │     [Ver detalle ▶]                                    │
│        │                                                         │
│        │  2. Resolución                                         │
│        │     Estado: Pendiente                                  │
│        │     [Ver detalle ▶]                                    │
│        │                                                         │
│        │  3. Archivo                                            │
│        │     Estado: No iniciado                                │
│        │     [Ver detalle ▶]                                    │
│        │                                                         │
│        │  ───────────────────────────────────────────────────  │
│        │                                                         │
│        │  TRÁMITES (0)  [+ Crear Trámite]                      │
│        │  No hay trámites directos en esta solicitud.          │
│        │  Los trámites pertenecen a las fases.                 │
│        │                                                         │
│        │  ───────────────────────────────────────────────────  │
│        │                                                         │
│        │  DOCUMENTOS (5)  [+ Subir documento]                  │
│        │  - proyecto_tecnico.pdf (2.3 MB)                      │
│        │  - licencia_municipal.pdf (1.1 MB)                    │
│        │                                                         │
└────────┴─────────────────────────────────────────────────────────┤
│ FOOTER                                                           │
│ 📊 354 expedientes | 415 solicitudes | 103 finalizados          │
│ © 2026 BDDAT v0.3.2                                             │
└─────────────────────────────────────────────────────────────────┘
```

### Componentes principales

#### Sidebar acordeón:
- Lista plana (sin indentación tipo árbol)
- Elemento seleccionado marcado con ●
- Hijos directos del seleccionado visibles (con indentación visual)
- Ancestros visibles pero compactos
- Hermanos del seleccionado visibles
- Ancho redimensionable con divisor arrastrable (250px por defecto)
- Scrollbar horizontal automático si contenido excede ancho

#### Panel detalle:
- Breadcrumb para navegación rápida hacia ancestros
- Tabs: [Datos] [Documentos] [Historial]
- Paneles de hijos directos siempre visibles:
  - Con datos: listado + botón [+ Crear]
  - Sin datos: mensaje informativo + botón [+ Crear]
- NO se muestran paneles de nietos (ej: Tareas NO aparecen en Fase)

### Reglas de navegación

#### Sidebar acordeón:
1. **Solo el elemento seleccionado está expandido** (marcado con ●)
2. **Hijos directos** del seleccionado se listan debajo (con indentación visual leve)
3. **Ancestros** permanecen visibles en formato compacto
4. **Hermanos** del seleccionado permanecen visibles
5. **NO es árbol indentado**, es lista plana tipo acordeón
6. Al hacer clic en otro elemento:
   - Se cierra el anterior
   - Se abre el nuevo
   - Se actualizan hijos visibles

#### Panel detalle:
1. **Solo muestra paneles de hijos DIRECTOS** del elemento seleccionado
2. Ejemplo jerarquía:
   - Expediente → muestra Solicitudes
   - Solicitud → muestra Fases (NO Trámites)
   - Fase → muestra Trámites (NO Tareas)
   - Trámite → muestra Tareas
3. **Paneles siempre visibles** aunque estén vacíos (con opción [+ Crear])
4. **Breadcrumb** permite saltos hacia ancestros
5. **NO hay botón [⟲ Volver]** (navegación por breadcrumb o sidebar)

#### Ejemplo navegación:

**Estado inicial - Solicitud AAP seleccionada:**
```
Sidebar:
Expte AT-123
Sol. AAP ●          ← Seleccionado
├ Fase 1            ← Hijos visibles
├ Fase 2
└ Fase 3
Sol. DUP            ← Hermano
Proyecto

Panel detalle:
- Datos de Solicitud AAP
- Panel FASES (3) [+ Nueva Fase]
- Panel TRÁMITES (0) [+ Crear Trámite]  ← Vacío pero visible
- Panel DOCUMENTOS (5) [+ Subir]
```

**Usuario hace clic en "Fase 1 - Información Pública":**
```
Sidebar:
Expte AT-123
Sol. AAP
Fase Info. Pública ●  ← Nuevo seleccionado
├ Trámite 1           ← Nuevos hijos visibles
└ Trámite 2
Fase Resolución       ← Hermano
Fase Archivo          ← Hermano

Panel detalle:
- Datos de Fase Información Pública
- Panel TRÁMITES (2) [+ Nuevo Trámite]
- Panel DOCUMENTOS (3) [+ Subir]
- (NO aparece panel TAREAS porque no son hijos directos)
```

**Usuario hace clic en "Trámite 1":**
```
Sidebar:
Expte AT-123
Sol. AAP
Fase Info. Pública
Trámite 1 ●           ← Nuevo seleccionado
├ Tarea 1             ← Hijos visibles
├ Tarea 2
└ Tarea 3
Trámite 2             ← Hermano

Panel detalle:
- Datos de Trámite 1
- Panel TAREAS (3) [+ Nueva Tarea]  ← Ahora SÍ aparecen
- Panel DOCUMENTOS (2) [+ Subir]
```

### Redimensionamiento sidebar

- Ancho predeterminado: **250px**
- Divisor vertical arrastrable (⋮) entre sidebar y panel
- Usuario puede arrastrar para expandir/contraer
- Si contenido excede ancho → scrollbar horizontal automático
- Al expandir suficiente → scrollbar desaparece

---

## APLICACIÓN DE PATRONES

Estos 3 patrones son blueprints reutilizables para:

- **Dashboard:** Página principal, paneles de control por sección
- **Listado:** Buscadores (expedientes, solicitantes, documentos), catálogos (municipios, tipos)
- **Tramitación:** Navegación expedientes, solicitudes, fases, trámites, tareas

---

**Última actualización:** 7 de febrero de 2026  
**Versión:** 1.0  
**Issue relacionado:** #90
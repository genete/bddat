# PATRONES UI - BDDAT

Documentación de los 3 patrones de vistas reutilizables para todo el sistema.

---

## 1. VISTA DASHBOARD

### Descripción
Panel principal tras el login. Fichas simples de acceso a áreas funcionales del sistema. Sin sidebar. Cada ficha es una puerta de entrada a un área completa con su propia navegación.

### Mockup

```
┌─────────────────────────────────────────────────────────────────┐
│ HEADER (top fijo)                                                │
│ Logo BDDAT                           Carlos López | 🔔 | Salir│
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  📊 PANEL DE CONTROL - ¿Qué desea hacer?                        │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │                    │  │                    │                │
│  │   📂 TRAMITACIÓN   │  │   🛠 ADMINISTRACIÓN│                │
│  │                    │  │                    │                │
│  │   Expedientes      │  │   Usuarios         │                │
│  │   Solicitudes      │  │   Roles            │                │
│  │   Entidades        │  │   Configuración    │                │
│  │                    │  │                    │                │
│  │   [Entrar →]       │  │   [Entrar →]       │                │
│  │                    │  │                    │                │
│  └──────────────────┘  └──────────────────┘                │
│                                                                  │
│  ┌──────────────────┐                                         │
│  │                    │                                         │
│  │   ❓ AYUDA         │                                         │
│  │                    │                                         │
│  │   Documentación    │                                         │
│  │   Tutoriales       │                                         │
│  │   Soporte          │                                         │
│  │                    │                                         │
│  │   [Entrar →]       │                                         │
│  │                    │                                         │
│  └──────────────────┘                                         │
│                                                                  │
│  Estadísticas rápidas:                                           │
│  📊 354 expedientes | 415 solicitudes | 103 finalizados          │
│                                                                  │
└──────────────────────────────────────────────────────────────────┤
│ FOOTER (bottom fijo)                                             │
│ © 2026 BDDAT v0.3.2                                             │
└─────────────────────────────────────────────────────────────────┘
```

### Componentes principales

- **Fichas simples de acceso a áreas**
  - Tramitación: Expedientes, solicitudes, fases, trámites
  - Administración: Usuarios, roles, configuración
  - Ayuda: Documentación, tutoriales, soporte
- **Sin estadísticas complejas en las fichas** (propenso a errores y divergencias)
- **Estadísticas simples al pie** (visibles o a demanda)
- **Sin sidebar**

### Navegación
- Header con breadcrumb simple: `Dashboard`
- Clic en ficha → Entra al área correspondiente (Vista 2 o Vista 3)
- Sin duplicación de navegación
- Cada área gestiona su propia complejidad

---

## 2. VISTA LISTADO SIN SIDEBAR

### Descripción

Vista de gestión/listado a pantalla completa sin sidebar. Usada como punto de entrada a un área antes de acceder a la navegación jerárquica.

Ejemplo: Tras pulsar ficha "Tramitación" en dashboard → Aparece listado de expedientes (Vista 2) → Usuario elige expediente → Entra a vista con sidebar (Vista 3).

### Mockup

```
┌─────────────────────────────────────────────────────────────────┐
│ HEADER (top fijo)                                                │
│ Logo | Dashboard > Tramitación        Carlos López | 🔔 | Salir│
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  📂 GESTIÓN DE EXPEDIENTES                      [+ Nuevo]       │
│                                                                  │
│  ┌─────────────────────────────────────────────────────┐       │
│  │ 🔍 Buscar...        [Filtros ▼]  [Exportar CSV]    │       │
│  └─────────────────────────────────────────────────────┘       │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ N° AT   │ Titular  │ Sols │ Estado    │ Vencim. │ Acciones │ │
│  ├───────────────────────────────────────────────────────────┤ │
│  │ AT-123  │ Endesa   │ 2    │ En trám.  │ 14 días  │ Tramitar │ │
│  │ AT-124  │ Iberdrola│ 1    │ Resuelto  │ -       │ Ver      │ │
│  │ AT-125  │ Sin tit. │ 0    │ Incomp.   │ -       │ Subsanar │ │
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

- **Tabla informativa** con columnas calculadas:
  - Nº AT
  - Titular
  - Solicitudes (count)
  - Estado tramitación (lógica compleja)
  - Próximo vencimiento (MIN fecha límite)
  - Acciones (Tramitar / Ver / Subsanar)
- **Filtros**: Por titular, estado, vencimientos, solicitudes activas
- **Botón [Tramitar]**: Lleva a Vista 3 (Sidebar acordeón) con expediente seleccionado
- **Botón [+ Nuevo]**: Crea expediente nuevo
- **Sin sidebar lateral**

### Navegación
- Header con breadcrumb: `Dashboard > Tramitación`
- Clic en [Tramitar] → Vista 3 (Detalle expediente CON sidebar)
- Clic en breadcrumb → Vuelve a Dashboard
- Esta vista es el "lobby" antes de entrar a la navegación jerárquica

---

## 3. VISTA TRAMITACIÓN (CON SIDEBAR)

### Descripción

Vista de detalle con navegación jerárquica mediante sidebar acordeón. Usada para tramitación de UN expediente específico y navegación por estructura anidada (solicitudes > fases > trámites > tareas).

**Importante**: Esta vista es para UN expediente. Para cambiar de expediente, se vuelve a Vista 2 (Listado).

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
- **NO se muestran paneles de nietos** (ej: Tareas NO aparecen en Fase)

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

- **Dashboard:** Página principal tras login, acceso a áreas funcionales
- **Listado:** Punto de entrada a áreas (ej: Gestión Expedientes), antes de navegación jerárquica
- **Tramitación:** Navegación jerárquica dentro de UN expediente (solicitudes > fases > trámites > tareas)

### Flujo completo:

1. **Login** → Vista 0 (pantalla completa, sin chrome)
2. **Dashboard** (Vista 1) → Fichas de acceso a áreas
3. **Clic en ficha Tramitación** → Vista 2 (Listado expedientes SIN sidebar)
4. **Clic en [Tramitar] expediente** → Vista 3 (Detalle CON sidebar acordeón)
5. **Navegación jerárquica** dentro del expediente (Vista 3 actualiza sidebar/panel)
6. **Volver a listado** → Breadcrumb "Tramitación" (vuelve a Vista 2)

---

**Última actualización:** 7 de febrero de 2026  
**Versión:** 1.1  
**Issue relacionado:** #90
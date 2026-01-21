# Unificación de Tablas de Expedientes

## 🎯 Objetivo
Unificar la estructura y presentación de las tablas de expedientes en **Listado General** y **Mis Expedientes** para mantener consistencia visual y funcional.

## 📊 Estructura Unificada

### Columnas Comunes (ambas tablas)

1. **Número AT**
   - Formato: `AT-{numero_at}`
   - Estilo: Texto bold azul (primary)
   - Enlace a: Detalle del expediente
   - Siempre visible

2. **Proyecto**
   - Línea 1: **Título** (bold, truncado a 300px)
   - Línea 2: Finalidad (texto pequeño gris)
   - Tooltip: Título completo al hover
   - Siempre visible

3. **Tipo Expediente**
   - Badge azul info con nombre del tipo
   - Texto "Sin tipo" si no tiene
   - Responsive: `d-none d-md-table-cell`

4. **Instrumento Ambiental**
   - Badge verde con siglas del IA (AAU, AAUS, CA, etc.)
   - Guión "-" si no tiene
   - Responsive: `d-none d-lg-table-cell`

5. **Heredado**
   - Icono check amarillo si es heredado
   - Icono X gris si no lo es
   - Centrado
   - Responsive: `d-none d-xl-table-cell`

6. **Acciones**
   - Botón "Ver" (outline-primary, icono ojo)
   - Botón "Editar" (outline-secondary, icono lápiz)
   - Agrupados en btn-group
   - Siempre visible

### Columna Adicional (solo Listado General)

7. **Responsable** (SOLO en `/expedientes`)
   - Siglas del usuario responsable
   - Badge "Tú" azul si es el usuario actual
   - Tooltip: Nombre completo al hover
   - Responsive: `d-none d-xxl-table-cell`

---

## ⚖️ Diferencias Entre Tablas

| Característica | Listado General (`/expedientes`) | Mis Expedientes (`/mis_expedientes`) |
|------------------|----------------------------------|--------------------------------------|
| **Columna Responsable** | ✅ Sí (d-none d-xxl-table-cell) | ❌ No (redundante, todos son del usuario) |
| **Encabezado tabla** | `table-success` (verde) | `table-light` (gris claro) |
| **Colspan vacío** | `colspan="7"` | `colspan="6"` |
| **Footer** | Alert azul con total | Card-footer con total |

---

## 📝 Cambios Realizados

### 1. `app/templates/dashboard/mis_expedientes.html`
- ✅ **Añadida** columna "Instrumento Ambiental"
- ✅ **Cambiada** columna "Proyecto" para mostrar Finalidad (antes mostraba Emplazamiento)
- ✅ **Cambiada** columna "Heredado" de badge a icono check/X
- ✅ **Unificado** formato "Número AT" a `AT-{numero}`
- ✅ **Mantenida** responsive con breakpoints Bootstrap 5

### 2. `app/templates/expedientes/index.html`
- ✅ **Unificada** estructura de columnas con `mis_expedientes.html`
- ✅ **Añadida** columna "Instrumento Ambiental"
- ✅ **Cambiada** columna "Heredado" de badge a icono check/X
- ✅ **Mantenida** columna "Responsable" (exclusiva de esta vista)
- ✅ **Cambiados** botones de acciones a btn-group unificado
- ✅ **Ajustado** colspan de fila vacía a 7 (6 + Responsable)

---

## 📦 Archivos Modificados

```
app/templates/
├── dashboard/
│   └── mis_expedientes.html    [MODIFICADO]
└── expedientes/
    └── index.html              [MODIFICADO]
```

---

## 🔍 Testing Requerido

### Listado General (`/expedientes`)
- [ ] Columnas visibles según breakpoint responsive
- [ ] Columna "Responsable" visible solo en pantallas XXL
- [ ] Badge "Tú" aparece en expedientes propios
- [ ] Instrumento Ambiental muestra siglas correctas
- [ ] Icono check amarillo en heredados
- [ ] Enlaces y botones funcionan

### Mis Expedientes (`/mis_expedientes`)
- [ ] NO aparece columna "Responsable"
- [ ] Columnas responsive funcionan correctamente
- [ ] Instrumento Ambiental muestra siglas correctas
- [ ] Proyecto muestra Título + Finalidad
- [ ] Icono check amarillo en heredados
- [ ] Enlaces y botones funcionan

### Ambas Tablas
- [ ] Formato Número AT consistente: `AT-{numero}`
- [ ] Proyecto trunca título a 300px con tooltip
- [ ] Badges con colores consistentes
- [ ] Botones de acción agrupados y funcionales
- [ ] Responsive no rompe layout en móvil/tablet

---

## 💡 Notas de Implementación

### Breakpoints Bootstrap 5 usados:
- `d-none d-md-table-cell`: Tipo Expediente (≥768px)
- `d-none d-lg-table-cell`: Instrumento Ambiental (≥992px)
- `d-none d-xl-table-cell`: Heredado (≥1200px)
- `d-none d-xxl-table-cell`: Responsable (≥1400px)

### Acceso a relaciones:
- `expediente.proyecto.ia.siglas` requiere relación `ia` en modelo `Proyecto`
- Si no existe, mostrará `-` en columna IA

---

## ✅ Checklist de Merge

- [ ] Probado en desarrollo local
- [ ] Columnas responsive funcionan
- [ ] Instrumento Ambiental muestra datos correctos
- [ ] No hay errores en consola Flask
- [ ] Templates renderizan correctamente
- [ ] Listo para merge a `main`

---

**Fecha:** 21 de enero de 2026  
**Rama:** `feature/tabla-expedientes-unificada`  
**Base:** `main`  

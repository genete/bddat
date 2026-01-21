# Unificación y Mejora de Listado de Expedientes

## 🎯 Objetivo
Unificar **completamente** el listado de expedientes en una sola vista con filtrado opcional, eliminando duplicación de código y mejorando la experiencia de usuario.

## ✨ Mejoras Implementadas

### 1. 🔄 Unificación Total
- **Eliminado** template `dashboard/mis_expedientes.html` (duplicado)
- **Un solo listado** en `/expedientes` con parámetro opcional `?mis_expedientes=1`
- **Redirección** desde dashboard a listado con filtro
- **Lógica unificada** en `expedientes.index()`

### 2. 📊 Estadísticas en la Parte Superior
- **Movidas** al inicio, debajo del título
- Muestra: Siglas y nombre del usuario + Total de expedientes
- **Preparado** para futuras métricas (activos, heredados, por tipo, etc.)
- **No requiere scroll** para ver cuántos expedientes hay

### 3. 📝 Cabeceras Multilinea
- Usa `<br>` para columnas estrechas:
  - "Número AT" → "Número<br>AT"
  - "Tipo Expediente" → "Tipo<br>Expediente"
  - "Instrumento Ambiental" → "Instrumento<br>Ambiental"

### 4. ✂️ Elipsis en Textos Largos
- **Título proyecto:** max-width 250px con `text-truncate`
- **Finalidad:** max-width 250px con `text-truncate` en línea secundaria
- Tooltip muestra texto completo al hover

### 5. ✅ Columna Heredado Simplificada
- **Solo muestra** icono check verde cuando ES heredado
- **Celda vacía** cuando NO es heredado (más limpio)
- Color verde (`text-success`) alineado con colores oficiales JA

### 6. 🎨 Colores Unificados
- **Cabecera:** `table-success` (verde) en todas las vistas
- **Badges:** Consistentes (info, success)
- Eliminada confusión visual entre vistas

### 7. 👥 Columna Responsable Restaurada
- **Presente** en listado general
- **Responsive:** `d-none d-xxl-table-cell` (≥1400px)
- Badge "Tú" cuando es el usuario actual

---

## 🛣️ Arquitectura de Filtrado

### Rutas
```python
# Listado general (ADMIN/SUPERVISOR ven todos)
GET /expedientes/

# Listado filtrado (solo expedientes propios)
GET /expedientes/?mis_expedientes=1

# Redirección desde dashboard (compatibilidad)
GET /mis_expedientes  →  redirect to /expedientes/?mis_expedientes=1
```

### Lógica de Filtrado
```python
if TRAMITADOR:
    # Siempre ve solo sus expedientes
    expedientes = filter_by(responsable_id=current_user.id)
    vista_filtrada = True
else:  # ADMIN/SUPERVISOR
    if request.args.get('mis_expedientes') == '1':
        # Filtro opcional activado
        expedientes = filter_by(responsable_id=current_user.id)
        vista_filtrada = True
    else:
        # Vista completa del sistema
        expedientes = Expediente.query.all()
        vista_filtrada = False
```

---

## 📋 Estructura Final de Tabla

| Columna | Ancho | Responsive | Descripción |
|---------|-------|------------|-------------|
| **Número AT** | Auto | Siempre | `AT-{numero}` enlace azul |
| **Proyecto** | 250px | Siempre | Título bold + Finalidad gris (ambos con elipsis) |
| **Tipo Expediente** | Auto | ≥768px | Badge azul info |
| **Instrumento Ambiental** | Auto | ≥992px | Badge verde con siglas |
| **Heredado** | Auto | ≥1200px | Check verde solo si heredado |
| **Responsable** | Auto | ≥1400px | Siglas + badge "Tú" si aplica |
| **Acciones** | Auto | Siempre | Ver/Editar agrupados |

---

## 💾 Archivos Modificados

```
✅ MODIFICADOS:
app/routes/
├── expedientes.py          [Filtrado unificado con ?mis_expedientes=1]
└── dashboard.py            [Redirección a listado con filtro]

app/templates/
└── expedientes/
    └── index.html          [Template único mejorado]

app/models/
└── proyectos.py            [Relación ia agregada]

❌ ELIMINADOS:
app/templates/dashboard/
└── mis_expedientes.html    [Ya no necesario]
```

---

## ✅ Ventajas de Esta Arquitectura

1. ✅ **DRY:** Un solo template, una sola lógica
2. ✅ **Mantenibilidad:** Cambios en UN lugar afectan todas las vistas
3. ✅ **Consistencia:** UI/UX idéntica en filtrado y sin filtrar
4. ✅ **SEO-friendly:** URL semántica con query parameter
5. ✅ **Escalable:** Fácil agregar más filtros (por tipo, estado, etc.)
6. ✅ **Performance:** Una sola consulta SQL optimizada

---

## 🔍 Testing Requerido

### Como TRAMITADOR
- [ ] `/expedientes/` muestra solo mis expedientes
- [ ] Dashboard "Mis expedientes" funciona
- [ ] Estadísticas muestran mi nombre y total correcto
- [ ] NO veo columna Responsable (siempre soy yo)

### Como ADMIN/SUPERVISOR
- [ ] `/expedientes/` muestra TODOS los expedientes
- [ ] `/expedientes/?mis_expedientes=1` muestra solo míos
- [ ] Dashboard "Mis expedientes" redirige con filtro
- [ ] Columna Responsable visible en pantallas XXL
- [ ] Badge "Tú" aparece en expedientes propios

### Generales
- [ ] Título/Finalidad con elipsis a 250px
- [ ] Heredado: solo check verde cuando aplica
- [ ] Instrumento Ambiental muestra siglas correctas
- [ ] Cabeceras multilinea legibles
- [ ] Estadísticas arriba sin scroll
- [ ] Responsive funciona en móvil/tablet
- [ ] Colores consistentes (table-success)

---

## 💡 Futuras Mejoras Preparadas

El template tiene comentarios para expandir fácilmente:

```html
<!-- Futuras estadísticas: expedientes activos, heredados, por tipo, etc. -->
```

Posibles adiciones:
- Total heredados vs. nuevos
- Expedientes por tipo
- Expedientes activos/cerrados
- Últimos modificados
- Gráficos inline

---

**Fecha:** 21 de enero de 2026  
**Rama:** `feature/tabla-expedientes-unificada`  
**Commits:** 7 (incluye fix relación IA y refactor completo)  

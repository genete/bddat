# Mejoras UX en Módulo Expedientes

## 🎯 Objetivo
Corregir inconsistencias de interfaz y flujos de navegación en el módulo de expedientes.

---

## ✅ Correcciones Implementadas

### 1. 🏷️ Nomenclatura Consistente: "Instrumento Ambiental"

**Problema:**
- Label inconsistente "Tipo de Instalación de Alta Tensión" en formularios
- Confusión con concepto real: campo almacena **Instrumento Ambiental** (IA)

**Solución:**
- ✅ `nuevo.html`: Cambio de label a "Instrumento Ambiental"
- ✅ `editar.html`: Cambio de label a "Instrumento Ambiental"
- ✅ Placeholder actualizado: "-- Sin instrumento ambiental --"

**Archivos modificados:**
```
app/templates/expedientes/
├── nuevo.html   [L107: label, L109: placeholder]
└── editar.html  [L114: label, L116: placeholder]
```

---

### 2. 🎨 Alerta Instrumento Ambiental: Color Verde

**Problema:**
- Alert beige (`alert-warning`) con icono de advertencia
- Texto "Instalación de Alta Tensión" incorrecto
- Color amarillo no alineado con identidad JA

**Solución:**
- ✅ Cambio a `alert-success` (verde oficial Junta Andalucía)
- ✅ Icono `fa-leaf` (🍃 hoja) en vez de `fa-exclamation-triangle`
- ✅ Texto correcto: "Instrumento Ambiental:"

**Archivos modificados:**
```
app/templates/expedientes/
└── detalle.html  [L100-102: alert-success, fa-leaf, texto]
```

---

### 3. 🔄 Flujo de Navegación: Botón Cancelar

**Problema:**
- En `editar.html`: Cancelar redirecciona a `detalle` (vista intermedia innecesaria)
- Usuario espera volver al punto de partida (listado)

**Flujo anterior (incoherente):**
```
Listado → Editar → [Cancelar] → Detalle ❌
```

**Flujo corregido (coherente):**
```
Listado → Editar → [Cancelar] → Listado ✅
Listado → Detalle → Editar → [Cancelar] → Listado ✅
```

**Solución:**
- ✅ Cambio en botón Cancelar: `url_for('expedientes.detalle')` → `url_for('expedientes.index')`

**Archivos modificados:**
```
app/templates/expedientes/
└── editar.html  [L132: href a expedientes.index]
```

**Nota:** `nuevo.html` ya tenía el flujo correcto.

---

### 4. 🔘 Visualización Heredado: Switch Consistente

**Problema:**
- `detalle.html`: Badge amarillo "Heredado" en título (inconsistente)
- `editar.html`: Switch elegante y claro
- Diferencia visual confusa entre vistas

**Solución:**
- ✅ Eliminado badge del título en `detalle.html`
- ✅ Añadido switch deshabilitado en card "Información General"
- ✅ Estilo idéntico a `editar.html` (form-check-switch)

**Antes (detalle.html):**
```html
<h2>
    Expediente AT-1 
    <span class="badge bg-warning">Heredado</span> ❌
</h2>
```

**Después (detalle.html):**
```html
<div class="form-check form-switch">
    <input type="checkbox" checked disabled>
    <label>Expediente Heredado</label> ✅
</div>
```

**Archivos modificados:**
```
app/templates/expedientes/
└── detalle.html  [L11: eliminado badge, L60-68: switch añadido]
```

---

## 📊 Resumen de Cambios

| Cambio | Archivos | Líneas |
|--------|----------|--------|
| Nomenclatura IA | nuevo.html, editar.html | 4 |
| Alert verde IA | detalle.html | 3 |
| Flujo cancelar | editar.html | 1 |
| Switch heredado | detalle.html | 10 |
| **TOTAL** | **3 templates** | **18** |

---

## ✅ Ventajas

1. ✅ **Consistencia terminológica**: "Instrumento Ambiental" en todo el sistema
2. ✅ **Identidad visual**: Verde JA en vez de amarillo genérico
3. ✅ **Navegación intuitiva**: Cancelar vuelve al origen
4. ✅ **UI unificada**: Switch para "heredado" en todas las vistas
5. ✅ **Menos clics**: Usuario no pasa por vista detalle innecesariamente

---

## 🧪 Testing Checklist

### Crear Expediente
- [ ] Label dice "Instrumento Ambiental"
- [ ] Placeholder: "-- Sin instrumento ambiental --"
- [ ] Cancelar vuelve al listado
- [ ] Switch "Heredado" funciona

### Editar Expediente
- [ ] Label dice "Instrumento Ambiental"
- [ ] Placeholder: "-- Sin instrumento ambiental --"
- [ ] Cancelar vuelve al listado (no a detalle)
- [ ] Switch "Heredado" guarda correctamente

### Ver Expediente
- [ ] No hay badge amarillo en título
- [ ] Switch "Heredado" deshabilitado visible
- [ ] Alert IA es verde con icono hoja
- [ ] Texto dice "Instrumento Ambiental:"

### Flujos de Navegación
- [ ] Listado → Nuevo → Cancelar → Listado ✅
- [ ] Listado → Editar → Cancelar → Listado ✅
- [ ] Listado → Ver → Editar → Cancelar → Listado ✅
- [ ] Listado → Ver → Volver → Listado ✅

---

**Fecha:** 21 de enero de 2026  
**Rama:** `fix/expedientes-ux-improvements`  
**Commits:** 3  
**Issue:** Mejoras UX solicitadas por usuario  

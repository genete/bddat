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

### 2. 📝 Instrumento Ambiental: Campo Normal (No Alert)

**Problema:**
- En `detalle.html`: Mostrado como alert amarillo/verde destacado
- Debería ser un campo más del proyecto, no una advertencia

**Solución:**
- ✅ Eliminado `<div class="alert ...">`
- ✅ Añadido como campo estándar con `<h6>` + badge verde
- ✅ Mismo estilo que Finalidad, Emplazamiento, Descripción
- ✅ Badge verde con siglas + descripción en texto normal

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

**Archivos modificados:**
```
app/templates/expedientes/
└── detalle.html  [L100-112: campo normal con h6, badge, texto]
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

### 4. ✅ Visualización Heredado: Semántica del Listado

**Problema:**
- `detalle.html`: Mostraba switch deshabilitado (control de edición en vista de solo lectura)
- Inconsistente con semántica del listado: solo mostrar si aplica

**Solución:**
- ✅ **Solo si `heredado == True`**: Mostrar check verde + etiqueta
- ✅ **Si `heredado == False`**: No mostrar nada (no ocupar espacio innecesariamente)
- ✅ Mismo estilo que en tabla listado: `fa-check-circle text-success`

**Antes (incorrecto):**
```html
<!-- Siempre visible, incluso si no es heredado -->
<div class="form-check form-switch">
    <input type="checkbox" disabled>
    <label>Expediente Heredado</label> ❌
</div>
```

**Después (correcto):**
```html
{% if expediente.heredado %}
    <i class="fas fa-check-circle text-success"></i>
    <span class="text-muted small">Expediente Heredado</span> ✅
{% endif %}
```

**Archivos modificados:**
```
app/templates/expedientes/
└── detalle.html  [L60-65: check + label solo si heredado]
```

---

## 📊 Resumen de Cambios

| Cambio | Archivos | Líneas |
|--------|----------|--------|
| Nomenclatura IA | nuevo.html, editar.html | 4 |
| IA campo normal | detalle.html | 13 |
| Flujo cancelar | editar.html | 1 |
| Heredado semántico | detalle.html | 6 |
| **TOTAL** | **3 templates** | **24** |

---

## ✅ Ventajas

1. ✅ **Consistencia terminológica**: "Instrumento Ambiental" en todo el sistema
2. ✅ **Semántica clara**: IA como campo, no como alert de advertencia
3. ✅ **Navegación intuitiva**: Cancelar vuelve al origen
4. ✅ **UI coherente**: Heredado con misma lógica que listado (solo si aplica)
5. ✅ **Menos ruido visual**: No mostrar controles vacíos/innecesarios

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
- [ ] Campo "Instrumento Ambiental" como h6 + badge/texto
- [ ] No hay alert amarillo/verde
- [ ] **Heredado solo si aplica**: Check verde + etiqueta
- [ ] **No heredado**: No muestra nada (espacio limpio)

### Flujos de Navegación
- [ ] Listado → Nuevo → Cancelar → Listado ✅
- [ ] Listado → Editar → Cancelar → Listado ✅
- [ ] Listado → Ver → Editar → Cancelar → Listado ✅
- [ ] Listado → Ver → Volver → Listado ✅

---

**Fecha:** 21 de enero de 2026  
**Rama:** `fix/expedientes-ux-improvements`  
**Commits:** 5  
**Issue:** Mejoras UX solicitadas por usuario  

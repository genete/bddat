# Issue #94 - Estructura de Archivos

## Archivos Creados

### CSS v2 (sin tocar existentes)
- `app/static/css/v2-theme.css` - Variables, colores Junta Andalucía, tipografía ✅
- `app/static/css/v2-layout.css` - Grid principal, header, footer ✅
- `app/static/css/v2-components.css` - Tabla, badges, botones, filtros ✅

### JavaScript v2
- `app/static/js/v2-scroll-to-top.js` - Botón scroll to top funcional ✅
- `app/static/js/v2-scroll-infinito.js` - Carga automática al scrollear (pendiente)
- `app/static/js/v2-filtros.js` - Filtros mock (UI sin backend) (pendiente)

### Templates v2
- `app/templates/layout/base_full_width.html` - Layout base 100% ancho
- `app/templates/layout/_header.html` - Header reutilizable
- `app/templates/layout/_footer.html` - Footer reutilizable
- `app/templates/expedientes/listado_v2.html` - Vista listado prototipo

### Documentación
- `docs/CSS_v2_GUIA_USO.md` - Guía completa de uso CSS v2 ✅
- `docs/SCROLL_INFINITO.md` - Estrategias implementación scroll infinito ✅
- `docs/UI_PATTERNS_DATA_TABLE.md` - Patrones UI para tablas de datos ✅

## Estado Implementación

### ✅ Fase 1 - Completada (PR #95)
- [x] Estructura de archivos
- [x] CSS: Variables y tema (Tarea 2) - Colores Junta Andalucía
- [x] CSS: Layout grid (Tarea 3) - Header/main/footer responsive
- [x] CSS: Componentes (Tarea 4) - Tabla, badges, botones
- [x] Botón scroll-to-top funcional
- [x] Test HTML funcional (test_v2.html)
- [x] Documentación CSS v2

### ✅ Fase 1.5 - Estructura C.1/C.2/D (Refinamiento Layout)
- [x] Modificar `.app-main` a flexbox con `overflow: hidden`
- [x] Crear `.lista-cabecera` (C.1) - cabecera sin scroll
- [x] Crear `.lista-scroll-container` (C.2) - contenedor con scroll propio
- [x] Refactorizar test_v2.html con estructura C.1/C.2/D
- [x] Documentar patrón en CSS_v2_GUIA_USO.md
- [x] Actualizar SCROLL_INFINITO.md con prerequisitos

**Objetivo Fase 1.5:** Aislar el scroll del listado para evitar que arrastre a elementos hermanos (header, footer). Preparación para Vista 3 (árbol + detalle) y scroll infinito.

### 🚧 Fase 2 - Pendiente
- [ ] Templates completos (tareas 5-6)
- [ ] JavaScript scroll infinito (tarea 7)
- [ ] JavaScript filtros mock (tarea 8)
- [ ] Ruta Flask (tarea 9)
- [ ] Testing y validación (tarea 10)

## Colores Corporativos Aplicados

### Junta de Andalucía (Issue #58)

| Color | HEX | Variable | Uso |
|-------|-----|----------|-----|
| Verde corporativo | `#087021` | `--primary` | Navbar, botones principales, identidad |
| Verde hover | `#0b4c1a` | `--primary-hover` | Estados hover |
| Verde apoyo | `#c4ddca` | `--primary-light` | Fondos sutiles |
| Verde claro | `#f7fbf8` | `--primary-lighter` | Fondos muy claros |

### Semánticos

| Color | HEX | Variable | Uso |
|-------|-----|----------|-----|
| Success | `#198754` | `--success` | Resuelto, validación correcta |
| Warning | `#ffc107` | `--warning` | Advertencias, incompleto |
| Danger | `#dc3545` | `--danger` | Errores, vencido |
| Info | `#0dcaf0` | `--info` | En trámite, información |

### Grises Corporativos

| Color | HEX | Variable | Uso |
|-------|-----|----------|-----|
| Gris principal | `#111111` | `--gris-principal` | Texto principal, footer |
| Gris apoyo | `#bebebe` | `--gris-apoyo` | Texto deshabilitado |
| Gris contenedor | `#eeeeee` | `--gris-contenedor` | Fondos contenedores |
| Gris específico | `#f5f5f5` | `--gris-especifico` | Fondos muy claros |

## Efectos Visuales

- **Gradiente corporativo**: `linear-gradient(180deg, rgba(255,255,255,0.15), rgba(255,255,255,0))`
  - Aplicado a navbar y headers de tabla
  - Proporciona brillo sutil moderno

- **Sombras Bootstrap**: 
  - `--shadow-sm`: Sombra pequeña
  - `--shadow`: Sombra estándar
  - `--shadow-lg`: Sombra grande

- **Focus ring**: Verde corporativo con transparencia para accesibilidad

## Arquitectura de Layout (Fase 1.5)

### Estructura Jerárquica

```
A: app-container (grid header/main/footer)
├── B.1: app-header (sticky top)
├── B.2: app-main (flexbox vertical)
│   ├── C.1: lista-cabecera (sin scroll)
│   │   ├── page-header (título + botón)
│   │   └── filters-row (filtros + paginación)
│   └── C.2: lista-scroll-container (con overflow-y)
│       └── D: expedientes-table (crece verticalmente)
│           ├── thead (sticky respecto a C.2)
│           └── tbody
└── B.3: app-footer (sticky bottom)
```

### Ventajas de C.1/C.2/D

- ✅ Scroll aislado solo en C.2 (no afecta a B.1, B.3, ni C.1)
- ✅ Cabecera de tabla sticky funcional dentro de C.2
- ✅ Reutilizable en Vista 3 (árbol lateral + detalle)
- ✅ Preparado para scroll infinito (observar solo C.2)
- ✅ UX mejorada: filtros/título siempre visibles

## Próximos Pasos

1. ~~Implementar CSS completo (tareas 2-4)~~ ✅ COMPLETADO (Fase 1)
2. ~~Refinar estructura layout (C.1/C.2/D)~~ ✅ COMPLETADO (Fase 1.5)
3. Implementar templates completos (tarea 5-6) - Fase 2
4. Implementar JavaScript scroll infinito (tarea 7) - Fase 2
5. Implementar JavaScript filtros mock (tarea 8) - Fase 2
6. Añadir ruta Flask (tarea 9) - Fase 2
7. Testing y validación (tarea 10) - Fase 2

## Referencias

- [Issue #94](https://github.com/genete/bddat/issues/94) - Prototipo Vista Listado v2
- [Epic #93](https://github.com/genete/bddat/issues/93) - UI Modular
- [Issue #58](https://github.com/genete/bddat/issues/58) - Colores Junta Andalucía
- [Issue #90](https://github.com/genete/bddat/issues/90) - Especificación Patrones UI
- [PATRONES_UI.md](arquitectura/PATRONES_UI.md)
- [guia_colores_junta_andalucia.html](guia_colores_junta_andalucia.html)
- [CSS_v2_GUIA_USO.md](CSS_v2_GUIA_USO.md) - Guía completa CSS v2
- [SCROLL_INFINITO.md](SCROLL_INFINITO.md) - Estrategias scroll infinito

## Notas de Diseño

**Filtros en Columnas** (cambio respecto a diseño inicial):
- Filtro global (búsqueda texto) fuera de tabla
- Filtros por columna aparecen con hover en cabecera
- Icono mini 🔽 si filtro activo
- Cabecera limpia sin hover (salvo icono filtrado)

Comentar cambios en el issue cuando se llegue a esa implementación.

**Scroll Independiente (Fase 1.5)**:
- Problema resuelto: listado largo arrastraba scroll a todo B (header, footer)
- Solución: C.2 con `overflow-y: auto` contiene el scroll del listado
- Beneficio: reutilizable en cualquier contexto (Vista 3, modales, paneles)

## Convivencia No Destructiva

✅ Todos los archivos v2-* conviven con los existentes sin conflictos.
✅ CSS existente (`custom.css`) no se toca.
✅ Templates existentes no se modifican.
✅ Estrategia de migración progresiva.

## Historial de Cambios

**08/02/2026 - Fase 1.5:**
- Implementada estructura C.1/C.2/D para scroll independiente
- Refactorizado test_v2.html con nuevo layout
- Actualizada documentación CSS_v2_GUIA_USO.md
- Actualizado SCROLL_INFINITO.md con prerequisitos

**07/02/2026 - Fase 1 (PR #95):**
- Implementado CSS v2 modular completo
- Creados v2-theme.css, v2-layout.css, v2-components.css
- Botón scroll-to-top funcional
- Test HTML completo
- Documentación inicial

# Issue #94 - Estructura de Archivos

## Archivos Creados

### CSS v2 (sin tocar existentes)
- `app/static/css/v2-theme.css` - Variables, colores Junta Andalucía, tipografía ✅
- `app/static/css/v2-layout.css` - Grid principal, header, footer ✅
- `app/static/css/v2-components.css` - Tabla, badges, botones, filtros ✅

### JavaScript v2
- `app/static/js/v2-scroll-infinito.js` - Carga automática al scrollear (pendiente)
- `app/static/js/v2-filtros.js` - Filtros mock (UI sin backend) (pendiente)

### Templates v2
- `app/templates/layout/base_full_width.html` - Layout base 100% ancho
- `app/templates/layout/_header.html` - Header reutilizable
- `app/templates/layout/_footer.html` - Footer reutilizable
- `app/templates/expedientes/listado_v2.html` - Vista listado prototipo

## Estado Implementación

### ✅ Completado
- [x] Estructura de archivos
- [x] CSS: Variables y tema (Tarea 2) - Colores Junta Andalucía
- [x] CSS: Layout grid (Tarea 3) - Header/main/footer responsive
- [x] CSS: Componentes (Tarea 4) - Tabla, badges, botones

### 🚧 Pendiente
- [ ] Templates completos (tareas 5-6)
- [ ] JavaScript (tareas 7-8)
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

## Próximos Pasos

1. ~~Implementar CSS completo (tareas 2-4)~~ ✅ COMPLETADO
2. Implementar templates completos (tarea 5-6)
3. Implementar JavaScript (tareas 7-8)
4. Añadir ruta Flask (tarea 9)
5. Testing y validación (tarea 10)

## Referencias

- [Issue #94](https://github.com/genete/bddat/issues/94) - Prototipo Vista Listado v2
- [Epic #93](https://github.com/genete/bddat/issues/93) - UI Modular
- [Issue #58](https://github.com/genete/bddat/issues/58) - Colores Junta Andalucía
- [Issue #90](https://github.com/genete/bddat/issues/90) - Especificación Patrones UI
- [PATRONES_UI.md](arquitectura/PATRONES_UI.md)
- [guia_colores_junta_andalucia.html](guia_colores_junta_andalucia.html)

## Notas de Diseño

**Filtros en Columnas** (cambio respecto a diseño inicial):
- Filtro global (búsqueda texto) fuera de tabla
- Filtros por columna aparecen con hover en cabecera
- Icono mini 🔽 si filtro activo
- Cabecera limpia sin hover (salvo icono filtrado)

Comentar cambios en el issue cuando se llegue a esa implementación.

## Convivencia No Destructiva

✅ Todos los archivos v2-* conviven con los existentes sin conflictos.
✅ CSS existente (`custom.css`) no se toca.
✅ Templates existentes no se modifican.
✅ Estrategia de migración progresiva.

# Issue #94 - Estructura de Archivos

## Archivos Creados

### CSS v2 (sin tocar existentes)
- `static/css/v2-theme.css` - Variables, colores, tipografía
- `static/css/v2-layout.css` - Grid principal, header, footer
- `static/css/v2-components.css` - Tabla, badges, botones, filtros

### JavaScript v2
- `static/js/v2-scroll-infinito.js` - Carga automática al scrollear
- `static/js/v2-filtros.js` - Filtros mock (UI sin backend)

### Templates v2
- `templates/layout/base_full_width.html` - Layout base 100% ancho
- `templates/layout/_header.html` - Header reutilizable
- `templates/layout/_footer.html` - Footer reutilizable
- `templates/expedientes/listado_v2.html` - Vista listado prototipo

## Próximos Pasos

1. Implementar CSS completo (tareas 2-4 del issue)
2. Implementar templates completos (tarea 5-6)
3. Implementar JavaScript (tareas 7-8)
4. Añadir ruta Flask (tarea 9)
5. Testing y validación (tarea 10)

## Referencias

- [Issue #94](https://github.com/genete/bddat/issues/94)
- [Epic #93](https://github.com/genete/bddat/issues/93)
- [Especificación #90](https://github.com/genete/bddat/issues/90)
- [PATRONES_UI.md](../arquitectura/PATRONES_UI.md)

## Notas de Diseño

**Filtros en Columnas** (cambio respecto a diseño inicial):
- Filtro global (búsqueda texto) fuera de tabla
- Filtros por columna aparecen con hover en cabecera
- Icono mini 🔽 si filtro activo
- Cabecera limpia sin hover (salvo icono filtrado)

Comentar cambios en el issue cuando se llegue a esa implementación.

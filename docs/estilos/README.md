# Estilos y Diseño Visual

Guías de estilos CSS, sistema de diseño y recursos visuales del proyecto.

## 📘 Guía Principal

### GUIA_VISTAS_BOOTSTRAP.md (en raíz docs/)
**Referencia principal para Claude Code** - Decisiones de diseño CSS:
- Variables CSS v2 (colores, spacing)
- Arquitectura modular (theme, layout, components)
- Patrones reutilizables (.content-constrained, badges, botones)
- Responsive breakpoints y estrategias
- **Usar esta guía como referencia principal**

---

## Documentos Activos

### guia_colores_junta_andalucia.html
**Referencia visual interactiva** de colores corporativos:
- Paleta oficial Junta de Andalucía
- Ejemplos de uso (navbar, cards, botones)
- Tabla de referencia rápida
- Reglas de aplicación
- **Abrir en navegador para ver ejemplos visuales**

> **Tokens de color (ADR-022 / #533):** la paleta JdA **se mantiene** sin cambios.
> Lo que cambió es la consistencia: los grises hardcodeados del shell (`#ebebeb`,
> `#888`, `#666`, fallbacks sueltos…) se consolidaron sobre las variables de
> `v2-theme.css` (`--gris-*`, `--text-secondary`, `--border-color`, etc.). En CSS
> nuevo, usar siempre las variables, nunca hex sueltos.

---

## Recursos Relacionados

- [GUIA_VISTAS_BOOTSTRAP.md](../GUIA_VISTAS_BOOTSTRAP.md) - **Referencia principal de diseño y CSS**

---

**Volver a:** [🏠 Documentación principal](../README.md)
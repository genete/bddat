# Documentación BDDAT

Sistema de tramitación administrativa de expedientes de autorización de instalaciones de alta tensión en Andalucía.

---

## 📘 Guía Principal de Desarrollo UI

### [GUIA_VISTAS_BOOTSTRAP.md](GUIA_VISTAS_BOOTSTRAP.md)
**Referencia principal para Claude Code** - Decisiones de diseño UI no deducibles:
- Sistema de colores corporativos Junta de Andalucía
- Arquitectura de layout (niveles A/B/C)
- Vistas V0/V1/V2/V3: patrones, estructura, CSS crítico
- Scroll infinito, acordeones Bootstrap 5, responsive
- Errores comunes y checklist de implementación

**Usar esta guía como referencia principal para desarrollo de vistas.**

---

## Estructura de Documentación

### 📁 [setup/](setup/)
Guías de instalación y configuración inicial del proyecto.
- [Guía Completa: Configurar BDDAT en un PC Nuevo](setup/Guía%20Completa_%20Configurar%20BDDAT%20en%20un%20PC%20Nuevo.md)

### 🏗️ [arquitectura/](arquitectura/)
Documentos de diseño de alto nivel: arquitectura frontend, sistema de módulos.
- [FASE_3_FRONTEND_DINAMICO.md](arquitectura/FASE_3_FRONTEND_DINAMICO.md) - Sistema metadata-driven (futuro)
- **Histórico:** Patrones UI, sistema de vistas V0/V1/V2 (ver [arquitectura/README.md](arquitectura/README.md))

### 🎨 [estilos/](estilos/)
Guías de estilos CSS y recursos visuales.
- [guia_colores_junta_andalucia.html](estilos/guia_colores_junta_andalucia.html) - Paleta interactiva
- **Histórico:** CSS_v2_GUIA_USO.md (compactado en guía principal)

### 💻 [implementaciones/](implementaciones/)
Documentación técnica de implementaciones específicas.
- [VISTA_V3_TRAMITACION.md](implementaciones/VISTA_V3_TRAMITACION.md) - Vista tramitación con acordeón (en desarrollo)
- **Histórico:** Issue #94, scroll infinito, patrones tablas (ver [implementaciones/README.md](implementaciones/README.md))

### 🤖 [fuentesIA/](fuentesIA/)
Referencias y reglas para desarrollo asistido por IA.
- [REGLAS_DESARROLLO.md](fuentesIA/REGLAS_DESARROLLO.md)
- [GuiaGeneralNueva.md](fuentesIA/GuiaGeneralNueva.md)

---

## Enlaces Rápidos

### Desarrollo
- [📘 Guía Vistas Bootstrap](GUIA_VISTAS_BOOTSTRAP.md) - **Referencia principal UI**
- [Reglas de Desarrollo](fuentesIA/REGLAS_DESARROLLO.md)
- [Guía General del Proyecto](fuentesIA/GuiaGeneralNueva.md)

### Proyecto
- [Acceso Rápido](../ACCESO_RAPIDO_PROYECTO.md)
- [Repositorio en GitHub](https://github.com/genete/bddat)

---

## Cambios Recientes

### Febrero 2026
- ✅ **Nueva guía compactada:** [GUIA_VISTAS_BOOTSTRAP.md](GUIA_VISTAS_BOOTSTRAP.md) - Referencia principal para Claude Code
- ✅ **Reorganización:** Documentos detallados movidos a carpetas `historico/` (siguen disponibles como referencia)
- ✅ **Vista V3:** Cambio arquitectónico de sidebar → acordeón Bootstrap 5 (12/02/2026)
- ✅ **Vistas completadas:** V0 (Login), V1 (Dashboard), V2 (Listado scroll infinito)

---

**Stack:** PostgreSQL + Flask (SQLAlchemy) + Bootstrap 5  
**Rama de desarrollo:** `develop`  
**Última actualización:** 16 de febrero de 2026
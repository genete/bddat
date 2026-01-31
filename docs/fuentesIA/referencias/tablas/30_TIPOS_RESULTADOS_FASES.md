<!--
Tabla: TIPOS_RESULTADOS_FASES
Generado automáticamente por: scripts/split_tables.py
Fecha de generación: 31/01/2026 21:04
IMPORTANTE: No editar Tablas.md directamente.
            Editar este archivo y ejecutar merge_tables.py para regenerar.
-->

### TIPOS_RESULTADOS_FASES

Catálogo de resultados posibles de fases.

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ID** | INTEGER | Identificador único del tipo de resultado | NO | PK, autoincremental |
| **CODIGO** | VARCHAR(50) | Código del resultado | NO | FAVORABLE, DESFAVORABLE, CONDICIONADO, SIN_PRONUNCIAMIENTO, etc. |
| **NOMBRE** | VARCHAR(200) | Denominación del resultado | NO | Descripción legible |

#### Claves

- **PK:** `ID`
- **UNIQUE:** `CODIGO`

#### Índices Recomendados

- `CODIGO` (búsqueda rápida)

#### Notas de Versión

- **v3.0:** Sin cambios estructurales.

#### Filosofía

Tabla maestra que define los posibles resultados de las fases:

- Determina si la fase tuvo éxito procedimental
- Condiciona las fases siguientes según reglas de negocio
- El técnico debe evaluar manualmente el resultado tras analizar documentos

#### Relación con Otras Tablas

Usado en:
- `FASES.RESULTADO_FASE_ID` (resultado de la fase)

---

## Resumen Final

**Tablas Operacionales:** 9  
**Tablas Maestras:** 9  
**Total:** 18 tablas

### Principios v3.0

1. **Minimalismo estructural:** Tablas con campos mínimos, semántica en tipos
2. **Documento agnóstico:** Solo `EXPEDIENTE_ID` como FK
3. **Relaciones unidireccionales:** TAREA → DOCUMENTO (no al revés)
4. **Estados deducibles:** No almacenar lo que se puede calcular
5. **Fechas administrativas:** Fechas con efectos legales, no técnicas
6. **Fuente de verdad única:** No duplicar información
7. **Configurabilidad:** Lógica de negocio en motor de reglas, no hardcoded

---

**Versión:** 3.0  
**Fecha:** 30 de diciembre de 2025  
**Proyecto:** BDDAT - Sistema de Tramitación de Expedientes de Alta Tensión

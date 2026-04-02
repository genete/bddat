# NORMATIVA — Legislación aplicable al motor de reglas BDDAT

> **Fuente:** Legislación estatal y autonómica sobre instalaciones de alta tensión en Andalucía.
> **Aplica a:** Motor de reglas — base legal de las reglas de tramitación ESFTT.
> **Estado:** Catálogo de normas y estructura de extracción definida. Iteraciones de investigación pendientes.

---

## 1. Contexto del sistema BDDAT

La tramitación de cada expediente sigue la jerarquía ESFTT:

```
EXPEDIENTE (proyecto de instalación eléctrica)
  └── SOLICITUD (qué se pide: AAP, AAC, APO, utilidad pública...)
        └── FASE (etapas procedimentales: análisis, info pública, consultas, resolución...)
              └── TRÁMITE (acciones concretas dentro de la fase)
                    └── TAREA (unidad de trabajo: redactar, firmar, notificar, publicar, esperar plazo)
```

**Tipos de instalaciones de alta tensión:**
- Líneas eléctricas aéreas y subterráneas
- Subestaciones y centros de transformación
- Instalaciones de generación (renovable y convencional)
- Elementos de conexión y seccionamiento

**Tipos de solicitud:** AAP, AAC, APO, DUP, Modificación, Desistimiento/Renuncia
(Ver `docs/NORMATIVA_SOLICITUDES.md` para detalle y combinaciones.)

---

## 2. Legislación base

### Nacional
- **RD 1955/2000**, de 1 de diciembre — Regula actividades de transporte, distribución,
  comercialización, suministro y procedimientos de autorización de instalaciones de energía
  eléctrica. **Norma procedimental principal.**
- **Ley 24/2013**, de 26 de diciembre — Ley del Sector Eléctrico. Marco legal de referencia.
- **Ley 39/2015**, de 1 de octubre — Procedimiento Administrativo Común. Plazos,
  notificaciones, silencio administrativo. → Ver `docs/NORMATIVA_PLAZOS.md` para detalle de arts. 21-25, 29-32 y 112-126.
- **Ley 40/2015** — Régimen Jurídico del Sector Público (procedimiento interadministrativo).
- **RD 842/2002** — Reglamento Electrotécnico de Baja Tensión (referencia técnica complementaria).
- **Ley 21/2013** — Evaluación de Impacto Ambiental (EIA). Afecta a fases de consultas y
  pronunciamiento ambiental.

### Autonómica Andalucía
- **Decreto 9/2011**, de 18 de enero (BOJA nº 22) — Medidas para la agilización de trámites
  administrativos. Contiene excepciones relevantes al procedimiento estándar.
- **Ley 2/2007**, de 27 de marzo — Fomento de las Energías Renovables y del Ahorro y Eficiencia
  Energética de Andalucía.
- **Decreto 369/2010** y normas de desarrollo autonómico aplicables.
- **Decreto-ley 26/2021**, de 14 de diciembre — Simplificación administrativa. Incluye la
  Disposición Final Cuarta sobre exención de información pública para instalaciones sin DUP
  y sin AAU (ver DISEÑO_MOTOR_REGLAS.md, regla INICIAR INFORMACION_PUBLICA).

---

## 3. Qué extraer por tipo de solicitud

Para cada tipo de solicitud (AAP, AAC, APO, DUP...):
- Fases obligatorias y su orden
- Fases opcionales o condicionales
- Plazos legales aplicables (días hábiles o naturales)
- Puntos de silencio administrativo positivo/negativo
- Organismos de consulta obligatoria

### Variables que modifican las reglas estándar
- Tensión de la instalación (< 30 kV, 30-132 kV, > 132 kV)
- Tipo de instalación (aérea, subterránea, mixta)
- Clasificación del suelo afectado
- Longitud o potencia (umbrales de cambio de procedimiento)
- Tipo de promotor (distribuidora, generador, consumidor directo)
- Necesidad de EIA: cuándo es obligatoria
- Afectación a espacios protegidos (Red Natura 2000, ZEPA, LIC)
- Instalaciones de generación renovable (régimen especial)

### Excepciones y regímenes especiales
- Instalaciones exentas de alguna fase (DA1ª del Decreto 9/2011)
- Procedimientos abreviados o simplificados
- Régimen especial para generación renovable
- Instalaciones de uso privado vs. uso público
- Pequeñas instalaciones bajo umbrales de simplificación

---

## 4. Formato de documentación de reglas

Para cada regla identificada, documentar:

| Campo | Contenido |
|-------|-----------|
| ID_regla | Identificador único (ej: R-AAP-01) |
| Descripción | Qué dice la regla en lenguaje natural |
| Tipo_solicitud | A qué tipo de solicitud aplica |
| Fase_afectada | Qué fase(s) afecta |
| Condición_activación | Cuándo aplica (siempre / si tensión > X / si suelo urbano...) |
| Excepción_de | Si es excepción, a qué regla estándar contradice |
| Fuente_legal | Norma, artículo y apartado |
| Notas | Observaciones de interpretación |

---

## 5. Resultados por iteración

*(Se completarán en sesiones de trabajo dedicadas — ver issue #250 para planificación)*

### Iteración 1 — Mapa de alto nivel
Para cada tipo de solicitud estándar (AAP, AAC, APO, DUP):
qué fases son obligatorias según RD 1955/2000 y cuáles son los plazos.

### Iteración 2 — Excepciones y regímenes especiales
Generación renovable, instalaciones < 30 kV.

### Iteración 3 — Plazos y silencio administrativo
→ En curso. Ver `docs/NORMATIVA_PLAZOS.md` para extracción detallada por norma.
- §1 LPACAP 39/2015 — completo (sesión 2026-04-01)
- §2.1 LSE 24/2013 — completo (sesión 2026-04-02)
- §2.2 RD 1955/2000 — completo (sesión 2026-04-02)

### Iteración 4 — Casos límite y casuística especial

---

## 6. Fuentes normativas por ámbito — Junta de Andalucía

Páginas de referencia de la Consejería de Industria, Energía y Minas:

| Ámbito | URL |
|---|---|
| Energía eléctrica (distribución y transporte) | https://www.juntadeandalucia.es/organismos/industriaenergiayminas/areas/energia/electricidad.html |
| Energías renovables | https://www.juntadeandalucia.es/organismos/industriaenergiayminas/areas/energia/renovables.html |

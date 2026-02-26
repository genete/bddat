# Investigación legislativa — Motor de Reglas BDDAT

> **Propósito:** Documento de trabajo para sistematizar la legislación aplicable
> a la tramitación de expedientes de instalaciones de alta tensión en Andalucía.
> Resultado esperado: catálogo de reglas de tramitación y sus excepciones,
> estructurado según la semántica de BDDAT, listo para diseñar el motor de reglas.
>
> **Uso:** Este documento se da como contexto a Perplexity Pro para investigación
> profunda por iteraciones. Los resultados de cada iteración se incorporan aquí
> y se revisan antes de continuar.

---

## 1. Contexto del sistema BDDAT

BDDAT es una aplicación de gestión de expedientes de autorización de instalaciones
de alta tensión para la Consejería de Industria, Energía y Minas de la Junta de
Andalucía.

La tramitación de cada expediente sigue una estructura jerárquica:

```
EXPEDIENTE (un proyecto de instalación eléctrica)
  └── SOLICITUD (qué se pide: AAP, AAC, APO, utilidad pública...)
        └── FASE (etapas procedimentales: análisis, info pública, consultas, resolución...)
              └── TRÁMITE (acciones concretas dentro de la fase)
                    └── TAREA (unidad de trabajo: redactar, firmar, notificar, publicar, esperar plazo)
```

**Tipos de instalaciones de alta tensión:**
- Líneas eléctricas aéreas
- Líneas eléctricas subterráneas
- Subestaciones de transformación
- Centros de transformación (CT)
- Instalaciones de generación (renovable y convencional)
- Elementos de conexión y seccionamiento

**Tipos de solicitud (TipoSolicitud):**
- AAP — Autorización Administrativa Previa
- AAC — Autorización Administrativa de Construcción
- APO — Autorización de Puesta en Operación (o Funcionamiento)
- DUP — Declaración de Utilidad Pública
- Modificación de instalación autorizada
- Desistimiento / Renuncia

---

## 2. Legislación base a estudiar

### Nacional
- **RD 1955/2000**, de 1 de diciembre — Regula actividades de transporte, distribución,
  comercialización, suministro y procedimientos de autorización de instalaciones de energía
  eléctrica. **Norma procedimental principal.**
- **Ley 24/2013**, de 26 de diciembre — Ley del Sector Eléctrico. Marco legal de referencia.
- **Ley 39/2015**, de 1 de octubre — Procedimiento Administrativo Común. Regula plazos,
  notificaciones, silencio administrativo, etc.
- **Ley 40/2015** — Régimen Jurídico del Sector Público (procedimiento interadministrativo).
- **RD 842/2002** — Reglamento Electrotécnico de Baja Tensión (referencia técnica complementaria).
- **Ley 21/2013** — Evaluación de Impacto Ambiental (EIA). Afecta a fases de consultas y
  pronunciamiento ambiental.

### Autonómica Andalucía
- **Decreto 9/2011**, de 18 de enero (BOJA nº 22) — Medidas para la agilización de trámites
  administrativos. **Contiene excepciones relevantes al procedimiento estándar.**
- **Ley 2/2007**, de 27 de marzo — Fomento de las Energías Renovables y del Ahorro y Eficiencia
  Energética de Andalucía.
- **Decreto 369/2010** u otras normas de desarrollo autonómico aplicables.
- Órdenes de la Consejería sobre procedimiento (si existen).

---

## 3. Qué necesitamos extraer

### 3.1 Reglas estándar de tramitación
Para cada tipo de solicitud (AAP, AAC, APO, DUP...):
- ¿Qué fases son obligatorias y en qué orden?
- ¿Hay fases opcionales o condicionales?
- ¿Qué plazos legales aplican (días hábiles o naturales)?
- ¿En qué punto hay silencio administrativo positivo/negativo?
- ¿Qué organismos deben ser consultados obligatoriamente?

### 3.2 Condiciones que modifican las reglas estándar
Variables que pueden alterar el procedimiento aplicable:
- Tensión de la instalación (< 30 kV, entre 30-132 kV, > 132 kV)
- Tipo de instalación (aérea, subterránea, mixta)
- Clasificación del suelo afectado (urbano, urbanizable, no urbanizable)
- Longitud o potencia (umbrales que cambian el procedimiento)
- Tipo de promotor (empresa distribuidora, generador, consumidor directo...)
- Necesidad de EIA (evaluación de impacto ambiental): ¿cuándo es obligatoria?
- Afectación a espacios protegidos (Red Natura 2000, ZEPA, LIC...)
- Instalaciones de generación renovable (régimen especial)

### 3.3 Excepciones y regímenes especiales
- Instalaciones que quedan exentas de alguna fase (como la DA1ª del Decreto 9/2011)
- Procedimientos abreviados o simplificados
- Régimen especial para generación renovable
- Instalaciones de uso privado vs. uso público
- Pequeñas instalaciones bajo umbrales de simplificación

### 3.4 Plazos legales
- Plazo máximo de resolución por tipo de solicitud
- Plazos de información pública (días mínimos de exposición)
- Plazos de consulta a organismos
- Efectos del silencio administrativo por tipo de solicitud
- Suspensión de plazos: cuándo y cómo

---

## 4. Formato de salida esperado

Para cada regla identificada, documentar en formato tabla:

| Campo | Contenido |
|-------|-----------|
| ID_regla | Identificador único (ej: R-AAP-01) |
| Descripción | Qué dice la regla en lenguaje natural |
| Tipo_solicitud | A qué tipo de solicitud aplica |
| Fase_afectada | Qué fase(s) afecta |
| Condición_activación | Condiciones bajo las que aplica (siempre / si tensión > X / si suelo urbano...) |
| Excepción_de | Si es excepción, a qué regla estándar contradice |
| Fuente_legal | Norma, artículo y apartado |
| Notas | Observaciones de interpretación |

---

## 5. Iteraciones previstas

**Iteración 1 (primera sesión):**
Mapa de alto nivel: para cada tipo de solicitud estándar (AAP, AAC, APO, DUP),
¿cuáles son las fases obligatorias según RD 1955/2000 y cuáles son los plazos?
Resultado: tabla resumen + lista de excepciones identificadas para profundizar.

**Iteración 2:**
Profundizar en las excepciones y regímenes especiales identificados en la iteración 1.
Especialmente: generación renovable, instalaciones < 30 kV, Decreto 9/2011.

**Iteración 3:**
Plazos legales detallados y silencio administrativo.

**Iteración 4 (si necesaria):**
Casos límite y casuística especial no cubierta en iteraciones anteriores.

---

## 6. Resultados por iteración

*(Se irán completando aquí tras cada sesión con Perplexity)*

### Iteración 1 — pendiente

### Iteración 2 — pendiente

### Iteración 3 — pendiente

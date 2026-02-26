# Plan de investigación con Perplexity — Motor de Reglas BDDAT

> **Estado:** Pendiente de retomar. Sesión anterior cerrada por reorientación de estrategia.
> **Objetivo:** Obtener un catálogo exhaustivo de legislación y reglas procedimentales
> para diseñar el motor de reglas de tramitación de expedientes AT en Andalucía.

---

## Lección aprendida de la sesión anterior

Los prompts iniciales fueron demasiado dirigidos: le indicamos tipos de instalación,
tipos de solicitud y legislación concreta. Perplexity se limitó a buscar lo que le
dijimos y no exploró por su cuenta. Resultado: se perdió legislación relevante
(renovables, RAIPEE, RADNE, decretos de simplificación, acceso y conexión).

**Principio para la próxima sesión:** prompt inicial abierto, sin acotar legislación
ni tipos. Que Perplexity descubra el mapa completo desde cero. Solo darle contexto
de quiénes somos y qué tramitamos.

---

## Contexto a dar a Perplexity (siempre)

Somos un servicio de la Consejería de Industria, Energía y Minas de la Junta de
Andalucía. Tramitamos **expedientes de autorización de instalaciones eléctricas
de alta tensión de competencia autonómica** (potencia ≤50 MW, tensión <220 kV).
Estamos construyendo un sistema informático para gestionar esa tramitación y
necesitamos un mapa exhaustivo de toda la legislación aplicable y todas las
variantes procedimentales posibles.

---

## Estrategia de sesión — 4 fases con paradas

### Fase 1 — Mapa legislativo libre (sin acotar)

**Prompt de arranque:**

> Eres un experto en derecho administrativo y legislación del sector eléctrico español.
> [CONTEXTO ARRIBA]
>
> TAREA: Sin que yo te indique ninguna norma concreta, elabora por ti mismo el mapa
> completo de legislación que puede afectar a la tramitación de estos expedientes.
> Incluye normativa estatal y autonómica andaluza. Considera todas las dimensiones:
> procedimiento de autorización, evaluación ambiental, ordenación del territorio,
> acceso y conexión a red, registros administrativos de instalaciones, régimen
> económico, simplificación administrativa, y cualquier otra que identifiques.
>
> No me des el contenido de las normas todavía. Solo el inventario: qué normas
> existen, para qué sirven, y si tienen relación entre sí (derogan, complementan,
> excepcionan a otras).
>
> Al terminar, presenta el inventario en formato tabla descargable (Markdown) y
> espera mi confirmación antes de continuar.

**Señal de parada:** cuando presente la tabla con el inventario legislativo.
**Revisión aquí (Claude Code):** verificar si faltan normas conocidas del servicio.

---

### Fase 2 — Tipos de procedimiento que genera esa legislación

Con el inventario validado, preguntar:

> Usando el inventario anterior, identifica todos los tipos de autorización,
> inscripción, comunicación o resolución administrativa que puede necesitar
> tramitar un expediente de instalación eléctrica AT de competencia autonómica
> en Andalucía. No asumas que son solo los del RD 1955/2000 — busca también
> los que impone normativa de renovables, autoconsumo, registros, acceso a red,
> simplificación, etc.
>
> Para cada tipo: nombre oficial, norma que lo establece, y si es independiente
> o se combina habitualmente con otros tipos en el mismo expediente.
>
> Formato tabla Markdown descargable. Espera confirmación.

**Señal de parada:** tabla de tipos de autorización/inscripción.
**Revisión aquí:** comparar con `tipos_solicitudes` de la BD para detectar gaps.

---

### Fase 3 — Variables que diferencian procedimientos

> Con los tipos identificados, determina qué variables técnicas, territoriales
> o jurídicas hacen que el procedimiento de un expediente sea diferente al de otro.
> Por ejemplo: tipo de tecnología, nivel de tensión, tipo de suelo, necesidad de
> evaluación ambiental, potencia, etc.
>
> Para cada variable: nombre, valores posibles, qué aspecto del procedimiento
> modifica y norma que lo establece.
>
> Incluye también las excepciones y simplificaciones procedimentales conocidas
> (decretos de simplificación, excepciones a información pública, etc.).
>
> Formato tabla Markdown descargable. Espera confirmación.

**Señal de parada:** tabla de variables diferenciadores.
**Revisión aquí:** estas variables son los campos del modelo de datos del motor de reglas.

---

### Fase 4 — Reglas de secuencia y plazos (JSON)

Solo cuando las tres fases anteriores estén validadas.

> Con todo lo anterior, extrae las reglas de secuencia procedimental:
> qué debe completarse antes que qué, qué requisitos debe cumplir cada
> paso, y qué plazos legales aplican.
>
> [Usar el schema JSON definido en MOTOR_REGLAS_prompts_perplexity.md]

---

## Notas para la próxima sesión

- Usar **investigación profunda** en Perplexity (no elegir modelo manualmente)
- No dar lista de legislación al inicio — que la descubra él
- No dar nombres de tipos de solicitud de BDDAT — que los descubra él
- Parar tras cada fase y revisar aquí antes de continuar
- Guardar cada entrega en `docs/fuentesIA/referencias/` y commitear
- La BD (`tipos_solicitudes`) es referencia de contraste, no de input a Perplexity

## Archivos de sesión anterior (referencia, no borrar)

- `referencias/Clasificacion AT Andalucia.md` — Capa 0 sesión anterior
- `referencias/Clasificacion AT Capa2.md` — Capa 0 sesión anterior (continuación)
- `MOTOR_REGLAS_prompts_perplexity.md` — prompts originales (schema JSON Fase 4 sigue siendo válido)
- `MOTOR_REGLAS_investigacion_legislativa.md` — contexto de trabajo original

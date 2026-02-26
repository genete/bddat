# Prompts para Perplexity Pro — Investigación legislativa motor de reglas

> Ejecutar en orden. Cada capa usa la anterior como input.
> Modelo recomendado: Gemini 2.0 Pro (contexto 1M, buena indexación fuentes españolas).
> Formato de salida: Markdown descargable para capas 0-2, JSON descargable para capa 3.

---

## CAPA 0 — Descubrimiento de tipologías

### Prompt

```
Soy desarrollador de software. Estoy construyendo un sistema informático para
gestionar la tramitación de expedientes de autorización de instalaciones
eléctricas de alta tensión en España (competencia de comunidades autónomas,
en este caso Andalucía). Necesito identificar, desde la legislación, todos
los tipos de instalaciones, expedientes y solicitudes posibles.

TAREA: A partir del RD 1955/2000, la Ley 24/2013 del Sector Eléctrico, y
cualquier normativa de desarrollo que identifiques (nacional y autonómica
andaluza), elabora una clasificación exhaustiva de:

1. TIPOS DE INSTALACIÓN eléctrica de alta tensión sujetas a autorización
   administrativa en Andalucía. Por ejemplo: línea aérea, línea subterránea,
   subestación, centro de transformación, instalación de generación...
   Para cada tipo, indica si tiene subtipos relevantes desde el punto de
   vista del procedimiento (ej: generación fotovoltaica vs eólica vs
   almacenamiento vs hibridación vs cogeneración).

2. TIPOS DE SOLICITUD/AUTORIZACIÓN posibles sobre esas instalaciones.
   Por ejemplo: autorización administrativa previa, de construcción, de
   puesta en operación, declaración de utilidad pública, modificación,
   legalización, desistimiento... Indica cuáles pueden o deben combinarse.

3. VARIABLES TÉCNICAS O TERRITORIALES que la legislación usa para
   diferenciar procedimientos. Por ejemplo: nivel de tensión, potencia,
   longitud, tipo de suelo, evaluación de impacto ambiental obligatoria,
   afección a espacios protegidos, régimen económico (mercado libre /
   régimen especial / autoconsumo).

No asumas que conozco la legislación. Descúbrela tú y justifica cada
tipología con la norma y artículo que la sustenta.

FORMATO DE SALIDA:
Genera un fichero de texto en formato Markdown con tres secciones:
- Sección 1: Árbol de tipos de instalación con subtipos
- Sección 2: Lista de tipos de solicitud/autorización con descripción breve
- Sección 3: Tabla de variables diferenciadores de procedimiento

Al terminar, presenta un resumen de 5 líneas y espera mi confirmación
antes de continuar con la siguiente capa. No continúes sin confirmación.
```

---

## CAPA 1 — Inventario legislativo

### Instrucciones previas
Adjuntar o referenciar el fichero Markdown generado en la Capa 0.

### Prompt

```
Usando el árbol de tipologías que has elaborado (adjunto), necesito ahora
el inventario completo de legislación aplicable.

TAREA: Para cada tipo de instalación y tipo de solicitud identificados,
elabora el inventario de todas las normas jurídicas aplicables, directa
o indirectamente, al procedimiento de autorización. Incluye:

- Normativa de procedimiento general (autorizaciones, plazos, notificaciones)
- Normativa sectorial eléctrica (procedimientos específicos)
- Normativa ambiental (cuándo aplica EIA, DIA, consultas ambientales)
- Normativa de ordenación del territorio y urbanismo (en qué afecta al
  procedimiento)
- Normativa específica de generación renovable (si aplica al tipo)
- Normativa autonómica andaluza que modifique, complemente o excepcione
  la normativa estatal

Para cada norma indica:
- Identificación completa (tipo, número, fecha, título oficial)
- Ámbito: qué tipos de instalación/solicitud afecta
- Relación con otras normas (complementa / excepciona / deroga parcialmente)
- Si está vigente o ha sido modificada recientemente (hasta 2025)

IMPORTANTE: Señala explícitamente si hay contradicciones o tensiones
entre normas (ej: norma estatal vs decreto autonómico que la excepciona).
Esas tensiones son especialmente valiosas para nosotros.

FORMATO DE SALIDA:
Genera un fichero Markdown descargable con:
- Tabla principal: Norma | Tipo | Ámbito de aplicación | Vigencia | Notas
- Sección aparte: Lista de contradicciones/tensiones normativas detectadas

Al terminar, presenta un resumen de las normas más críticas y espera
mi confirmación antes de continuar.
```

---

## CAPA 2 — Mapa de procedimientos

### Instrucciones previas
Adjuntar los ficheros Markdown de Capa 0 y Capa 1.

### Prompt

```
Usando las tipologías (Capa 0) y el inventario legislativo (Capa 1)
que hemos elaborado, necesito ahora mapear los procedimientos completos.

TAREA: Para cada combinación significativa de [Tipo de instalación] ×
[Tipo de solicitud] que hayas identificado, describe el procedimiento
administrativo completo: qué fases/etapas deben superarse, en qué orden,
y bajo qué condiciones.

Para cada procedimiento indica:
- Nombre de la fase/etapa
- Si es OBLIGATORIA siempre, OBLIGATORIA bajo condición, u OPCIONAL
- La condición que la hace obligatoria u opcional (ej: "si potencia > 50MW",
  "si afecta a Red Natura 2000", "si suelo no urbanizable")
- Orden respecto a otras fases (qué debe completarse antes)
- Plazo legal asociado si existe
- Organismo competente o que debe intervenir

Si una combinación [instalación × solicitud] no tiene procedimiento propio
sino que hereda de otro tipo, indícalo explícitamente (ej: "igual que AAP
estándar salvo la fase X").

ESPECIAL ATENCIÓN a:
- Generación renovable (fotovoltaica, eólica, almacenamiento, hibridación):
  suelen tener regímenes específicos que difieren del procedimiento estándar
- Instalaciones de distribución vs generación vs transporte: procedimientos
  distintos
- Excepciones por tamaño/tensión/territorio (ej: instalaciones < 30kV en
  suelo urbano pueden tener procedimiento simplificado)

FORMATO DE SALIDA:
Un fichero Markdown descargable. Para cada procedimiento, una tabla:

| Fase | Obligatoria | Condición | Orden | Plazo | Organismo | Norma |
|------|-------------|-----------|-------|-------|-----------|-------|

Agrupa los procedimientos por tipo de instalación. Si dos procedimientos
son idénticos salvo excepciones, describe el estándar y luego las
diferencias como variantes.

Al terminar, lista los procedimientos cubiertos y espera confirmación.
```

---

## CAPA 3 — Reglas de secuencia y plazos

### Instrucciones previas
Adjuntar los tres ficheros anteriores. Esta capa produce el input
directo para el motor de reglas del sistema informático.

### Prompt

```
Tengo ya el mapa de procedimientos (adjunto). Ahora necesito extraer
las reglas de secuencia, prerequisitos y plazos en un formato
estructurado que pueda importar directamente a una base de datos.

TAREA: Para cada procedimiento mapeado, extrae todas las reglas del
siguiente tipo:

TIPO A — SECUENCIA: "La fase X no puede iniciarse hasta que la fase Y
  esté completada". O bien: "La fase X y la fase Y pueden ejecutarse
  en paralelo".

TIPO B — REQUISITO: "Para iniciar/cerrar la fase X es necesario
  disponer del documento/resultado D". O bien: "Para cerrar la
  solicitud de tipo S es obligatorio haber pasado por la fase X".

TIPO C — PLAZO: "La fase/trámite X tiene un plazo máximo/mínimo de
  N días [hábiles/naturales]". Incluye plazos de silencio administrativo.

TIPO D — EXCEPCIÓN: "La regla R no aplica si [condición técnica o
  territorial]". Por ejemplo: si suelo urbano + subterráneo + solo CT
  + tensión < 30kV → no es obligatoria la información pública.

Para cada regla, si hay incertidumbre en su interpretación legal,
márcala con flag INCERTIDUMBRE y explica el motivo.

FORMATO DE SALIDA — JSON descargable con este esquema exacto:

[
  {
    "regla_id": "R-001",
    "tipo": "SECUENCIA | REQUISITO | PLAZO | EXCEPCION",
    "descripcion": "texto legible de la regla",
    "aplica_a": {
      "tipo_instalacion": ["nombre"] o "TODAS",
      "tipo_solicitud": ["nombre"] o "TODAS",
      "tecnologia": ["nombre"] o "TODAS"
    },
    "condicion_activacion": "SIEMPRE | descripción de la condición",
    "enunciado": {
      "sujeto": "nombre de la fase o trámite afectado",
      "relacion": "REQUIERE_ANTES | REQUIERE_DOCUMENTO | PLAZO_MAX | PLAZO_MIN | SILENCIO_POSITIVO | SILENCIO_NEGATIVO | PARALELO_CON | EXCEPCION_DE",
      "objeto": "nombre de la fase, trámite o documento relacionado",
      "valor": null o "30 días hábiles"
    },
    "excepciones": [
      {
        "excepcion_id": "R-001-EX1",
        "condicion": "descripción de cuándo aplica",
        "efecto": "qué cambia respecto a la regla base"
      }
    ],
    "fuente": [
      {
        "norma": "RD 1955/2000",
        "articulo": "art. 128",
        "apartado": "1.b"
      }
    ],
    "incertidumbre": false,
    "nota_incertidumbre": null
  }
]

Genera el JSON completo como fichero descargable. Al terminar indica
cuántas reglas has generado por tipo y espera confirmación.
```

---

## Notas de uso

- Revisar cada capa aquí (en BDDAT/Claude Code) antes de lanzar la siguiente
- Volcar los ficheros generados en `docs/fuentesIA/referencias/`
- La Capa 3 en JSON es el artefacto más valioso: será la base del diseño
  de las tablas del motor de reglas
- Las `INCERTIDUMBRE` del JSON son puntos a resolver con el equipo jurídico
  o con conocimiento propio del dominio antes de implementar

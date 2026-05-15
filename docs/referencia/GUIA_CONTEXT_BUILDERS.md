# GUÍA — Context Builders para generación de escritos

> **Propósito:** Permitir la creación de nuevos tipos de escritos administrativos
> con campos calculados o cruzados, con soporte de Claude Code.
>
> **Audiencia:** Técnico de sistemas + Claude Code.
> El Supervisor gestiona plantillas; esta guía es para el responsable técnico.
>
> **Diseño de referencia:** `docs/referencia/DISEÑO_GENERACION_ESCRITOS.md`

---

## Qué es un Context Builder

Un Context Builder es una clase Python que enriquece el contexto base de un expediente
con campos específicos necesarios para un tipo de escrito concreto.

- **Sin Context Builder:** el escrito solo puede usar campos directos del expediente (capa base).
- **Con Context Builder:** el escrito puede usar campos calculados, cruzados o derivados.

El Supervisor no distingue la diferencia — en ambos casos prepara su plantilla .docx
con `{{campo}}` y el sistema la rellena. La diferencia es interna.

### Relación con el renderizador de plantillas

El Context Builder y el renderizador de plantillas son dos capas distintas que trabajan en secuencia:

1. **Context Builder** (capa de datos): código Python que consulta la BD y construye un diccionario
   `{variable: valor}`. Por ejemplo, consulta `requerimientos_tarea` y construye la lista Python
   `requerimientos = [{texto: "..."}, {texto: "..."}, ...]`.

2. **Renderizador** (capa de presentación): recibe ese diccionario y ejecuta la plantilla `.docx`.
   Los bloques Jinja2 de la plantilla (`{% for r in requerimientos %}`, `{{ r.texto }}`, etc.)
   operan sobre los datos que el Context Builder ya preparó.

El bloque `{% for %}` en la plantilla es necesario pero no suficiente — sin el Context Builder
que alimente la variable con datos reales de la BD, la lista estaría vacía. Ambas capas
deben estar sincronizadas: si se añade una variable nueva al Context Builder, la plantilla
debe incluir el token correspondiente, y viceversa.

---

## Cuándo crear un Context Builder

Cuando el Supervisor necesita un campo en la plantilla que NO está en el catálogo base:

- Datos de un organismo consultado (nombre, fecha respuesta, plazo)
- Estado calculado de una fase o trámite
- Combinación de fechas (`fecha_inicio` + días hábiles = `fecha_límite`)
- Datos de múltiples entidades (cotitulares, representantes legales)
- Cualquier dato que requiera JOINs o lógica más allá del expediente directo

---

## Estructura de un Context Builder

Todo CB vive en `app/services/context_builders/` con nombre en snake_case derivado de la clase.
La clase implementa exactamente dos métodos públicos:

```python
# app/services/context_builders/notificacion_organismo.py

from app.models import Documento, TipoDocumento

class ContextoNotificacionOrganismo:
    """
    Context Builder para escritos de notificación a organismos consultados.

    Campos adicionales que aporta:
    - organismo_nombre: Nombre del organismo consultado
    - organismo_nif: NIF del organismo
    - fecha_respuesta: Fecha administrativa del documento de respuesta
    - plazo_alegaciones: Plazo legal para presentar alegaciones (texto)
    - fecha_limite: Fecha límite calculada para el plazo
    """

    def __init__(self, expediente, db_session, tarea=None):
        self._expediente = expediente
        self._db = db_session
        self._tarea = tarea  # disponible si el CB necesita navegar al trámite

    def get_contexto(self) -> dict:
        """Devuelve los campos adicionales para esta plantilla."""
        doc_respuesta = (Documento.query
            .join(TipoDocumento)
            .filter(
                TipoDocumento.codigo == 'RESPUESTA_ORGANISMO',
                Documento.expediente_id == self._expediente.id
            )
            .order_by(Documento.fecha_administrativa.desc())
            .first())

        if doc_respuesta and doc_respuesta.organismo_vinculado:
            return doc_respuesta.organismo_vinculado.as_contexto_cb()

        return {}
```

El generador llama al CB así (no hay que registrarlo en ningún dict):

```python
# app/services/generador_escritos.py (infraestructura — no modificar)
builder = _cargar_context_builder(plantilla.contexto_clase)
ctx.update(builder(expediente, db_session).get_contexto())
```

`_cargar_context_builder` resuelve el módulo por convenio snake_case automáticamente:

- `ContextoNotificacionOrganismo` → `app.services.context_builders.contexto_notificacion_organismo`
- `ContextoConsultaSeparata` → `app.services.context_builders.consulta_separata`

**No hay dict de registro que mantener.** Basta con crear el fichero en el paquete.

---

## Convención `as_contexto_cb()`

Todo modelo que aporte datos enriquecidos a un CB implementa:

```python
def as_contexto_cb(self) -> dict:
    """Devuelve el fragmento de contexto que este modelo aporta a una plantilla."""
    ...
```

El CB es delgado: navega la cadena ESFTT hasta el modelo relevante y llama a su método.
La lógica de serialización vive en el modelo, no en el CB:

```python
def get_contexto(self) -> dict:
    # El CB delega en el modelo; no serializa aquí
    organismo_exp = self._expediente.organismos[0]
    return organismo_exp.as_contexto_cb()
```

Esta convención **no** aplica a los modelos de Capa 1 (`Expediente`, `Titular`, `Proyecto`),
que son accedidos directamente por `ContextoBaseExpediente`.

---

## Context Builders disponibles

| Clase | Fichero | Trámite | Estado | Issue |
|-------|---------|---------|--------|-------|
| `ContextoConsultaSeparata` | `consulta_separata.py` | `CONSULTA_SEPARATA` | Implementado | #391 |
| `ContextoAnalisisDocumental` | `analisis_documental.py` | `ANALISIS_DOCUMENTAL` | Bloqueado — tabla diagnosticos no diseñada | #392 |
| `ContextoRecepcionAlegacion` | `recepcion_alegacion.py` | `RECEPCION_ALEGACION` | Implementado | #393 |
| `ContextoAnalisisAlegaciones` | `analisis_alegaciones.py` | `ANALISIS_ALEGACIONES` | Bloqueado — depende de #393 | #394 |

---

## Cómo registrar el tipo en la BD

```python
# En migración manual (flask db revision -m "Añadir tipo escrito NOTIF_ORGANISMO")
# Editar el .py generado:

def upgrade():
    op.execute("""
        INSERT INTO public.plantillas
            (codigo, nombre, descripcion, plantilla_url, contexto_clase, activo)
        VALUES (
            'NOTIF_ORGANISMO',
            'Notificación a organismo consultado',
            'Traslado de respuesta de organismo con plazo de alegaciones',
            'escritos/notificacion_organismo.docx',
            'ContextoNotificacionOrganismo',
            TRUE
        )
    """)

def downgrade():
    op.execute("DELETE FROM public.plantillas WHERE codigo = 'NOTIF_ORGANISMO'")
```

---

## Campos del contexto base (disponibles en todos los escritos)

| Campo | Descripción |
|-------|-------------|
| `expediente_id` | ID técnico interno |
| `numero_at` | Número administrativo (AT-XXXXX) |
| `titular_nombre` | Nombre o razón social del titular |
| `titular_nif` | NIF/CIF del titular |
| `titular_direccion` | Dirección de notificación preferente |
| `proyecto_titulo` | Título del proyecto técnico |
| `proyecto_finalidad` | Finalidad de la instalación |
| `proyecto_emplazamiento` | Emplazamiento descriptivo |
| `instrumento_ambiental` | Siglas del instrumento (AAI, AAU, EXENTO...) |
| `responsable_nombre` | Nombre completo del tramitador asignado |
| `municipios` | Lista de nombres de municipios afectados (`list[str]`) |
| `fecha_hoy` | Fecha actual formateada (DD/MM/AAAA) |

*(Fuente: `app/services/escritos.py` → clase `ContextoBaseExpediente`)*

---

## Workflow git para un nuevo Context Builder

```bash
# 1. Crear rama
git checkout -b feature/issue-XXX-context-builder-nombre

# 2. Crear el fichero de la clase
# app/services/context_builders/nombre.py

# 3. Añadir la plantilla .docx al repositorio
# app/static/escritos/nombre.docx

# 4. Crear migración manual
flask db revision -m "Añadir tipo escrito NOMBRE"
# Editar manualmente el .py generado con el INSERT

# 5. Commit con todos los ficheros relacionados
git add app/services/context_builders/nombre.py
git add app/static/escritos/nombre.docx
git add migrations/versions/XXXX_nombre.py
git commit -m "[SERVICIO] #XXX añadir Context Builder nombre"

# 6. PR contra develop
gh pr create --title "CB nombre" --body-file /d/BDDAT/docs_prueba/temp/gh_body.md
```

---

## Qué documentar en el manual de usuario

Al crear un nuevo tipo de escrito, añadir en el manual:

1. **Nombre y propósito** — qué tramitación cubre este escrito
2. **Cuándo usarlo** — en qué tarea de qué trámite aparece disponible
3. **Catálogo de campos** — derivado del Context Builder y las consultas nombradas
4. **Requisitos previos** — qué datos deben existir en el expediente
5. **Ejemplo de resultado** — captura o fragmento del escrito generado

---

## Cómo pedir soporte a Claude Code

Abrir Claude Code en el proyecto y describir:

> "Necesito un Context Builder para el tipo de escrito [nombre].
> La plantilla va en [nombre_plantilla.docx].
> Los campos que necesito son: [lista de campos y de dónde vienen en el expediente].
> El escrito se usa en la tarea [tipo_tarea] del trámite [tipo_tramite]."

Claude Code leerá esta guía y creará el Context Builder siguiendo el patrón.

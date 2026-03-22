# GUÍA — Context Builders para generación de escritos

> **Propósito:** Permitir la creación de nuevos tipos de escritos administrativos
> con campos calculados o cruzados, con soporte de Claude Code.
>
> **Audiencia:** Técnico de sistemas + Claude Code.
> El Supervisor gestiona plantillas; esta guía es para el responsable técnico.
>
> **Diseño de referencia:** `docs/fuentesIA/ARQUITECTURA_DOCUMENTOS.md`

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

```python
# app/services/context_builders/notificacion_organismo.py

from app.models import Documento, TipoDocumento
from app.services.escritos import ContextoBaseExpediente

class ContextoNotificacionOrganismo:
    """
    Context Builder para escritos de notificación a organismos consultados.

    Campos adicionales que aporta (ver campos_catalogo en tipos_escritos):
    - organismo_nombre: Nombre del organismo consultado
    - fecha_respuesta: Fecha administrativa del documento de respuesta
    - plazo_alegaciones: Plazo legal para presentar alegaciones (texto)
    - fecha_limite: Fecha límite calculada para el plazo
    """

    def get_contexto(self, tarea_id: int) -> dict:
        """Devuelve el contexto enriquecido para la tarea indicada."""
        from app.models import Tarea

        # 1. Subir el árbol ESFTT hasta el nivel necesario
        tarea = Tarea.query.get_or_404(tarea_id)
        tramite = tarea.tramite
        fase = tramite.fase
        solicitud = fase.solicitud
        expediente = solicitud.expediente

        # 2. Partir siempre del contexto base
        contexto = ContextoBaseExpediente.get_contexto(expediente.id)

        # 3. Enriquecer con campos específicos
        doc_respuesta = (Documento.query
            .join(TipoDocumento)
            .filter(
                TipoDocumento.codigo == 'RESPUESTA_ORGANISMO',
                Documento.expediente_id == expediente.id
            )
            .order_by(Documento.fecha_administrativa.desc())
            .first())

        if doc_respuesta and doc_respuesta.organismo_vinculado:
            organismo = doc_respuesta.organismo_vinculado.organismo
            contexto.update({
                'organismo_nombre': organismo.nombre,
                'organismo_nif': organismo.nif,
                'fecha_respuesta': doc_respuesta.fecha_administrativa.strftime('%d/%m/%Y'),
                'plazo_alegaciones': '15 días hábiles',
                'fecha_limite': '',  # calculado por plazos.py cuando esté en M3
            })

        return contexto
```

---

## Registrar el Context Builder en el dispatcher

```python
# app/services/escritos.py → diccionario CONTEXT_BUILDERS

CONTEXT_BUILDERS = {
    'ContextoNotificacionOrganismo': ContextoNotificacionOrganismo,
    # añadir nuevos aquí
}

def get_contexto(tipo_escrito: TipoEscrito, tarea_id: int) -> dict:
    """Devuelve el contexto apropiado según el tipo de escrito."""
    if tipo_escrito.contexto_clase and tipo_escrito.contexto_clase in CONTEXT_BUILDERS:
        builder = CONTEXT_BUILDERS[tipo_escrito.contexto_clase]()
        return builder.get_contexto(tarea_id)
    return ContextoBaseExpediente.get_contexto_desde_tarea(tarea_id)
```

---

## Cómo registrar el tipo en la BD

```python
# En migración manual (flask db revision -m "Añadir tipo escrito NOTIF_ORGANISMO")
# Editar el .py generado:

def upgrade():
    op.execute("""
        INSERT INTO public.tipos_escritos
            (codigo, nombre, descripcion, plantilla_url, contexto_clase, campos_catalogo, activo)
        VALUES (
            'NOTIF_ORGANISMO',
            'Notificación a organismo consultado',
            'Traslado de respuesta de organismo con plazo de alegaciones',
            'escritos/notificacion_organismo.docx',
            'ContextoNotificacionOrganismo',
            '{
                "expediente_codigo": "Código del expediente (AT-XXXXX)",
                "titular_nombre": "Nombre del titular",
                "organismo_nombre": "Nombre del organismo consultado",
                "fecha_respuesta": "Fecha de la respuesta del organismo (DD/MM/AAAA)",
                "plazo_alegaciones": "Plazo legal para alegaciones",
                "fecha_limite": "Fecha límite calculada"
            }',
            TRUE
        )
    """)

def downgrade():
    op.execute("DELETE FROM public.tipos_escritos WHERE codigo = 'NOTIF_ORGANISMO'")
```

---

## Campos del contexto base (disponibles en todos los escritos)

| Campo | Descripción |
|-------|-------------|
| `expediente_codigo` | AT-XXXXX |
| `expediente_tipo` | Tipo de expediente (Distribución, Transporte...) |
| `titular_nombre` | Nombre o razón social del titular |
| `titular_nif` | NIF/CIF del titular |
| `titular_direccion` | Dirección postal del titular |
| `titular_municipio` | Municipio del titular |
| `proyecto_denominacion` | Denominación del proyecto |
| `proyecto_municipio` | Municipio/s del proyecto |
| `proyecto_tension` | Tensión nominal (kV) |
| `proyecto_ia` | Instrumento ambiental (AAI, CA, EXENTO...) |
| `fecha_hoy` | Fecha actual formateada (DD/MM/AAAA) |

*(Lista completa en `app/services/escritos.py` → clase `ContextoBaseExpediente`)*

---

## Workflow git para un nuevo Context Builder

```bash
# 1. Crear rama
git checkout -b feature/issue-XXX-context-builder-nombre

# 2. Crear el fichero de la clase
# app/services/context_builders/nombre.py

# 3. Registrar en el dispatcher
# app/services/escritos.py → diccionario CONTEXT_BUILDERS

# 4. Añadir la plantilla .docx al repositorio
# app/static/escritos/nombre.docx

# 5. Crear migración manual
flask db revision -m "Añadir tipo escrito NOMBRE"
# Editar manualmente el .py generado con el INSERT

# 6. Commit con todos los ficheros relacionados
git add app/services/context_builders/nombre.py
git add app/services/escritos.py
git add app/static/escritos/nombre.docx
git add migrations/versions/XXXX_nombre.py
git commit -m "[SERVICIO]: Añadir Context Builder [nombre] — issue #XXX"

# 7. PR contra develop
gh pr create --title "Context Builder: [nombre]" --body "..."
```

---

## Qué documentar en el manual de usuario

Al crear un nuevo tipo de escrito, añadir en el manual:

1. **Nombre y propósito** — qué tramitación cubre este escrito
2. **Cuándo usarlo** — en qué tarea de qué trámite aparece disponible
3. **Catálogo de campos** — copiar de `campos_catalogo` en `tipos_escritos`
4. **Requisitos previos** — qué datos deben existir en el expediente
5. **Ejemplo de resultado** — captura o fragmento del escrito generado

---

## Cómo pedir soporte a Claude Code

Abrir Claude Code en el proyecto y describir:

> "Necesito un Context Builder para el tipo de escrito [nombre].
> La plantilla va en [nombre_plantilla.docx].
> Los campos que necesito son: [lista de campos y de dónde vienen en el expediente].
> El escrito se usa en la tarea [tipo_tarea] del trámite [tipo_tramite]."

Claude Code leerá esta guía y creará el Context Builder siguiendo el patrón,
incluyendo migración, registro en el dispatcher y commit.

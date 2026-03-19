# Guía de Plantillas para el Supervisor
## Sistema de generación de escritos administrativos

> **Para quién es esta guía:** Supervisores que crean y registran plantillas .docx
> para la generación automática de escritos administrativos.
>
> **Requisito previo:** Saber usar Microsoft Word o LibreOffice Writer.

---

## Cómo funciona

1. El supervisor crea un fichero `.docx` con el texto del escrito.
2. En los lugares donde deben aparecer datos del expediente, escribe **marcadores** con la sintaxis `{{campo}}`.
3. Registra la plantilla en la aplicación (pantalla de administración → Plantillas).
4. El tramitador genera el escrito desde la tarea REDACTAR: la aplicación sustituye los marcadores por los datos reales y produce el `.docx` final.

---

## 1. Campos disponibles (contexto base)

Estos campos están **siempre disponibles** en cualquier plantilla, sin configuración adicional:

| Marcador | Qué contiene |
|----------|-------------|
| `{{numero_at}}` | Número de expediente (ej: `AT-1234`) |
| `{{expediente_id}}` | ID técnico interno del expediente |
| `{{titular_nombre}}` | Nombre o razón social del titular |
| `{{titular_nif}}` | NIF/CIF del titular |
| `{{titular_direccion}}` | Dirección de notificación preferente |
| `{{proyecto_titulo}}` | Título del proyecto técnico |
| `{{proyecto_finalidad}}` | Finalidad de la instalación |
| `{{proyecto_emplazamiento}}` | Emplazamiento descriptivo |
| `{{instrumento_ambiental}}` | Siglas del instrumento (AAI, AAU, EXENTO…) |
| `{{responsable_nombre}}` | Nombre completo del tramitador asignado |
| `{{municipios}}` | Lista de municipios afectados |
| `{{fecha_hoy}}` | Fecha actual en formato DD/MM/AAAA |

---

## 2. Campo simple

**Lo más habitual.** Se escribe el marcador en cualquier lugar del texto.

### En la plantilla Word escribes:

```
En relación con el expediente {{numero_at}}, cuyo titular es
{{titular_nombre}} ({{titular_nif}}), con emplazamiento en
{{proyecto_emplazamiento}},
```

### El resultado generado:

```
En relación con el expediente AT-1234, cuyo titular es
Empresa Ejemplo S.L. (B12345678), con emplazamiento en
Polígono Industrial Las Marismas, parcela 7,
```

### Notas:
- Si el campo es `None` (no existe para ese expediente), aparece **vacío** (sin error).
- Para poner un valor por defecto: `{{titular_direccion|default('Sin dirección registrada')}}`.
- Para poner en mayúsculas: `{{titular_nombre|upper}}`.

---

## 3. Consulta nombrada → valor único

Las **consultas nombradas** se registran en la aplicación (Administración → Consultas nombradas).
Cada consulta tiene un nombre-clave (ej: `num_documentos`) y devuelve filas de datos del expediente.

### Caso: la consulta devuelve un único valor

Si la consulta `num_documentos` devuelve una sola fila con una sola columna `total`:

### En la plantilla Word escribes:

```
El expediente cuenta con {{num_documentos[0].total}} documentos incorporados.
```

### El resultado generado:

```
El expediente cuenta con 12 documentos incorporados.
```

---

## 4. Consulta nombrada → tabla

### 4a. Tabla básica

Crea una tabla Word con tantas columnas como campos quieras mostrar.
La **primera fila** es la cabecera (texto fijo).
La **segunda fila** lleva los marcadores de bucle y de datos.

### En la plantilla Word, la tabla tiene esta estructura:

| `{%tr for row in organismos_consultados %}` | | |
|---|---|---|
| **Organismo** | **Tipo** | **Fecha inclusión** |
| `{{row.nombre}}` | `{{row.tipo}}` | `{{row.fecha}}` |
| `{%tr endfor %}` | | |

> **Importante:** Los marcadores `{%tr for ... %}` y `{%tr endfor %}` deben estar
> solos en su propia fila de la tabla (pueden estar en la primera celda; el resto
> de celdas de esa fila quedan vacías o pueden no existir).

### El resultado generado (con 3 organismos):

| **Organismo** | **Tipo** | **Fecha inclusión** |
|---|---|---|
| Confederación Hidrográfica | SEPARATA | 01/03/2026 |
| Delegación de Cultura | LISTA | 05/03/2026 |
| Red Eléctrica de España | SEPARATA | 10/03/2026 |

El formato de la fila de datos (fuente, bordes, sombreado) se define en la plantilla
y se replica automáticamente para cada fila generada.

---

### 4b. Tabla con cabecera condicional (se elimina si está vacía)

Si la consulta puede devolver cero filas, la cabecera quedaría sola y quedaría feo.
Solución: aplicar la misma condición a la fila de cabecera.

### En la plantilla Word:

| `{%tr if organismos_consultados %}` | | |
|---|---|---|
| **Organismo** | **Tipo** | **Fecha** |
| `{%tr endif %}` — `{%tr for row in organismos_consultados %}` | | |
| `{{row.nombre}}` | `{{row.tipo}}` | `{{row.fecha}}` |
| `{%tr endfor %}` | | |

> **Truco:** El `{%tr endif %}` y el `{%tr for ... %}` pueden ir en filas separadas
> o en la misma fila si la tabla lo permite. Lo más limpio es una fila por marcador.

**Cuando la consulta devuelve filas:** aparece cabecera + datos.
**Cuando devuelve vacío:** la tabla entera desaparece del documento.

---

## 5. Lista con viñetas

### En la plantilla Word:

1. Crea un párrafo con estilo de lista (viñeta o numerada).
2. Escribe los marcadores de bucle y el campo dentro.

El párrafo de la plantilla (con su estilo de viñeta) se replica una vez por elemento.

### En la plantilla Word escribes (un único párrafo con viñeta):

```
• {%p for municipio in municipios %}{{municipio}}{%p endfor %}
```

> **Nota:** `{%p ... %}` es el marcador de control a nivel de párrafo completo
> (en lugar de `{% ... %}` que es inline). Úsalo siempre para bucles y condicionales
> que afecten a párrafos enteros.

### El resultado generado:

```
• Alcalá la Real
• Alcaudete
• Martos
```

Con el estilo de viñeta exacto que definiste en la plantilla.

---

## 6. Condicionales

### 6a. Párrafo condicional (aparece o no según los datos)

### En la plantilla Word (un párrafo con el condicional):

```
{%p if instrumento_ambiental == 'AAI' %}
Este proyecto está sujeto a Autorización Ambiental Integrada y deberá
aportar la documentación prevista en el artículo 12 de la Ley 16/2002.
{%p endif %}
```

El párrafo completo aparece solo si el expediente tiene instrumento AAI.
Si no, desaparece sin dejar espacio en blanco.

### 6b. Fila de tabla condicional

```
{%tr if proyecto_finalidad %}
| **Finalidad:** | {{proyecto_finalidad}} |
{%tr endif %}
```

La fila desaparece si el campo está vacío.

---

## 7. Fragmentos insertables

Un **fragmento** es un fichero `.docx` independiente que se inserta en el lugar
indicado. Útil para cláusulas legales, membretes, pies estándar que se reutilizan
en múltiples plantillas.

Los ficheros de fragmento se depositan en la carpeta `fragmentos/` del servidor
(el administrador del sistema los gestiona).

### En la plantilla Word escribes (en su propio párrafo, solo, sin texto alrededor):

```
{{r ClausulaConfidencialidad}}
```

> **Regla obligatoria:** El marcador `{{r NombreFragmento}}` debe estar
> **completamente solo en su párrafo** — sin texto antes ni después, ni espacios.
> Si hay texto en el mismo párrafo, el fragmento no se insertará.

### Resultado:

El contenido completo del fichero `ClausulaConfidencialidad.docx` aparece
en ese punto del documento, con su propio formato.

**Funciona también en cabeceras y pies de página**, con la misma regla.

**Limitación:** Los marcadores `{{campo}}` dentro de un fragmento **no se procesan**.
Los fragmentos son contenido estático. Si necesitas contenido dinámico, ponlo
en la plantilla principal.

---

## 8. Filtros útiles de Jinja2

Se añaden con `|` después del campo:

| Sintaxis | Efecto | Ejemplo resultado |
|----------|--------|-------------------|
| `{{campo\|upper}}` | Mayúsculas | `EMPRESA EJEMPLO S.L.` |
| `{{campo\|lower}}` | Minúsculas | `empresa ejemplo s.l.` |
| `{{campo\|title}}` | Primera letra mayúscula | `Empresa Ejemplo S.l.` |
| `{{campo\|default('texto')}}` | Valor si campo es None | `Sin datos` |
| `{{lista\|join(', ')}}` | Une lista con separador | `Alcalá, Martos, Alcaudete` |
| `{{lista\|length}}` | Número de elementos | `3` |

---

## 9. Registrar la plantilla en la aplicación

Una vez creado el fichero `.docx`:

1. Ir a **Administración → Plantillas**.
2. Crear nueva plantilla:
   - **Nombre:** texto legible (aparece en el desplegable del tramitador).
   - **Código:** identificador slug único (ej: `REQUERIMIENTO_SUBSANACION`).
   - **Fichero:** subir el `.docx`.
   - **Tipo de documento:** qué tipo se asignará al documento generado en el pool.
   - **Filtros ESFTT:** tipo de expediente, solicitud, fase y/o trámite donde aplica
     (dejar vacío = aplica a cualquier contexto).
   - **Variante:** si hay varias versiones del mismo escrito (ej: `Favorable`, `Denegatoria`).

---

## Referencia rápida

```
{{campo}}                          Campo simple
{{campo|default('N/D')}}           Campo con valor por defecto
{{consulta[0].columna}}            Primer resultado de una consulta
{%p if condicion %}...{%p endif %} Párrafo condicional
{%p for x in lista %}...{%p endfor %} Lista/bucle a nivel párrafo
{%tr for row in consulta %}        Bucle de filas en tabla
{%tr endfor %}                     Fin bucle de filas
{%tr if condicion %}               Fila condicional
{%tr endif %}                      Fin fila condicional
{{r NombreFragmento}}              Insertar fragmento (párrafo propio)
```

# S05b — La Entidad

## Metadatos

- **Layout:** Contenido (texto completo, sin imagen derecha)
- **Fragments:** Sí
- **Artefacto visual:** Ninguno
- **Posición:** Entre S05 (Tramitación estructurada) y S06 (Sistema documental)
- **Número de sección sugerido:** 5.5 (o renumerar las siguientes si se prefiere secuencia limpia)

---

## Contenido visible

**Número de sección:** 5.5

**Título** *(extrabold negro):*
> Todos los actores, una sola tabla

**Subtítulo** *(bold verde):*
> El rol es circunstancial. La entidad, no.

**Bullets** *(se revelan con clic):*

1. *(fragment)* En un expediente intervienen actores de naturaleza muy distinta: el **titular** que promueve la instalación, los **organismos** que emiten condicionados, la **Diputación** que publica en el BOP, el **Ayuntamiento** afectado por la información pública…

2. *(fragment)* La solución obvia es una tabla por tipo: `titulares`, `organismos`, `ayuntamientos`, `diputaciones`… El problema: la misma organización puede actuar en varios roles a la vez, y los datos de contacto se duplican sin control

3. *(fragment)* BDDAT usa **una sola tabla `entidades`** con campos comunes (NIF, nombre, dirección, contacto) y tres roles booleanos que se activan según el contexto del trámite:
   `rol_titular` · `rol_consultado` · `rol_publicador`

4. *(fragment)* El campo `tipo_titular` no define el procedimiento directamente: permite **filtrar y segmentar titulares** según sus características propias — gran distribuidora, promotor privado, organismo público — y aplicar lógicas diferenciadas para cada colectivo cuando el procedimiento lo requiere
   - *(popup sobre "tipo_titular" — ver sección Popups)*

5. *(fragment)* Una entidad puede además **autorizar a otra para actuar en su nombre**: si una empresa gestora representa a un titular en la tramitación, el sistema lo registra y lo tiene en cuenta. La autoautorización es implícita — el titular siempre puede actuar por sí mismo sin entrada adicional
   - *(popup sobre "actuar en su nombre" — ver sección Popups)*

6. *(fragment)* Cada entidad puede tener además **distintas direcciones de notificación según el rol** que desempeña: e-distribución como titular recibe los escritos en su departamento de tramitaciones; como empresa consultada, en su área técnica. El sistema sabe siempre a quién dirigirse — y en qué canal.
   - *(popup sobre "direcciones de notificación" — ver sección Popups)*


---

## Popups

### Popup: `tipo_titular`

**Disparador:** el texto `tipo_titular` en el bullet 4.

**Título:** Tipos de titular

**Contenido:**

Los tipos permiten filtrar y trabajar con grupos de titulares de forma selectiva —
por ejemplo, ver todos los expedientes de grandes distribuidoras, o aplicar
reglas distintas para promotores privados.

| Valor | Descripción |
|---|---|
| `GRAN_DISTRIBUIDORA` | Empresa PTD (producción, transporte o distribución) |
| `DISTRIBUIDOR_MENOR` | Distribuidora no PTD que cede la instalación antes de la puesta en servicio |
| `PROMOTOR` | Promotor privado no PTD |
| `ORGANISMO_PUBLICO` | Administración pública promotora |
| `OTRO` | Sin clasificar (valor por defecto en migración desde sistema anterior) |

Si el titular es o no distribuidora determina el régimen de autorización aplicable —
el sistema usa este campo para diferenciar el procedimiento.

---

### Popup: `direcciones de notificación`

**Disparador:** el texto `direcciones de notificación` en el bullet 6.

**Título:** Dirección de notificación

**Contenido:**

Cada dirección se activa para uno o varios roles (titular, consultado, publicador).
El sistema usa siempre la más reciente activa para el rol correspondiente.
Cambiar la dirección no elimina el historial — borrado lógico.

| Canal | Descripción |
|---|---|
| Postal | Dirección estructurada (calle, CP, municipio) |
| Email | Correo aviso de Notifica-PNT |
| DIR3 | Código de unidad orgánica para organismos públicos |
| SIR | Sistema de Información del Registro (telemático) |

---

### Popup: `actuar en su nombre`

**Disparador:** el texto `actuar en su nombre` en el bullet 5.

**Título:** Autorizado titular

**Contenido:**

La tabla `autorizados_titular` registra relaciones N:N entre entidades:
un titular puede autorizar a varios administrados, y un administrado puede
estar autorizado por varios titulares.

Características del modelo:
- **Borrado lógico** — revocar una autorización no destruye el historial
- **Observaciones libres** — permite anotar el tipo de poder o documento que sustenta la autorización
- **Autoautorización implícita** — el titular siempre puede actuar por sí mismo; no necesita entrada en esta tabla

---

## Notas ponente

El bullet 6 responde directamente la pregunta "¿A quién notifica el sistema?":
a la entidad con el rol correspondiente, en la dirección que ella misma haya configurado para ese rol.

El concepto clave es la separación entre *qué es* una entidad (sus datos) y *qué hace*
en un expediente concreto (su rol). Esa separación es lo que permite reutilizar el mismo
registro sin duplicar.

Bullet 4: subrayar que `tipo_titular` no es burocracia — es el mecanismo que permite,
por ejemplo, que jefatura vea "todos los expedientes de grandes distribuidoras" con un filtro,
o que el sistema aplique una lógica diferente al cerrar una fase según el tipo de promotor.

Bullet 5: el caso típico es una empresa consultora o gestora que lleva varios expedientes
de distintos titulares. Sin este modelo, habría que registrar a la gestora como titular
en cada expediente, perdiendo la trazabilidad real de quién es el propietario de la instalación.

Bullet 6: conectar con S05 — "los tipos definen el procedimiento, los roles definen los actores".

Transición a S06: "Esas mismas entidades son los destinatarios de los documentos que el sistema gestiona."

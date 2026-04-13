# S05b — La Entidad

## Metadatos

- **Layout:** Contenido (texto completo, sin imagen derecha)
- **Fragments:** Sí
- **Artefacto visual:** Ninguno — la claridad la da el texto y el popup de `tipo_titular`
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

1. *(fragment)* En un expediente intervienen actores muy distintos: el **titular** que promueve la instalación, los **organismos** que emiten condicionados, la **Diputación** que publica en el BOP, el **Ayuntamiento** afectado por la información pública…

2. *(fragment)* La solución obvia es una tabla por tipo: `titulares`, `organismos`, `ayuntamientos`, `diputaciones`… El problema: la misma organización puede actuar en varios roles a la vez, y los datos de contacto se duplican sin control

3. *(fragment)* BDDAT usa **una sola tabla `entidades`** con campos comunes (NIF, nombre, dirección, contacto) y tres roles booleanos que se activan según el contexto: `rol_titular` · `rol_consultado` · `rol_publicador`

4. *(fragment)* Una Diputación puede tener `rol_consultado` **y** `rol_publicador` simultáneamente — sin duplicar el registro. El rol lo determina el trámite, no la estructura de la tabla

5. *(fragment)* Cuando el titular es una gran distribuidora o un promotor privado, el campo `tipo_titular` añade la distinción que el procedimiento legal requiere — sin romper el modelo unificado

   - 5.1 *(popup sobre "tipo_titular" — ver sección Popups abajo)*

6. *(fragment)* La misma filosofía que el resto del sistema: **la semántica vive en los roles y los tipos, no en los campos ni en las tablas**

---

## Popups

### Popup: `tipo_titular`

**Disparador:** el texto `tipo_titular` en el bullet 5.

**Título:** Variantes del titular

**Contenido:**

| Valor | Descripción |
|---|---|
| `GRAN_DISTRIBUIDORA` | Empresa PTD (producción, transporte o distribución). Autorización por RD 1955/2000 |
| `DISTRIBUIDOR_MENOR` | Distribuidora no PTD que cede la instalación antes de la puesta en servicio |
| `PROMOTOR` | Promotor privado no PTD. Puede quedar exento según el tipo de instalación |
| `ORGANISMO_PUBLICO` | Administración pública promotora |
| `OTRO` | Sin clasificar (valor por defecto en migración desde sistema anterior) |

La distinción determina qué procedimiento de autorización aplica: RD 1955/2000, RAT o exención directa.

---

## Notas ponente

Esta slide puede dispararse con la pregunta "¿A quién notifica el sistema?". Respuesta:
a la entidad que tenga el rol correspondiente en ese trámite — y eso el sistema ya lo sabe porque la entidad lo declara.

El concepto clave es la separación entre *qué es* una entidad (sus datos de contacto) y *qué hace* en un expediente concreto (su rol). Esa separación es lo que permite reutilizar el mismo registro sin duplicar.

Bullet 6: conectar explícitamente con S05 — "los tipos definen el procedimiento, los roles definen los actores". Es el mismo principio.

Transición a S06: "Esas mismas entidades son los destinatarios de los documentos que el sistema gestiona. Os explico cómo funciona eso."

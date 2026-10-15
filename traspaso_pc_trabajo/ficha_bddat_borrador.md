# Ficha de BDDAT — borrador 2 (guion para imprimir)

Cambios respecto al borrador 1: cabecera sin organismo, pie quitado, frase del conocimiento fuera, «despliegue
progresivo» sustituido por los tres modos del motor, dos conceptos nuevos (el documento como centro del dato; las
tareas consumen y producen documentos), SEDEBOJA fuera, y los elementos eléctricos (`genete/bddat-instalaciones`)
en «después de producción».

---

# A) LA FICHA (una página A4)

**BDDAT · Sistema de tramitación de expedientes de alta tensión**

## 1. Fin
Llevar un expediente de autorización de instalaciones de alta tensión **de principio a fin en el navegador**,
con la estructura legal del procedimiento como guía, y sustituir las hojas de cálculo y la base Access
actuales.

## 2. Bondades
- **Sin instalación**: solo navegador y red.
- **El estado se calcula solo**: lo que toca hacer en cada expediente sale de sus documentos, sin actualizarlo a mano.
- **Trazabilidad completa**: quién hizo qué y cuándo; todo salto del flujo queda justificado en bitácora.
- **Plazos automáticos** desde un catálogo editable, con calendario hábil y suspensiones.
- **Se adapta a cambios normativos** modificando registros, no código.

## 3. Estructura
**Expediente → Solicitud → Fase → Trámite → Tarea** (4 tipos de tarea: analizar, elaborar, notificar, esperar plazo).
Cuatro roles: **tramitador, administrativo, supervisor, administrador**.
Una sola tabla de **entidades** (titulares, organismos, ayuntamientos…) con roles circunstanciales.
Interfaz en zonas: cabecera con buscador, menú, cuerpo, inspector lateral y panel de bitácora.

## 4. Conceptos novedosos
- **La semántica vive en los tipos**, no en la multiplicación de campos.
- **El documento es el centro del dato del expediente**: las fechas son del documento (fecha administrativa), la
  estructura no guarda fechas y el estado se deriva.
- **Las tareas consumen y producen documentos**: así se sabe qué borrador produjo qué resolución firmada.
- **Motor de reglas** separado del código y agnóstico del dominio: Ley → variables → reglas → tramitación.
- **Tres modos del motor**: inactivo, avisa o bloquea.
- **Invariantes con escape**: lo que el motor no cubre se protege con reglas fijas; solo lo ya notificado al exterior no se puede deshacer.
- **Almacén documental propio**, con manifiestos por expediente que permiten reconstruir las carpetas sin BDDAT.

## 5. Tecnología
Python y Flask · PostgreSQL · SQLAlchemy y Alembic · Bootstrap con la identidad visual de la Junta · islas React
para el árbol del expediente · escritos en LibreOffice (.odt). Todo **software libre**, sin coste de licencias;
código bajo **EUPL v1.2**. Despliegue previsto: Linux, nginx y contenedores.
- **Modelo de datos:** 71 tablas y 192 migraciones que reconstruyen el esquema y el catálogo desde cero.
- **Aplicación:** unas 48.000 líneas de Python; 75 módulos de servicios; 50 blueprints y unas 250 rutas.
- **Interfaz:** 95 plantillas Jinja y unas 9.400 líneas de React.
- **Calidad:** más de 2.200 pruebas automáticas y 53 decisiones de diseño documentadas (ADR).

## 6. Alcance
**Cubre:** tramitación estructurada de expedientes AT con sus solicitudes; documentos y almacén; generación de
escritos desde plantillas; notificaciones, incluida la edictal; plazos; seguimiento y estadísticas por rol.
**No cubre (todavía):** portafirmas ni envío de notificaciones (Notifica); previstos de forma indirecta mediante
automatización.

## 7. Estado
- **Hecho:** árbol del expediente interactivo; fases de análisis documental y consultas; reformados de proyecto;
  certificados de cierre; notificación edictal; plazos desde catálogo; motor de reglas e invariantes; sellado de fase
  cerrada; almacén de ficheros; escritos en .odt; buscador global; seguimiento y estadísticas.
- **En curso:** fase de DUP; notificaciones a varios destinatarios; interfaz unificada.
- **Pendiente antes de producción:** resto de fases, importación de expedientes de Access y adecuación
  al ENS (categorización y medidas técnicas: HTTPS, copias, autenticación corporativa, registro).
- **Después de producción:** automatización de BandeJA, Notifica-PNT y Port@firmas; mensajería; elementos
  eléctricos del proyecto (activos), con repositorio propio `genete/bddat-instalaciones`, y su cartografía (PostGIS);
  manual de usuario; exportaciones e informes.

---

# B) NOTAS

**Sobre «pantalla de notificaciones» (tu pregunta).** En la presentación de octubre (ficha 12, post-producción) el
punto dice: «la interfaz de notificaciones, y la automatización de BandeJA, Notifica-PNT y Port@firmas». Se refiere
a una **pantalla propia para gestionar las notificaciones** (a quién, con qué dirección, en qué estado, con su
justificante) más la automatización de los envíos. Pero la propia ficha 10 dice que «falta la interfaz» de las
notificaciones a varios destinatarios, y `CONTEXTO_ACTUAL.md` / `ESTADO_ADR049.md` muestran que la parte de interfaz
de #929 (zona A, tramitar una notificación; zonas B a E pendientes) **está en el «Próximo», antes de producción**.
Así que ese punto de la ficha 12 está desfasado: en la ficha del borrador 2 he dejado solo la **automatización** en
«después de producción», y la interfaz de notificaciones queda implícita en «en curso: notificaciones a varios
destinatarios». ¿Te cuadra?

**Elementos eléctricos.** `docs/decisiones/ADR-030` ya cita `bddat-instalaciones` (#592, M5) para integrar PostGIS con
los activos de red. Lo he enlazado con la cartografía porque así figura; corrígelo si no es una sola cosa.

**Cifras comprobadas hoy en el repo** (ficheros versionados en git): 71 tablas (clases con `__tablename__`), 192
migraciones, 75 módulos de servicios, 50 blueprints, 252 decoradores `@route`, 95 plantillas Jinja, 48.156 líneas de
Python en `app/`, 9.367 de React, 53 ADR y 2.219 pruebas recogidas por pytest. Las cifras de rutas y de React son
recuentos mecánicos (no cuentan rutas registradas de otra forma); por eso van redondeadas en la ficha.

**Sin cabecera de organismo ni pie**, como pediste. El título de la página sí lo mantengo.

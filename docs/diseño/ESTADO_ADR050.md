# Estado de la cadena de issues — ADR-050

> Registro vivo. `ADR-050` es la fuente de verdad de las decisiones de diseño y vive en
> `docs/decisiones/`; aquí solo se lleva la cuenta de en qué issue está cada fase y qué
> hueco queda sin issue, para no perder el hilo entre sesiones. Se actualiza a mano, sin
> issue ni rama propios (documento de diseño vivo), cada vez que se crea o cierra un issue
> de la cadena. Mismo formato que [`ESTADO_ADR049.md`](ESTADO_ADR049.md).

---

## Origen

`ADR-050` — [`docs/decisiones/ADR-050-almacen-documental-privado-por-contenido.md`](../decisiones/ADR-050-almacen-documental-privado-por-contenido.md) — BDDAT, único dueño de los ficheros: almacén privado direccionado por contenido y edición sin acceso al servidor de ficheros. Secuenciación y fases en su §I; consumidores en su §M. La fase 1 absorbió la 2 y la 3 (enmienda del 02/10/2026), así que los issues no se corresponden uno a uno con los números de fase.

## Fases e issues

| Fase | Issue | Qué es | Capa | Estado (09/10/2026) |
|---|---|---|---|---|
| 0 | **#1000** | Prueba de la edición WebDAV en un puesto de la Junta (puerta de la fase 1) | Infra | Cerrado (pasada el 01/10/2026) |
| 0 | **#1001** | Congelar los consumidores del modelo de rutas (`test_1001`) | Test | Cerrado (PR #1003) |
| 1 (absorbe 2 y 3) | **#1007** | Almacén, `ficheros`, módulo de contenido, formatos, subida y descarga, manifiesto y exportador, corte del modelo de carpetas, sustitución con motivo, aviso por hash en el mismo expediente | Backend + frontend | Cerrado (seis PR; el último, #1029, 08/10/2026). Diferido: «Aportar desde otro expediente» (#1033) |
| 2b | **#1008** | «Exportar expediente» (ZIP), exportación automática al finalizar (`ARCHIVO_BASE`), marca de manifiesto pendiente con su señal, `flask manifiestos --verificar`, tareas diarias | Backend + frontend | Abierto. Antes de producción |
| 4 | **#1009** | Plantillas y fragmentos al almacén (`fragmentos`, `generacion_fragmentos`, `plantilla_ref`), subida desde el navegador, retirada del motor de Word, del explorador de plantillas y de `scripts/cliente/` | BD + backend + frontend | Abierto. Antes de producción |
| 5 | **#1010** | Edición del borrador por WebDAV, botón «Editar», sesiones en BD, congelado del borrador al vincular el firmado, confirmación al regenerar un borrador retocado, HTTPS | BD + backend + frontend | Abierto. Al ritmo del despliegue; HTTPS espera a #151 y #330 |
| 6 | **#1011** | PDF para firma generado en el servidor y sincronizado con el borrador | Backend | Abierto. Depende de #330 (Dockerfile con LibreOffice) y de #1010 |
| 7 | **#1012** | Papelera, limpieza del almacén (con conciliación), integridad, parámetros | BD + backend + frontend | Abierto. Al ritmo del despliegue. Depende de #1008 (tareas diarias) |
| — | **#1033** | «Aportar desde otro expediente» y aviso por hash entre expedientes | Backend + frontend | Abierto, aparcado (M5) |
| — | **#1034** | Ampliar los formatos admitidos con muestras reales (KMZ/KML, SHP, DWG, firmas) | Backend | Abierto, aparcado (M5) |

Las fases 2 y 3 no tienen issue propio: las absorbe #1007. Las fases 0-4 y la 2b van antes de producción (ADR-050 §I); la 5, 6 y 7 pueden ir al ritmo del despliegue.

## Despliegue (no es código de esta cadena)

Lo que ADR-050 necesita de fuera y está en otros issues: **#151** (infraestructura de producción: las tres carpetas con sus permisos, cuenta de servicio, LibreOffice en el servidor), **#852** (montaje `soft` del share, ADR-050 §B), **#851** (workers con hilos, el margen de las subidas) y **#330** (entornos, Dockerfile y HTTPS). El proxy con límite de 300 MB (§B) solo vive en el ADR y en #151.

## Sin issue a propósito

- **Buzón por usuario** (`BUZON_BASE/<usuario>/`): aparcado en ADR-050 §A y Alternativa N hasta que haya datos reales de que subir por el navegador ficheros grandes es una fricción. No se abre issue hasta entonces.

## Huecos por definir

- **Regenerar un borrador sustituido a mano pierde los retoques sin avisar.** ADR-050 §F dice que hasta la fase 5 «no hay retoques que perder», pero la sustitución con motivo de #1007 permite el ciclo descargar, retocar y volver a subir, y `regeneracion_escritos` sustituye sin preguntar. La confirmación está ahora en #1010. Pendiente de decidir si se adelanta (la bitácora ya guarda las sustituciones con vía `SUSTITUCION`) o se acepta hasta la fase 5; la fase 5 puede llegar después de producción.
- **Cierre documental de #1007** sin hacer: `MATRIZ_COBERTURA_BDDAT.md` (N009, N021, N077; con `/cobertura`) y las notas de los documentos «Actualizar al implementar» de ADR-050 §M que no se tocaron en los PR de #1007.
- **Orden de las fases 4-7.** El ADR dice qué va antes de producción pero no el orden entre #1008, #1009, #1010, #1011 y #1012. Sin decidir.

## Relación con la cadena de ADR-049

#929 (frontend de las notificaciones) esperaba a «las fases 0-3 de ADR-050» (`ESTADO_ADR049`): cumplido con #1007. Del resto de la cadena solo se cruza con él `ElaborarEditor.jsx`: #929 le añade el selector de destinatario, #1009 el aviso de plantilla desfasada y #1010 el botón «Editar». #922 es independiente.

## Historial de esta tabla

- **09/10/2026** — Creada tras cerrar #1007. Casado de fases e issues, y correcciones de tres issues: #1010 gana el congelado del borrador y la confirmación al regenerar (antes en ninguna fase, #1011 decía que el congelado era de la fase 1) y los nombres de columna del ADR; #1011 deja de atribuir el congelado del borrador a #1007; #1012 gana el paso 5 de §G (conciliación), el enganche de `fecha_borrado` con el manifiesto, el tamaño máximo de 300 MB (decía 500) y los nombres de columna del ADR. Creados #1033 y #1034 para lo diferido de la fase 1.

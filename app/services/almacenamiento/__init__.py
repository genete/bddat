"""Subsistema de almacenamiento (ADR-050 §B; #1007).

Lo único de BDDAT que lee o escribe `ficheros`, `documentos.fichero_ref` y una
`ref`: el resto trabaja con `documentos.id` y pide el contenido por aquí. Las
comprobaciones que dan coherencia al contenido (sellado, bitácora) viven en este
subsistema, y quien escribiera `fichero_ref` por su cuenta se las saltaría. Lo
vigila `tests/test_1007_subsistema_almacenamiento.py`.

Piezas:

- `adaptador`: traduce lo que BDDAT necesita a la API del almacén (hoy, la librería
  `almacen/`). Es el único módulo de `app/` que la importa. Lleva el tiempo límite
  de cada petición y el semáforo de transferencias.
- `contenido`: las operaciones sobre el contenido de un documento (subir, leer,
  comprobar al vincular, servir la descarga).
- `formatos`: qué se puede subir (lista cerrada de §E), detectado por el contenido.
- `nombres`: el saneado del nombre de un fichero que viene de fuera (§C).
- `manifiestos`: un manifiesto por expediente para reconstruir sus carpetas sin
  BDDAT (§H, N009). Lo lee el exportador (`exportador/`, en la raíz del repositorio).

Este `__init__` no importa nada a propósito: `nombres` y `formatos` no necesitan
la aplicación, y `rutas_esftt` los usa mientras viva (hasta el PR 5).
"""

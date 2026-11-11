"""Librería común de los guiones de interfaz (#1106).

- `sesion`:     navegador, login de dos pasos, diario de pasos, capturas y opciones de línea de órdenes.
- `contexto`:   lo que comparten los pasos (sesión + expediente + ids de lo creado) y su estado en disco.
- `arbol`:      lienzo, inspector y despensa; subidas, vínculos, checklist, reloj y plazos.
- `documentos`: los PDF dummy que se suben (los de `scripts/generar_documentos_dummy.py`).
- `pasos`:      piezas reutilizables entre expedientes-tipo (diagnóstico, escrito, ELABORAR, NOTIFICAR, plazos…).
- `alta`:       el formulario de alta.
- `ejecutor`:   `--lista` / `--desde` / `--hasta` / `--nuevo` sobre la lista de pasos de un expediente-tipo.

Nada de esto importa `app`: vale contra cualquier URL, también la de la nube.
"""

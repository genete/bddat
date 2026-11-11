"""Expedientes-tipo por la INTERFAZ: guiones Playwright que tramitan un expediente como lo haría una persona (#1106).

Contraparte de los módulos de `scripts/expedientes_dummy/` (que construyen por la API, con servicios y
endpoints): aquí se rellena el formulario de alta, se crean fases, trámites y tareas desde el árbol, se suben
documentos, se vinculan, se notifica y se mueve el reloj de desarrollo.

- `lib/`: la librería común. No importa `app`: necesita la URL de la aplicación, no la base de datos.
- Una carpeta por expediente-tipo (`analisis_doc_dos_vueltas/`): solo la historia.
- `explorar.py`: mira una ruta (captura y árbol de accesibilidad) para escribir guiones nuevos.

Es una herramienta a demanda, fuera de pytest y de la semilla. Ver `README.md`.
"""

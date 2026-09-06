"""Paquete `scripts` — solo para que la suite pueda importar la semilla (#849).

Los scripts se siguen ejecutando como programas (`python scripts/x.py`); este
fichero no cambia nada de eso. Existe para que `tests/` pueda hacer
`from scripts.semilla_test import CONTRASENA, USUARIOS` y no haya dos copias de
las credenciales de la base de tests: la semilla las define, los tests las leen.
"""

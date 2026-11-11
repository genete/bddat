"""Lo que comparten los pasos de un guion: la sesión de navegador y el expediente sobre el que se actúa.

El estado (qué pasos están hechos y los ids de lo creado) vive en `docs_prueba/ui_dummy/<tipo>/estado.json`: es lo
que permite retomar una ejecución en el primer paso que falta y, con `--nuevo`, reciclar el expediente anterior.
"""
import json

from .arbol import abrir_arbol, inspector, ir_nodo

FICHERO_ESTADO = 'estado.json'


def cargar_estado(carpeta):
    """El estado guardado de la última ejecución, o None si no hay."""
    ruta = carpeta / FICHERO_ESTADO
    return json.loads(ruta.read_text(encoding='utf-8')) if ruta.exists() else None


def guardar_estado(carpeta, estado):
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / FICHERO_ESTADO).write_text(json.dumps(estado, indent=2, ensure_ascii=False), encoding='utf-8')


class Contexto:
    def __init__(self, sesion, opts, carpeta, estado):
        self.s, self.page, self.opts = sesion, sesion.page, opts
        self.url, self.carpeta, self.estado = opts.url, carpeta, estado
        self.insp = inspector(self.page)

    @property
    def id(self):
        """Id interno del expediente (el de las URL), como texto."""
        return str(self.estado['id'])

    @property
    def at(self):
        """El código «AT-N» del expediente."""
        return self.estado['at']

    @property
    def ids(self):
        """Nodo (`tarea-33199`) de lo que ha creado cada paso, por clave."""
        return self.estado.setdefault('ids', {})

    def arbol(self):
        abrir_arbol(self.page, self.url, self.id)

    def ir(self, clave):
        """Abre el inspector (en lectura) sobre el nodo que creó el paso `clave`."""
        nodo = self.ids.get(clave)
        if not nodo:
            raise RuntimeError(f'falta el id de «{clave}»: ejecuta antes el paso que lo crea')
        ir_nodo(self.page, self.url, self.id, nodo)

    def anotar(self, clave, nodo):
        self.ids[clave] = nodo
        print(f'     {clave} = {nodo}')

    def guardar(self):
        guardar_estado(self.carpeta, self.estado)

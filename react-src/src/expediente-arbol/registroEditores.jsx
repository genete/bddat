// registroEditores.jsx — Qué lleva cada nodo del árbol en el inspector (#1047, ADR-053 §C).
//
// `InspectorEdicion` decidía qué pintar debajo de los datos —la Despensa, las acciones propias, «Borrar»— con
// una cadena de banderas (`esAnalizar`, `esSolicitud`…): cada tipo nuevo añadía otra. Aquí cada tipo de nodo
// tiene una entrada que DECLARA lo que lleva, y el contenedor solo la ejecuta. Añadir un tipo es añadir una
// entrada, sin tocar el contenedor.
//
// Forma de una entrada:
//   despensa  { oculta, deshabilitarProducido, ayudaRecepcion }  cómo se comporta la Despensa (todo falso por defecto)
//   borrable  si el nodo admite «Borrar» (además de los permisos y de que su fase no esté cerrada)
//
// `entradaDe` devuelve `null` para los tipos que aún no tienen entrada; el contenedor sigue con sus banderas
// para ellos hasta que se migren (#1047, tipo a tipo).
import { superficieDeNodoTarea } from './superficiesTarea.js'

// Tarea sin superficie propia: la que no figura en `superficiesTarea.js`. Datos comunes, Despensa y «Borrar».
const TAREA_GENERICA = {
  despensa: {},
  borrable: true,
}

// ESPERAR_PLAZO (#766): sin editor propio, salvo la ayuda de la Despensa sobre qué documento es el producido
// cuando en la recepción llegan varios (regla de #764). Es la única tarea cuyo producido es un documento
// recibido de fuera.
const TAREA_ESPERAR_PLAZO = {
  despensa: { ayudaRecepcion: true },
  borrable: true,
}

// La entrada del nodo seleccionado (`nodo` = su entrada en el árbol), o `null` si su tipo aún no está migrado.
export function entradaDe(tipo, nodo, arbol) {
  if (tipo === 'tarea') {
    // ANALIZAR, ELABORAR y NOTIFICAR tienen superficie propia y siguen por las banderas hasta su migración.
    if (superficieDeNodoTarea(arbol, nodo) !== null) return null
    return nodo && nodo.tipo_codigo === 'ESPERAR_PLAZO' ? TAREA_ESPERAR_PLAZO : TAREA_GENERICA
  }
  return null
}

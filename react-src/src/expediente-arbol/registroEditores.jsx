// registroEditores.jsx — Qué lleva cada nodo del árbol en el inspector (#1047, ADR-053 §C).
//
// `InspectorEdicion` decidía qué pintar debajo de los datos —tarjetas propias, la Despensa, las acciones, «Borrar»—
// con una cadena de banderas (`esAnalizar`, `esSolicitud`…): cada tipo nuevo añadía otra. Aquí cada tipo de nodo
// tiene una entrada que DECLARA lo que lleva, y el contenedor solo la ejecuta. Añadir un tipo es añadir una
// entrada, sin tocar el contenedor.
//
// Forma de una entrada (todo es opcional; `entrada()` pone los valores por defecto):
//   tarjetas  [{ clave, render(c) }]            tarjetas de dato propias, tras los datos del nodo: en lectura y en edición
//   acciones  [{ clave, visible(c), render(c) }] acciones propias, solo en edición y en este orden. El separador
//                                                 solo se pinta si alguna es visible
//   modales   [{ clave, render(c) }]            modales del nodo, solo en edición, al final del inspector
//   despensa  { oculta, deshabilitarProducido, ayudaRecepcion }  cómo se comporta la Despensa (todo falso por defecto)
//   borrable  si el nodo admite «Borrar» (además de los permisos y de que su fase no esté cerrada)
//
// `c` es el contexto de la llamada: { tipo, id, nodo, detalle, expedienteId, arbol, modoEdicion } más los hechos de
// `useHechosDelNodo`. Las funciones de una entrada son puras: un hook no puede ir dentro de una entrada (no se
// llamaría siempre), así que lo que depende de un store se calcula en `useHechosDelNodo` y la entrada solo lo lee.
//
// `entradaDe` devuelve `null` para los tipos que aún no tienen entrada; el contenedor sigue con sus banderas
// para ellos hasta que se migren (#1047, tipo a tipo). La clave de cada elemento es la de la entrada, sin el id del
// nodo: dos nodos del mismo tipo comparten componente, igual que antes, y no se pierde lo escrito al cambiar de uno a otro.
import React from 'react'
import { superficieDeNodoTarea } from './superficiesTarea.js'
import {
  TarjetaNotificacionesTramite, AccionNotificacionesTramite, useHayNotificacionesTramite,
} from './components/notificar/NotificacionesTramite.jsx'
import { CertFinInstruccion, CierreSolicitud, ModalInformeFinInstruccion } from './components/AccionesNodo.jsx'

const entrada = (def) => ({ tarjetas: [], acciones: [], modales: [], despensa: {}, borrable: true, ...def })

// Los hechos del nodo que salen de un store de zustand. Se llaman siempre (reglas de los hooks), con el id del nodo
// seleccionado: un id de tarea puede coincidir con el de un trámite, y cada hecho solo lo lee la entrada de su tipo.
export function useHechosDelNodo(id) {
  return {
    hayNotificacionesTramite: useHayNotificacionesTramite(id),
  }
}

// Expediente: sin «Borrar» (el expediente no se borra desde el árbol).
const EXPEDIENTE = entrada({ borrable: false })

const ORGANISMO = entrada({})

// Solicitud: la bisagra instrucción → resolución (#827, ADR-043 §E) y el cierre de la solicitud (#996, ADR-049 §F),
// en la zona de acciones y siempre visibles (cada componente decide si tiene algo que decir), y el modal con el
// informe de la revisión cuando no se consolida.
const SOLICITUD = entrada({
  acciones: [
    { clave: 'fin-instruccion', visible: () => true, render: () => <CertFinInstruccion /> },
    { clave: 'cierre-solicitud', visible: () => true, render: () => <CierreSolicitud /> },
  ],
  modales: [{ clave: 'informe-fin-instruccion', render: () => <ModalInformeFinInstruccion /> }],
})

// Notificaciones del trámite (#929, ADR-051 §D): a quién falta notificar (tarjeta de dato, en los dos modos) y el
// botón de añadirlas (acción, solo en edición). Si el trámite no notifica a nadie según el catálogo, ni la tarjeta
// ni el botón se pintan.
const TRAMITE = entrada({
  tarjetas: [{
    clave: 'notificaciones',
    render: (c) => <TarjetaNotificacionesTramite expedienteId={c.expedienteId} tramiteId={Number(c.id)} />,
  }],
  acciones: [{
    clave: 'notificaciones',
    visible: (c) => c.hayNotificacionesTramite,
    render: (c) => <AccionNotificacionesTramite expedienteId={c.expedienteId} tramiteId={Number(c.id)} />,
  }],
})

// Tarea sin superficie propia: la que no figura en `superficiesTarea.js`. Datos comunes, Despensa y «Borrar».
const TAREA_GENERICA = entrada({})

// ESPERAR_PLAZO (#766): sin editor propio, salvo la ayuda de la Despensa sobre qué documento es el producido
// cuando en la recepción llegan varios (regla de #764). Es la única tarea cuyo producido es un documento
// recibido de fuera.
const TAREA_ESPERAR_PLAZO = entrada({ despensa: { ayudaRecepcion: true } })

const POR_TIPO = { expediente: EXPEDIENTE, solicitud: SOLICITUD, organismo: ORGANISMO, tramite: TRAMITE }

// La entrada del nodo seleccionado (`nodo` = su entrada en el árbol), o `null` si su tipo aún no está migrado.
export function entradaDe(tipo, nodo, arbol) {
  if (tipo === 'tarea') {
    // ANALIZAR, ELABORAR y NOTIFICAR tienen superficie propia y siguen por las banderas hasta su migración.
    if (superficieDeNodoTarea(arbol, nodo) !== null) return null
    return nodo && nodo.tipo_codigo === 'ESPERAR_PLAZO' ? TAREA_ESPERAR_PLAZO : TAREA_GENERICA
  }
  return Object.hasOwn(POR_TIPO, tipo) ? POR_TIPO[tipo] : null
}

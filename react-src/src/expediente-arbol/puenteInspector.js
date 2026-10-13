// puenteInspector.js — alimenta el marco único del shell con el estado del árbol (ADR-053 §A,
// #1042).
//
// La barra del inspector (cabecera + Editar / Guardar / Cancelar-Cerrar) la pinta el shell, no
// React. Este hook le pasa, por `AppInspector.setFrame`, lo que necesita: datos planos
// (tipo, título, estado, candado, semáforo) y el estado del borrador (`hayCambios`,
// `guardando`), más los tres gestos, que ejecutan las acciones del store.
//
// El interior no cambia: «Guardar» solo cubre lo que cuelga del borrador global (los campos
// directos del nodo, ADR-023 §5 bis rev. 2026-07-29, #688). Lo que cada contenedor bespoke
// (ANALIZAR, ELABORAR, NOTIFICAR) persiste por su cuenta y de inmediato no toca el borrador y
// no enciende «Guardar», como hasta ahora.
import React from 'react'
import { useArbolStore, selectHayCambios } from './store.js'
import { puedeEditarNodo } from '../shared/auth.js'
import { estaSellado } from './sellado.js'
import { SIGNIFICADO } from './components/nodos/Semaforo.jsx'
import { buscarNodo, tituloNodo, ETIQUETA_TIPO } from './components/Inspector.jsx'

// Los gestos leen el store en el momento de pulsar (no capturan estado de un render), así que
// el shell puede conservarlos aunque el descriptor se repita.
const GESTOS = {
  onEditar: () => {
    const { seleccion, entrarEdicion } = useArbolStore.getState()
    if (seleccion) entrarEdicion(seleccion)
  },
  // `() => guardar()` y no `guardar` a secas: desde #765 el primer argumento de `guardar` es la
  // justificación del escape, y pasarle el evento del clic lo convertiría en un bypass
  // involuntario.
  onGuardar: () => useArbolStore.getState().guardar(),
  // El mismo `cancelar` para «Cancelar» y «Cerrar»: solo cambia el rótulo según haya borrador
  // vivo (lo pone el shell). La confirmación en sucio la impone el bloqueo de light-dismiss
  // (ADR-023 §5 bis), no un diálogo aparte.
  onSalir: () => useArbolStore.getState().cancelar(),
}

export function usePuenteInspector() {
  const seleccion  = useArbolStore((s) => s.seleccion)
  const arbol      = useArbolStore((s) => s.arbol)
  const modoEdicion = useArbolStore((s) => s.modoEdicion)
  const guardando  = useArbolStore((s) => s.guardando)
  const hayCambios = useArbolStore(selectHayCambios)
  const ultima = React.useRef(null)

  React.useEffect(() => {
    if (!window.AppInspector || !seleccion) { ultima.current = null; return }
    const nodo = buscarNodo(arbol, seleccion)
    const sem = nodo && nodo.semaforo
    // Sellado (#720, ADR-036): Editar sigue disponible sobre la propia fase cerrada —es el
    // único camino hasta el botón "Reabrir fase" del editor— pero no sobre un trámite/tarea
    // cuya fase está cerrada, donde el backend rechazaría el guardado.
    const puedeEditar = puedeEditarNodo(seleccion.tipo) &&
                        (seleccion.tipo === 'fase' || !estaSellado(arbol, seleccion))
    const plano = {
      modo: modoEdicion ? 'editar' : 'ver',
      tipo: ETIQUETA_TIPO[seleccion.tipo] || seleccion.tipo,
      titulo: tituloNodo(seleccion.tipo, nodo) || '—',
      estado: (nodo && nodo.estado) || '',
      // Candado (#720, ADR-036): solo la propia fase lleva el indicador — es el único nivel
      // con un acto de cierre formal (documento_resultado_id); trámite/tarea quedan cubiertos
      // transitivamente, sin badge propio.
      candado: seleccion.tipo === 'fase' && !!nodo && nodo.estado === 'FINALIZADA',
      semaforo: sem ? { color: sem.color, titulo: SIGNIFICADO[sem.color] || '' } : null,
      puedeEditar,
      hayCambios,
      guardando,
    }
    // El borrador cambia con cada tecla; el descriptor, casi nunca: solo se empuja si difiere.
    const clave = JSON.stringify(plano)
    if (clave === ultima.current) return
    ultima.current = clave
    window.AppInspector.setFrame({ ...plano, ...GESTOS })
  }, [seleccion, arbol, modoEdicion, guardando, hayCambios])
}

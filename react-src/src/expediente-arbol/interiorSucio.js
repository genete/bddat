// interiorSucio.js — un bloque del inspector avisa al marco de que lleva texto sin guardar (#1055).
//
// Algunos bloques guardan por su cuenta, con su propio botón (ítem técnico y requerimientos de
// ANALIZAR, registro y destinatario de NOTIFICAR, destinatario de ELABORAR), y su texto no pasa por
// el borrador del nodo. Sin este aviso, la barra del marco seguía diciendo «Cerrar» mientras el
// usuario escribía, y pulsarlo tiraba lo escrito sin avisar.
//
// Uso: `useInteriorSucio('tecnico-12', 'Verificación técnica', hayCambios)`. Mientras `sucio` sea
// cierto el marco dice «Cancelar», el «Guardar» de la barra pide decisión antes de tirar el texto y
// el cierre de la pestaña avisa. El bloque se desapunta solo al quedar limpio o al desmontarse
// (guardar, salir de la edición, cambiar de nodo). `rotulo` es lo que se le enseña al usuario en
// ese aviso: dos bloques con el mismo rótulo salen una sola vez.
import React from 'react'
import { useArbolStore } from './store.js'

export function useInteriorSucio(id, rotulo, sucio) {
  const marcar = useArbolStore((s) => s.marcarInteriorSucio)
  React.useEffect(() => {
    marcar(id, sucio ? rotulo : null)
    return () => marcar(id, null)
  }, [marcar, id, rotulo, sucio])
}

// superficiesTarea.js — Qué superficie de trabajo propia tiene una tarea (#1043, ADR-053 §C).
//
// Lo que el inspector enseña de una tarea no depende solo de su tipo, sino del tipo de tarea y del
// trámite en que está: el ANALIZAR de ANALISIS_DOCUMENTAL y de REQUERIMIENTO_SUBSANACION lleva las
// secciones extendidas y el de CONSULTA_SEPARATA no; el ELABORAR pinta el destinatario solo si el
// trámite lo tiene; el NOTIFICAR cambia si va al solicitante. Cada superficie decide esas
// variantes por dentro (con la bandera de su propio endpoint); aquí se decide solo QUÉ SUPERFICIE
// entra, y con ella qué tareas son «genéricas».
//
// Una tarea es genérica cuando su combinación (tipo de tarea, trámite) NO figura en la tabla:
// la ausencia es lo que decide, no la presencia, de modo que un tipo de tarea o un trámite nuevo
// cae en el diseño genérico (datos comunes + Despensa + Borrar) sin tocar nada, aunque la semilla
// no tenga ningún caso (hoy solo ESPERAR_PLAZO). Es el germen del registro de editores de #1047.
//
// Para una excepción por trámite: `porTramite: { CODIGO_TRAMITE: 'SUPERFICIE' | null }`; `null` dice
// que en ese trámite la tarea es genérica aunque su tipo tenga superficie.
export const SUPERFICIES_TAREA = {
  ANALIZAR:  { defecto: 'ANALIZAR',  porTramite: {} },
  ELABORAR:  { defecto: 'ELABORAR',  porTramite: {} },
  NOTIFICAR: { defecto: 'NOTIFICAR', porTramite: {} },
}

// Código del tipo de trámite al que pertenece la tarea, buscado en el árbol ya cargado.
export function codigoTramiteDeTarea(arbol, tareaId) {
  for (const sol of (arbol && arbol.solicitudes) || []) {
    for (const fase of sol.fases || []) {
      for (const tr of fase.tramites || []) {
        if ((tr.tareas || []).some((ta) => ta.id === tareaId)) return tr.tipo_codigo || null
      }
    }
  }
  return null
}

// Nombre de la superficie propia de la combinación, o null si la tarea es genérica.
export function superficieDeTarea(tareaCodigo, tramiteCodigo) {
  // Solo claves propias: un código que coincida con una propiedad de `Object` («constructor»…)
  // no es una entrada de la tabla.
  const propia = (obj, clave) => !!clave && Object.prototype.hasOwnProperty.call(obj, clave)
  if (!propia(SUPERFICIES_TAREA, tareaCodigo)) return null
  const entrada = SUPERFICIES_TAREA[tareaCodigo]
  const porTramite = entrada.porTramite || {}
  if (propia(porTramite, tramiteCodigo)) return porTramite[tramiteCodigo]
  return entrada.defecto
}

// La superficie de la tarea del árbol (`nodo` = su entrada en el árbol), o null.
export function superficieDeNodoTarea(arbol, nodo) {
  if (!nodo) return null
  return superficieDeTarea(nodo.tipo_codigo, codigoTramiteDeTarea(arbol, nodo.id))
}

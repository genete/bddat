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
// Cómo se elige la superficie de una entrada, en este orden:
//   1. `porTramite: { CODIGO_TRAMITE: 'SUPERFICIE' | null }`; `null` dice que en ese trámite la tarea
//      es genérica aunque su tipo tenga superficie.
//   2. `variante(nodo)`: el nodo de la tarea en el árbol dice qué variante es, con un dato que pone
//      el backend (ANALIZAR: `analisis_extendido`, que sale de la única lista de trámites con
//      secciones extendidas, `consolidacion_defectos.TRAMITES_CON_SECCIONES_ANALISIS`; el front no
//      la repite). Devuelve el nombre de la superficie o `undefined` para quedarse con el defecto.
//   3. `defecto`.
//
// Las dos variantes de ANALIZAR ya usan el diseño de datos de la tarea: su análisis son tarjetas de
// datos —en lectura y en edición— y producir el diagnóstico, una acción de la zona de acciones.
// `ANALIZAR` es el de los trámites con secciones extendidas (ANALISIS_DOCUMENTAL,
// REQUERIMIENTO_SUBSANACION) y `ANALIZAR_SIMPLE` el de los demás. ELABORAR y NOTIFICAR siguen con su
// editor hasta que la fase 3 las migre.
export const SUPERFICIES_TAREA = {
  ANALIZAR: {
    defecto: 'ANALIZAR',
    // Sin el dato (un árbol antiguo) se queda en la variante con secciones, que si el endpoint dice
    // que no las hay no las pinta (`AnalisisExtendido`).
    variante: (nodo) => (nodo && nodo.analisis_extendido === false ? 'ANALIZAR_SIMPLE' : undefined),
    porTramite: {},
  },
  ELABORAR:  { defecto: 'ELABORAR',  porTramite: {} },
  NOTIFICAR: { defecto: 'NOTIFICAR', porTramite: {} },
}

// Superficies que ya usan el diseño de datos de la tarea (las demás siguen con su editor).
const SUPERFICIES_CON_DISENO = new Set(['ANALIZAR', 'ANALIZAR_SIMPLE'])

// ¿Pinta la tarea la zona de datos común? Sí si es genérica (sin superficie) o su superficie ya migró.
export function tieneDisenoTarea(superficie) {
  return !superficie || SUPERFICIES_CON_DISENO.has(superficie)
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

// Nombre de la superficie propia de la combinación, o null si la tarea es genérica. `nodo` es la
// entrada de la tarea en el árbol (solo lo leen las entradas con `variante`).
export function superficieDeTarea(tareaCodigo, tramiteCodigo, nodo) {
  // Solo claves propias: un código que coincida con una propiedad de `Object` («constructor»…)
  // no es una entrada de la tabla.
  const propia = (obj, clave) => !!clave && Object.prototype.hasOwnProperty.call(obj, clave)
  if (!propia(SUPERFICIES_TAREA, tareaCodigo)) return null
  const entrada = SUPERFICIES_TAREA[tareaCodigo]
  const porTramite = entrada.porTramite || {}
  if (propia(porTramite, tramiteCodigo)) return porTramite[tramiteCodigo]
  const variante = entrada.variante ? entrada.variante(nodo) : undefined
  return variante === undefined ? entrada.defecto : variante
}

// La superficie de la tarea del árbol (`nodo` = su entrada en el árbol), o null.
export function superficieDeNodoTarea(arbol, nodo) {
  if (!nodo) return null
  return superficieDeTarea(nodo.tipo_codigo, codigoTramiteDeTarea(arbol, nodo.id), nodo)
}

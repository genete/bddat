// API de la isla del árbol, sobre shared/api.js (ADR-016 §16).
//
// OJO: la ruta del endpoint es PLURAL (/api/expedientes/...), confirmado en
// app/routes/api_expedientes.py:451. El plan/ADR la citan a veces en singular.
import { api } from '../shared/api.js'

// S2 (lectura): árbol completo de dominio (expediente → solicitudes → … → tareas).
export function getArbol(expedienteId) {
  return api.get(`/api/expedientes/${expedienteId}/arbol`)
}

// --- Esqueletos S3 (no usados en S2) ------------------------------------------

// Detalle lazy de un nodo para el inspector (§16). `opts` permite pasar { signal }
// para cancelar la petición anterior al cambiar de selección (AbortController).
export function getNodo(expedienteId, tipo, nodoId, opts) {
  return api.get(`/api/expedientes/${expedienteId}/nodo/${tipo}/${nodoId}`, opts)
}

// Tipos de hijo creables bajo un nodo: despensa + menú contextual (§16/§8).
export function getTiposCreables(expedienteId, tipo, nodoId) {
  return api.get(`/api/expedientes/${expedienteId}/nodo/${tipo}/${nodoId}/tipos-creables`)
}

// Esquema editable del nodo (editor del inspector, S3b-1).
export function getEditable(expedienteId, tipo, nodoId) {
  return api.get(`/api/expedientes/${expedienteId}/nodo/${tipo}/${nodoId}/editable`)
}

// Editar campos de un nodo (PATCH, S3b-1).
export function patchNodo(expedienteId, tipo, nodoId, body) {
  return api.patch(`/api/expedientes/${expedienteId}/nodo/${tipo}/${nodoId}`, body)
}

// Crear hijo bajo un nodo (POST, S3b-2). Respuesta: {ok, ids:[...], advertencia?}.
export function postHijo(expedienteId, padreTipo, padreId, body) {
  return api.post(`/api/expedientes/${expedienteId}/nodo/${padreTipo}/${padreId}/hijos`, body)
}

// Pool de documentos del expediente (GET, S3b-3). Respuesta: {documentos:[{id,nombre,
// tipo_doc,tipo_doc_codigo,fecha}]}. tipo_doc_codigo (#712) permite filtrar client-side
// (p.ej. JUSTIFICANTE_* en el desplegable de NotificarEditor).
export function getPool(expedienteId) {
  return api.get(`/api/expedientes/${expedienteId}/pool`)
}

// Borrar un nodo (DELETE, S3b-4). Respuesta éxito: {ok:true} 200. Motor: {motivo,url_norma} 422.
export function deleteNodo(expedienteId, tipo, nodoId) {
  return api.delete(`/api/expedientes/${expedienteId}/nodo/${tipo}/${nodoId}`)
}

// Reabre una fase cerrada (POST, #720, ADR-036). body: {justificacion} — obligatoria
// siempre. Respuesta éxito: {ok:true} 200. Bloqueo (422, puede_escapar:false): solicitud
// ya resuelta y notificada — puerta cerrada.
export function postReabrirFase(expedienteId, faseId, justificacion) {
  return api.post(`/api/expedientes/${expedienteId}/nodo/fase/${faseId}/reabrir`, { justificacion })
}

// "Enviar consultas pendientes" (POST, ADR-042 §C, #396 bloque 5): crea una
// CONSULTA_SEPARATA por cada organismo vía consulta que aún no tenga una.
// Acción de fase en modo edición — incremental e idempotente por construcción,
// pensada para pulsarse N veces (segunda ronda incluida). Respuesta éxito:
// {ok:true, ids:[...]} 201 (`ids` vacío si no había pendientes). Bloqueo: 422.
export function postEnviarConsultas(expedienteId, faseId) {
  return api.post(`/api/expedientes/${expedienteId}/nodo/fase/${faseId}/organismos/enviar-consultas`, {})
}

// Contenedor de la tarea ANALIZAR (#442). Respuesta: {resultado, documento_producido,
// secciones_extendidas, defectos_consolidado, completo}.
export function getAnalizar(expedienteId, tareaId) {
  return api.get(`/api/expedientes/${expedienteId}/nodo/tarea/${tareaId}/analizar`)
}

// Produce el documento de diagnóstico (POST, #442/#677). body: {resultado?, justificacion?}
// — `resultado` se ignora en ANALIZAR extendido (derivado server-side, ADR-033 §3).
// Respuesta éxito: {ok:true, documento:{id,nombre,tipo_doc,fecha}} 200.
// Bloqueo (ya producido / incompleto sin justificación): {error, motivo?, defectos_consolidado?} 422.
export function postAnalizar(expedienteId, tareaId, body) {
  return api.post(`/api/expedientes/${expedienteId}/nodo/tarea/${tareaId}/analizar`, body)
}

// Revierte el diagnóstico producido (DELETE, #678, ADR-033 §5): vuelve a
// "Borrador defectos". Respuesta éxito: {ok:true} 200.
// Bloqueo (422): {error, motivo, puede_escapar} — sin producido, consumido por otra
// tarea, o superado dentro de la cadena de subsanación (#714). `puede_escapar:false`
// es puerta cerrada (consumido, o requerimiento ya notificado al titular);
// `true` admite reintento con `justificacion`, que queda en bitácora.
export function revertirDiagnostico(expedienteId, tareaId, justificacion) {
  const url = `/api/expedientes/${expedienteId}/nodo/tarea/${tareaId}/analizar`
  return justificacion ? api.delete(url, { body: { justificacion } }) : api.delete(url)
}

// Guarda solo `notas` de una tarea (PATCH, #677) — vía estrecha que NO toca los
// vínculos documentales. Desde #688 la usa el propio `guardar()` del store cuando
// el borrador solo difiere en `notas` (ver store.js). Respuesta: {ok:true, notas}.
export function guardarNotas(expedienteId, tareaId, notas) {
  return api.patch(`/api/expedientes/${expedienteId}/nodo/tarea/${tareaId}/notas`, { notas })
}

// Check documental (#495): vincula/desvincula un documento del pool a un requisito.
// Respuesta ambas: {ok:true, checklist_documental:[...]}.
export function vincularRequisitoDocumental(expedienteId, tareaId, requisitoId, documentoId) {
  return api.post(
    `/api/expedientes/${expedienteId}/nodo/tarea/${tareaId}/requisitos-documentales/${requisitoId}`,
    { documento_id: documentoId },
  )
}

// `justificacion` (#724): solo hace falta cuando el requisito ya se exigió al
// titular en una vuelta notificada anterior y desvincular lo devuelve a
// pendiente — sin eso, la mutación es libre (vincular nunca la necesita, nunca
// crea un defecto nuevo). Sin `justificacion`, 422 {motivo, puede_escapar:true}.
export function desvincularRequisitoDocumental(expedienteId, tareaId, requisitoId, justificacion) {
  const url = `/api/expedientes/${expedienteId}/nodo/tarea/${tareaId}/requisitos-documentales/${requisitoId}`
  return justificacion ? api.delete(url, { body: { justificacion } }) : api.delete(url)
}

// Check técnico (#581): registra el veredicto (texto + cubierto) de un ítem técnico.
// `body` puede incluir `justificacion` (#724) si un guardado previo devolvió 422
// {puede_escapar:true} — el ítem ya se exigió al titular en una vuelta notificada
// y este guardado lo vuelve a marcar "no cumple".
// Respuesta: {ok:true, checklist_tecnico:[...]}.
export function guardarCoberturaTecnica(expedienteId, tareaId, itemTecnicoId, body) {
  return api.post(
    `/api/expedientes/${expedienteId}/nodo/tarea/${tareaId}/coberturas-tecnicas/${itemTecnicoId}`,
    body,
  )
}

// Selector de requerimientos (#440): estado inicial del panel shuttle (catálogo +
// selección). La selección es por solicitud (#679, ADR-033 §7) — continua entre
// vueltas de subsanación, aunque la URL cuelgue de una tarea concreta.
export function getRequerimientos(expedienteId, tareaId) {
  return api.get(`/api/expedientes/${expedienteId}/nodo/tarea/${tareaId}/requerimientos`)
}

// Sustituye la lista completa de requerimientos_tarea de la solicitud en una sola llamada.
// body: {items: [{catalogo_requerimientos_id, texto_libre, resuelto}, ...], justificacion?}.
// `justificacion` (#724): solo hace falta si el guardado devolvió 422
// {puede_escapar:true} — alguno de los ítems ya resueltos vuelve a quedar
// pendiente (o desaparece) y ya se había exigido al titular en una vuelta
// notificada anterior. El motivo del 422 ya trae listados todos los afectados.
export function postRequerimientos(expedienteId, tareaId, items, justificacion) {
  const body = justificacion ? { items, justificacion } : { items }
  return api.post(`/api/expedientes/${expedienteId}/nodo/tarea/${tareaId}/requerimientos`, body)
}

// Crea una entrada nueva en catalogo_requerimientos desde el shuttle ("Guardar en catálogo").
// Exige `gestionar_catalogo_requerimientos` además de `gestionar_tarea` (#684): es alta en el
// catálogo maestro, mismo permiso que el CRUD de #593. Devuelve 403 a TRAMITADOR/ADMINISTRATIVO,
// a quienes la UI ya no les ofrece la casilla operativa.
export function crearRequerimientoCatalogo(expedienteId, tareaId, texto, categoria) {
  return api.post(
    `/api/expedientes/${expedienteId}/nodo/tarea/${tareaId}/requerimientos/catalogo`,
    { texto, categoria },
  )
}

// Propone al Supervisor un alta en el catálogo ("Solicitar guardado en catálogo", #28).
// Endpoint distinto del anterior a propósito: aquel es escritura directa en el catálogo
// maestro y sigue siendo exclusivo de quien puede curarlo; este crea un mensaje interno y
// no toca el catálogo. Solo exige `gestionar_tarea` — quien no puede curar es justo su
// destinatario.
export function solicitarAltaCatalogo(expedienteId, tareaId, texto, categoria) {
  return api.post(
    `/api/expedientes/${expedienteId}/nodo/tarea/${tareaId}/requerimientos/catalogo/solicitar`,
    { texto, categoria },
  )
}

// Generación de escritos (#167/#608) — Blueprint aparte (/api/escritos), no bajo
// /api/expedientes. Plantillas ESFTT compatibles con la tarea. Respuesta:
// {ok, plantillas:[{id, nombre, variante, descripcion, especificidad}]}.
export function getEscritosPlantillas(tareaId) {
  return api.get(`/api/escritos/plantillas?tarea_id=${tareaId}`)
}

// Preview de campos + nombre/ruta propuestos antes de generar.
// Respuesta: {ok, campos, nombre_propuesto, ruta_destino}.
export function getEscritosPreview(plantillaId, tareaId) {
  return api.get(`/api/escritos/preview?plantilla_id=${plantillaId}&tarea_id=${tareaId}`)
}

// Contenedor de la tarea NOTIFICAR (#657/#658, ADR-034). Respuesta: {notificacion:
// {canal, identificador_envio, fecha_puesta_disposicion, resultado, fecha_resultado,
// numero_intento, observaciones, documento_id}|null, documento_producido:{id,nombre}|null}.
export function getNotificar(expedienteId, tareaId) {
  return api.get(`/api/expedientes/${expedienteId}/nodo/tarea/${tareaId}/notificar`)
}

// "Registrar envío" (camino A, opcional): body {canal, identificador_envio?,
// fecha_puesta_disposicion}. Upsert por tarea_id — no toca resultado/fecha_resultado.
export function postNotificar(expedienteId, tareaId, body) {
  return api.post(`/api/expedientes/${expedienteId}/nodo/tarea/${tareaId}/notificar`, body)
}

// "Registrar notificación" (camino B manual): body {resultado, fecha_resultado,
// numero_intento, observaciones?, documento_id?}. 422 si no hay puesta a disposición
// registrada todavía. `documento_id` (#712, acto 3): vincula ese documento del pool
// como Producido en el mismo acto — ver docstring del endpoint (sustituye al anterior
// si lo había). Respuesta: {ok, notificacion, advertencia?} — advertencia si el cotejo
// de remesa o canal no coincide con lo ya registrado (no bloqueante).
export function patchNotificar(expedienteId, tareaId, body) {
  return api.patch(`/api/expedientes/${expedienteId}/nodo/tarea/${tareaId}/notificar`, body)
}

// Parseo transitorio del justificante (multipart, sin persistir nada) para
// autorrellenar "Registrar puesta a disposición" — el usuario verifica/corrige
// antes de confirmar. Respuesta: el .to_dict() del parser (incluye `reconocido`, fechas ISO).
export function postNotificarParsear(expedienteId, tareaId, fichero) {
  const formData = new FormData()
  formData.append('fichero', fichero)
  return api.post(`/api/expedientes/${expedienteId}/nodo/tarea/${tareaId}/notificar/parsear`, formData)
}

// Preview del justificante DEFINITIVO ya en el pool (#712, acto 1 — desplegable de
// "Registrar notificación"): a diferencia de postNotificarParsear, aquí el documento
// ya existe (se pasa documento_id, no fichero) y se lee de disco en el servidor. Sin
// persistir nada. Respuesta: {reconocido:false, canal} si el canal no tiene parser
// (BANDEJA/SIR/POSTAL) o el PDF no se reconoce; si no, el .to_dict() del parser + canal.
export function postNotificarParsearDocumento(expedienteId, tareaId, documentoId) {
  return api.post(
    `/api/expedientes/${expedienteId}/nodo/tarea/${tareaId}/notificar/parsear_documento`,
    { documento_id: documentoId },
  )
}

// Genera el .docx y lo guarda en disco + pool (#608: asignar_doc_producido siempre
// false — el .docx es un auxiliar de trabajo, no dispara cambio de estado de la
// tarea; el ciclo BORRADOR_FIRMA/firmado se gestiona aparte vía Despensa).
// El draft de la tarea es único (#730): si ya existe y hace falta decisión del
// usuario (colisión de nombre o sustitución de contenido) no escribe nada y
// devuelve {ok, requiere_confirmacion:true, caso, colision_nombre,
// documento_existente_id} — ver postEscritosGenerarConfirmar. Si no hace
// falta decisión: {ok, caso, nombre_fichero, ruta, doc_id, uri_explorador}.
export function postEscritosGenerar(plantillaId, tareaId, nombreFichero) {
  return api.post('/api/escritos/generar', {
    plantilla_id: plantillaId,
    tarea_id: tareaId,
    nombre_fichero: nombreFichero,
    registrar_pool: true,
    asignar_doc_producido: false,
  })
}

// Segundo paso de la regeneración (#730): ejecuta la decisión tomada en el
// popup correspondiente al `caso` devuelto por postEscritosGenerar.
// decision: 'continuar' | 'cancelar' | 'renombrar_nuevo' | 'renombrar_existente'.
// Respuesta: {ok, cancelado:true} si decision='cancelar', si no la misma
// forma que postEscritosGenerar cuando no requiere confirmación.
export function postEscritosGenerarConfirmar(plantillaId, tareaId, nombreFichero, decision) {
  return api.post('/api/escritos/generar/confirmar', {
    plantilla_id: plantillaId,
    tarea_id: tareaId,
    nombre_fichero: nombreFichero,
    decision,
  })
}

// Subida inline desde la Despensa (#367): reutiliza el mismo endpoint multipart
// del pool (ADR-032/#666, app/modules/expedientes/routes.py:pool_subir_documento).
// Un solo fichero — la Despensa solo hace staging de un doc pendiente a la vez.
// Nota de URL: apunta a /expedientes/... (blueprint `expedientes`, no /api) —
// misma ruta que ya usa pool_documentos.html; no se corrige aquí (fuera de
// alcance de #367 tocar la URL de un endpoint con otro consumidor).
export function subirDocumentoPool(expedienteId, fichero, metadatos) {
  const formData = new FormData()
  formData.append('ficheros', fichero)
  formData.append('metadatos', JSON.stringify([metadatos]))
  return api.post(`/expedientes/${expedienteId}/documentos/subir`, formData)
}

// Sugerencia de tipo_doc_id/asunto para el formulario de subida inline (#367).
// Respuesta: {tipo_doc_id, asunto} | {tipo_doc_id:null, asunto:null} si no hay
// coincidencia exacta y no ambigua en el catálogo.
export function getSugerenciaDocumento(expedienteId, tareaId) {
  return api.get(`/api/expedientes/${expedienteId}/nodo/tarea/${tareaId}/sugerencia_documento`)
}

// Catálogo de tipos de documento para el <select> del formulario de subida (#367).
export function getTiposDocumento() {
  return api.get('/api/tipos-documento?limit=100')
}

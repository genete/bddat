// arbolMock.js — árbol de ejemplo para `npm run dev` standalone (andamiaje desechable).
//
// Fiel al contrato de app/services/arbol_expediente.py (ADR-016 §16). NO es AT-2009
// exacto: solo ejercita layout (varias solicitudes/fases/trámites, tareas en columna),
// estados mixtos (para probar "Colapsar finalizados") y los tipos de tarea con sus
// decoradores (ESPERAR_PLAZO con plazo, NOTIFICAR con resultado, doc-dots).
// La verificación real va contra el endpoint Flask con AT-2009 (id=9).

const aggVacio = () => ({
  plazos_vencidos: 0, plazos_proximos: 0, plazos_en_plazo: 0, pendientes_notificar: 0,
})

export const ARBOL_MOCK = {
  expediente: {
    tipo: 'expediente',
    id: 9,
    codigo: 'AT-2009',
    titular: 'Endesa Distribución S.L.U.',
    responsable: 'CLG',
    tipo_expediente: 'Línea de Alta Tensión',
  },
  solicitudes: [
    {
      tipo: 'solicitud',
      id: 101,
      siglas: 'AAP',
      descripcion: 'Autorización Administrativa Previa',
      estado: 'EN_TRAMITE',
      fecha_presentacion: '2024-02-10',
      agregados: { plazos_vencidos: 1, plazos_proximos: 1, plazos_en_plazo: 0, pendientes_notificar: 1 },
      fases: [
        {
          tipo: 'fase',
          id: 201,
          tipo_codigo: 'INFORMACION_PUBLICA',
          nombre: 'Información Pública',
          estado: 'FINALIZADA',
          resultado: 'FAVORABLE',
          agregados: aggVacio(),
          tramites: [
            {
              tipo: 'tramite',
              id: 301,
              tipo_codigo: 'ANUNCIO_BOJA',
              nombre: 'Anuncio en BOJA',
              estado: 'FINALIZADO',
              agregados: aggVacio(),
              tareas: [
                {
                  tipo: 'tarea', id: 401, tipo_codigo: 'ELABORAR', nombre: 'Elaborar anuncio',
                  estado: 'EJECUTADA',
                  doc_consumido: { presente: false, count: 0 },
                  doc_producido: { presente: true, count: 1 },
                  plazo: null, resultado: null,
                },
                {
                  tipo: 'tarea', id: 402, tipo_codigo: 'NOTIFICAR', nombre: 'Publicar en BOJA',
                  estado: 'EJECUTADA',
                  doc_consumido: { presente: true, count: 1 },
                  doc_producido: { presente: true, count: 1 },
                  plazo: null, resultado: 'CORRECTA',
                },
              ],
            },
          ],
        },
        {
          tipo: 'fase',
          id: 202,
          tipo_codigo: 'RESOLUCION',
          nombre: 'Resolución',
          estado: 'EN_CURSO',
          resultado: null,
          agregados: { plazos_vencidos: 1, plazos_proximos: 1, plazos_en_plazo: 0, pendientes_notificar: 1 },
          tramites: [
            {
              tipo: 'tramite',
              id: 302,
              tipo_codigo: 'INFORME_TECNICO',
              nombre: 'Informe técnico',
              estado: 'EN_CURSO',
              agregados: { plazos_vencidos: 0, plazos_proximos: 1, plazos_en_plazo: 0, pendientes_notificar: 0 },
              tareas: [
                {
                  tipo: 'tarea', id: 403, tipo_codigo: 'ANALIZAR', nombre: 'Analizar alegaciones',
                  estado: 'EN_CURSO',
                  doc_consumido: { presente: true, count: 2 },
                  doc_producido: { presente: false, count: 0 },
                  plazo: null, resultado: null,
                },
                {
                  tipo: 'tarea', id: 404, tipo_codigo: 'ESPERAR_PLAZO', nombre: 'Plazo de alegaciones',
                  estado: 'EN_CURSO',
                  doc_consumido: { presente: false, count: 0 },
                  doc_producido: { presente: false, count: 0 },
                  plazo: { estado: 'PROXIMO_VENCER', fecha_limite: '2026-06-05', dias_restantes: 6 },
                  resultado: null,
                },
              ],
            },
            {
              tipo: 'tramite',
              id: 303,
              tipo_codigo: 'RESOLUCION_AAP',
              nombre: 'Resolución AAP',
              estado: 'PLANIFICADO',
              agregados: { plazos_vencidos: 1, plazos_proximos: 0, plazos_en_plazo: 0, pendientes_notificar: 1 },
              tareas: [
                {
                  tipo: 'tarea', id: 405, tipo_codigo: 'ELABORAR', nombre: 'Elaborar resolución',
                  estado: 'PLANIFICADA',
                  doc_consumido: { presente: false, count: 0 },
                  doc_producido: { presente: false, count: 0 },
                  plazo: null, resultado: null,
                },
                {
                  tipo: 'tarea', id: 406, tipo_codigo: 'ESPERAR_PLAZO', nombre: 'Plazo de resolución',
                  estado: 'EN_CURSO',
                  doc_consumido: { presente: false, count: 0 },
                  doc_producido: { presente: false, count: 0 },
                  plazo: { estado: 'VENCIDO', fecha_limite: '2026-05-20', dias_restantes: -10 },
                  resultado: null,
                },
                {
                  tipo: 'tarea', id: 407, tipo_codigo: 'NOTIFICAR', nombre: 'Notificar resolución',
                  estado: 'PLANIFICADA',
                  doc_consumido: { presente: false, count: 0 },
                  doc_producido: { presente: false, count: 0 },
                  plazo: null, resultado: null,
                },
              ],
            },
          ],
        },
      ],
    },
    {
      tipo: 'solicitud',
      id: 102,
      siglas: 'AAC',
      descripcion: 'Autorización Ambiental — solicitud resuelta',
      estado: 'RESUELTA',
      fecha_presentacion: '2023-11-03',
      agregados: aggVacio(),
      fases: [
        {
          tipo: 'fase',
          id: 203,
          tipo_codigo: 'EVALUACION_AMBIENTAL',
          nombre: 'Evaluación ambiental',
          estado: 'FINALIZADA',
          resultado: 'FAVORABLE',
          agregados: aggVacio(),
          tramites: [
            {
              tipo: 'tramite',
              id: 304,
              tipo_codigo: 'INFORME_AMBIENTAL',
              nombre: 'Informe ambiental',
              estado: 'FINALIZADO',
              agregados: aggVacio(),
              tareas: [
                {
                  tipo: 'tarea', id: 408, tipo_codigo: 'ELABORAR', nombre: 'Elaborar informe ambiental',
                  estado: 'EJECUTADA',
                  doc_consumido: { presente: true, count: 1 },
                  doc_producido: { presente: true, count: 1 },
                  plazo: null, resultado: null,
                },
              ],
            },
          ],
        },
      ],
    },
  ],
}

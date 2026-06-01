// arbolMock.js — árbol de ejemplo para `npm run dev` standalone (andamiaje desechable).
//
// Fiel al contrato de app/services/arbol_expediente.py (ADR-016 §16 + MODELO §3/§4/§7/§8).
// NO es AT-2009 exacto: ejercita layout, colapso y —sobre todo— los 6 colores semáforo
// y los decoradores (docs, plazo, círculo hueco/relleno). La verificación real va contra
// el endpoint Flask con AT-2009 (id=9).

const aggVacio = () => ({
  plazos_vencidos: 0, plazos_proximos: 0, plazos_en_plazo: 0, pendientes_notificar: 0,
})
const sem = (estado, color, propio) => ({ estado, color, propio })
const doc = (presente, count, na = false) => ({ presente, count, na })

export const ARBOL_MOCK = {
  expediente: {
    tipo: 'expediente',
    id: 9,
    codigo: 'AT-2009',
    titular: 'Endesa Distribución S.L.U.',
    responsable: 'CLG',
    tipo_expediente: 'Línea de Alta Tensión',
    semaforo: sem('PENDIENTE_ESTUDIO', 'rojo', false),
  },
  solicitudes: [
    {
      tipo: 'solicitud',
      id: 101,
      siglas: 'AAP',
      descripcion: 'Autorización Administrativa Previa',
      estado: 'EN_TRAMITE',
      fecha_presentacion: '2024-02-10',
      doc_consumido: doc(true, 1),
      doc_producido: doc(false, 0, true),
      semaforo: sem('PENDIENTE_ESTUDIO', 'rojo', false),
      agregados: { plazos_vencidos: 1, plazos_proximos: 1, plazos_en_plazo: 0, pendientes_notificar: 1 },
      fases: [
        {
          tipo: 'fase',
          id: 201,
          tipo_codigo: 'INFORMACION_PUBLICA',
          nombre: 'Información Pública',
          abrev: 'INF. PÚBLICA',
          estado: 'FINALIZADA',
          resultado: 'FAVORABLE',
          semaforo: sem('FIN', 'verde', false),
          agregados: aggVacio(),
          tramites: [
            {
              tipo: 'tramite',
              id: 301,
              tipo_codigo: 'ANUNCIO_BOJA',
              nombre: 'Anuncio en BOJA',
              abrev: 'ANUNCIO BOJA',
              estado: 'FINALIZADO',
              semaforo: sem('FIN', 'verde', false),
              agregados: aggVacio(),
              tareas: [
                {
                  tipo: 'tarea', id: 401, tipo_codigo: 'ELABORAR', abrev: 'ELABORAR', nombre: 'Elaborar anuncio',
                  estado: 'EJECUTADA',
                  doc_consumido: doc(false, 0), doc_producido: doc(true, 1),
                  plazo: null, resultado: null,
                  semaforo: sem('FIN', 'verde', true),
                },
                {
                  tipo: 'tarea', id: 402, tipo_codigo: 'NOTIFICAR', abrev: 'NOTIFICAR', nombre: 'Publicar en BOJA',
                  estado: 'EJECUTADA',
                  doc_consumido: doc(true, 1), doc_producido: doc(true, 1),
                  plazo: null, resultado: 'CORRECTA',
                  semaforo: sem('FIN', 'verde', true),
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
          abrev: 'RESOLUCIÓN',
          estado: 'EN_CURSO',
          resultado: null,
          semaforo: sem('PENDIENTE_ESTUDIO', 'rojo', false),
          agregados: { plazos_vencidos: 1, plazos_proximos: 1, plazos_en_plazo: 0, pendientes_notificar: 1 },
          tramites: [
            {
              tipo: 'tramite',
              id: 302,
              tipo_codigo: 'RECEPCION_ALEGACION',
              nombre: 'Análisis de alegaciones',
              abrev: 'REC. ALEGACIÓN',
              estado: 'EN_CURSO',
              semaforo: sem('PENDIENTE_ESTUDIO', 'rojo', false),
              agregados: { plazos_vencidos: 0, plazos_proximos: 1, plazos_en_plazo: 0, pendientes_notificar: 0 },
              tareas: [
                {
                  tipo: 'tarea', id: 403, tipo_codigo: 'ANALIZAR', abrev: 'ANÁLISIS', nombre: 'Analizar alegaciones',
                  estado: 'EN_CURSO',
                  doc_consumido: doc(true, 2), doc_producido: doc(false, 0),
                  plazo: null, resultado: null,
                  semaforo: sem('PENDIENTE_ESTUDIO', 'rojo', true),
                },
                {
                  tipo: 'tarea', id: 404, tipo_codigo: 'ESPERAR_PLAZO', abrev: 'PLAZO', nombre: 'Plazo de alegaciones',
                  estado: 'EN_CURSO',
                  doc_consumido: doc(false, 0), doc_producido: doc(false, 0),
                  plazo: { estado: 'PROXIMO_VENCER', fecha_limite: '2026-06-05', dias_restantes: 6 },
                  resultado: null,
                  semaforo: sem('PENDIENTE_PLAZOS', 'gris', true),
                },
              ],
            },
            {
              tipo: 'tramite',
              id: 303,
              tipo_codigo: 'ELABORACION',
              nombre: 'Elaboración de resolución',
              abrev: 'ELAB. RESOLUCIÓN',
              estado: 'EN_CURSO',
              semaforo: sem('PENDIENTE_TRAMITAR', 'rojo', false),
              agregados: { plazos_vencidos: 1, plazos_proximos: 0, plazos_en_plazo: 0, pendientes_notificar: 2 },
              tareas: [
                {
                  tipo: 'tarea', id: 405, tipo_codigo: 'ELABORAR', abrev: 'ELABORAR', nombre: 'Elaborar resolución',
                  estado: 'EN_CURSO',
                  doc_consumido: doc(true, 1), doc_producido: doc(false, 0),
                  plazo: null, resultado: null,
                  semaforo: sem('PENDIENTE_FIRMA', 'amarillo', true),   // PDF listo para firma
                },
                {
                  tipo: 'tarea', id: 406, tipo_codigo: 'ESPERAR_PLAZO', abrev: 'PLAZO', nombre: 'Plazo de resolución',
                  estado: 'EN_CURSO',
                  doc_consumido: doc(false, 0), doc_producido: doc(false, 0),
                  plazo: { estado: 'VENCIDO', fecha_limite: '2026-05-20', dias_restantes: -10 },
                  resultado: null,
                  semaforo: sem('PENDIENTE_ESTUDIO', 'rojo', true),     // barra roja 100%
                },
                {
                  tipo: 'tarea', id: 407, tipo_codigo: 'NOTIFICAR', abrev: 'NOTIFICAR', nombre: 'Notificar resolución',
                  estado: 'EN_CURSO',
                  doc_consumido: doc(true, 1), doc_producido: doc(false, 0),
                  plazo: null, resultado: null,
                  semaforo: sem('PENDIENTE_NOTIFICAR', 'azul', true),   // a la espera del destinatario
                },
                {
                  tipo: 'tarea', id: 409, tipo_codigo: 'NOTIFICAR', abrev: 'NOTIFICAR', nombre: 'Notificar (2º intento)',
                  estado: 'EJECUTADA',
                  doc_consumido: doc(true, 1), doc_producido: doc(true, 1),
                  plazo: null, resultado: 'INCORRECTA',
                  semaforo: sem('NOTIFICACION_FALLIDA', 'naranja', true), // queda 2º intento
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
      doc_consumido: doc(true, 1),
      doc_producido: doc(false, 0, true),
      semaforo: sem('FIN', 'verde', false),
      agregados: aggVacio(),
      fases: [
        {
          tipo: 'fase',
          id: 203,
          tipo_codigo: 'COMPATIBILIDAD_AMBIENTAL',
          nombre: 'Evaluación ambiental',
          abrev: 'COMPAT. AMB.',
          estado: 'FINALIZADA',
          resultado: 'FAVORABLE',
          semaforo: sem('FIN', 'verde', false),
          agregados: aggVacio(),
          tramites: [
            {
              tipo: 'tramite',
              id: 304,
              tipo_codigo: 'RECEPCION_INFORME',
              nombre: 'Informe ambiental',
              abrev: 'REC. INFORME',
              estado: 'FINALIZADO',
              semaforo: sem('FIN', 'verde', false),
              agregados: aggVacio(),
              tareas: [
                {
                  tipo: 'tarea', id: 408, tipo_codigo: 'ELABORAR', abrev: 'ELABORAR', nombre: 'Elaborar informe ambiental',
                  estado: 'EJECUTADA',
                  doc_consumido: doc(true, 1), doc_producido: doc(true, 1),
                  plazo: null, resultado: null,
                  semaforo: sem('FIN', 'verde', true),
                },
              ],
            },
          ],
        },
      ],
    },
  ],
}

// Colores por nivel ESFTT — definidos en ANALISIS_GENERACION_DIAGRAMA_EXPEDIENTE.md §9
export const COLORES = {
  solicitud: '#3b7dd8',  // azul
  fase:      '#d97706',  // ámbar
  tramite:   '#7c3aed',  // violeta
}

// Datos mock para la POC — refleja estructura real de ESTRUCTURA_FTT.json
export const MOCK = {
  solicitudes: [
    {
      id: 'sol-001',
      nombre: 'Autorización Administrativa Previa',
      fases: [
        {
          id: 'f-001',
          nombre: 'Análisis de Admisibilidad',
          tramites: [
            { id: 't-001', nombre: 'Análisis técnico' },
            { id: 't-002', nombre: 'Análisis ambiental' },
          ],
        },
        {
          id: 'f-002',
          nombre: 'Consultas Previas',
          tramites: [
            { id: 't-003', nombre: 'Consulta a organismos' },
          ],
        },
        {
          id: 'f-003',
          nombre: 'Información Pública',
          tramites: [
            { id: 't-004', nombre: 'Publicación BOE' },
            { id: 't-005', nombre: 'Publicación BOJA' },
          ],
        },
      ],
    },
    {
      id: 'sol-002',
      nombre: 'Autorización Ambiental Unificada',
      fases: [
        {
          id: 'f-004',
          nombre: 'Evaluación Ambiental',
          tramites: [
            { id: 't-006', nombre: 'Estudio de impacto' },
          ],
        },
      ],
    },
  ],
}

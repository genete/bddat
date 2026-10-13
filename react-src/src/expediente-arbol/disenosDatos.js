// disenosDatos.js — El «diseño» de la zona de datos de cada nodo del árbol (#1043, ADR-053 §C).
//
// Un diseño dice en qué tarjetas va cada dato del payload de `detalle_de_nodo` y qué dato es
// editable, con los rótulos y el orden de los inspectores del listado. Lo pinta `DatosNodo`,
// igual en lectura que en edición. Un nodo sin diseño sigue con la lista de texto plano
// (`Campos`) y su `Editor`, hasta que la revisión nodo a nodo lo migre.
//
// Cada dato: { etiqueta, rotulo?, col?, casilla?, opcional?, campo?, control? }
//   etiqueta  clave del payload (`detalle.campos[].etiqueta`)
//   rotulo    solo si se pinta con otro nombre
//   col       ancho sobre 12 columnas (por defecto 12)
//   casilla   se pinta como casilla de solo lectura («Sí» / «No» en el payload)
//   opcional  si el payload no lo trae, no se pinta (por defecto sale con «—», como en el listado)
//   campo     clave del esquema editable (`esquema_de_nodo`): en edición es el control vivo
//   control   'textarea' para los textos largos (alto igual en lectura y en edición)
//
// `ocultas`: etiquetas que el payload sigue trayendo y no se pintan en el cuerpo porque ya están
// en la barra del marco (decisión de Carlos, 13/10/2026). Cualquier otra que el payload traiga y
// el diseño no conozca cae en una tarjeta «Otros datos»: nunca se pierde información en silencio.

export const DISENO_EXPEDIENTE = {
  ocultas: [],
  tarjetas: [
    {
      titulo: 'Datos administrativos', icono: 'fa-file-alt',
      campos: [
        { etiqueta: 'Tipo de expediente', col: 8 },
        { etiqueta: 'Heredado', col: 4, casilla: true },
        { etiqueta: 'Responsable' },
        { etiqueta: 'Titular' },
        { etiqueta: 'NIF', col: 6 },
        { etiqueta: 'Nº de solicitudes', col: 6 },
      ],
    },
    {
      titulo: 'Datos del proyecto', icono: 'fa-bolt',
      campos: [
        // El payload lo llama «Proyecto»; dentro de «Datos del proyecto» es el título, como en el listado.
        { etiqueta: 'Proyecto', rotulo: 'Título' },
        { etiqueta: 'Finalidad' },
        { etiqueta: 'Emplazamiento' },
      ],
    },
  ],
}

export const DISENO_SOLICITUD = {
  // Estado y Tipo están en la barra (estado, y título «siglas — descripción»).
  ocultas: ['Estado', 'Tipo'],
  tarjetas: [
    {
      titulo: 'Datos de la solicitud', icono: 'fa-file-alt',
      campos: [
        { etiqueta: 'Fecha de presentación', col: 6 },
        { etiqueta: 'Nº de fases', col: 6 },
        { etiqueta: 'Afecta a', opcional: true },
        // El único campo editable de la solicitud hoy (`esquema_editable._esquema_solicitud`).
        { etiqueta: 'Observaciones', campo: 'observaciones', control: 'textarea' },
      ],
    },
    {
      // Aquí entrarán el representante y la sede de notificación (#1038), editables.
      titulo: 'Solicitante', icono: 'fa-user',
      campos: [
        // 6 + 6 y no 8 + 4: con 4 columnas el NIF baja de 110 px a 320 px de inspector, el umbral
        // de un campo de texto en las mediciones de #1042 (GUIA_COMPONENTES_INTERACTIVOS).
        { etiqueta: 'Solicitante', col: 6 },
        { etiqueta: 'NIF', col: 6 },
      ],
    },
  ],
}

const DISENOS = {
  expediente: DISENO_EXPEDIENTE,
  solicitud: DISENO_SOLICITUD,
}

// El diseño del nodo, o null si todavía no está migrado.
export function disenoDeNodo(tipo) {
  return DISENOS[tipo] || null
}

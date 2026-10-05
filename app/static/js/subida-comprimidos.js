// Aviso de ficheros comprimidos al elegirlos para subir (ADR-050 §E, #1007).
// Expone window.quitar_comprimidos(input).
// Cargado en base_app.html tras toast.js; el módulo React
// (react-src/shared/subida.js) actúa como thin wrapper.
//
// Solo mira la extensión, para no subir en balde lo que el servidor va a
// rechazar. La barrera de verdad es el servidor, que reconoce el comprimido
// por su contenido aunque venga renombrado
// (app/services/almacenamiento/formatos.py).
(function () {
  'use strict';

  var EXTENSIONES = ['.zip', '.rar', '.7z'];

  // GEMELO EN PYTHON: `_MENSAJE_COMPRIMIDO` en app/services/almacenamiento/formatos.py,
  // para que el usuario lea lo mismo lo pare quien lo pare. Si cambia uno, cambiar el otro.
  var MENSAJE = 'Los ficheros comprimidos (ZIP, RAR, 7z) no se admiten: descomprímelo y ' +
                'sube cada documento por separado, con su fecha administrativa.';

  function es_comprimido(nombre) {
    var n = (nombre || '').toLowerCase();
    return EXTENSIONES.some(function (ext) { return n.endsWith(ext); });
  }

  // Quita del <input type="file"> los comprimidos, avisa nombrándolos en un solo
  // aviso y devuelve los ficheros que quedan (array de File).
  window.quitar_comprimidos = function (input) {
    var todos = Array.from(input.files || []);
    var rechazados = todos.filter(function (f) { return es_comprimido(f.name); });
    if (rechazados.length === 0) return todos;

    var admitidos = todos.filter(function (f) { return !es_comprimido(f.name); });
    // input.files no se puede editar en sitio: se sustituye por una lista nueva.
    var dt = new DataTransfer();
    admitidos.forEach(function (f) { dt.items.add(f); });
    input.files = dt.files;

    window.mostrar_toast('warning', 'No se han añadido: ' +
      rechazados.map(function (f) { return f.name; }).join(', ') + '. ' + MENSAJE);
    return admitidos;
  };
}());

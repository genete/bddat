/**
 * Script para listado de proyectos
 * - Activación de tooltips Bootstrap 5
 * 
 * Nota: El ordenamiento de columnas se realiza server-side mediante parámetros URL.
 */

document.addEventListener('DOMContentLoaded', function() {
  // Activar tooltips de Bootstrap 5
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });
});

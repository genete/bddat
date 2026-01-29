/**
 * Script para listado de proyectos
 * - Ordenamiento de columnas
 * - Activación de tooltips Bootstrap
 */

document.addEventListener('DOMContentLoaded', function() {
  // Activar tooltips de Bootstrap 5
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });
  
  // Ordenamiento de tabla
  const tabla = document.getElementById('tablaProyectos');
  if (tabla) {
    const encabezados = tabla.querySelectorAll('th.sortable');
    
    encabezados.forEach(function(encabezado) {
      encabezado.style.cursor = 'pointer';
      
      encabezado.addEventListener('click', function() {
        const columna = this.dataset.column;
        const tbody = tabla.querySelector('tbody');
        const filas = Array.from(tbody.querySelectorAll('tr'));
        
        // Determinar dirección de ordenamiento
        const orden = this.classList.contains('asc') ? 'desc' : 'asc';
        
        // Limpiar clases de otros encabezados
        encabezados.forEach(h => h.classList.remove('asc', 'desc'));
        
        // Aplicar clase al encabezado actual
        this.classList.add(orden);
        
        // Obtener índice de la columna
        const colIndex = Array.from(encabezado.parentElement.children).indexOf(encabezado);
        
        // Ordenar filas
        filas.sort(function(a, b) {
          let aVal = a.cells[colIndex].textContent.trim();
          let bVal = b.cells[colIndex].textContent.trim();
          
          // Comparación
          if (aVal < bVal) return orden === 'asc' ? -1 : 1;
          if (aVal > bVal) return orden === 'asc' ? 1 : -1;
          return 0;
        });
        
        // Reordenar filas en el DOM
        filas.forEach(fila => tbody.appendChild(fila));
      });
    });
  }
});

/**
 * v2-tabla-scroll-to-top.js
 * Botón flotante "volver arriba" para scroll interno de C.2 (tabla)
 * 
 * Issue: #94 (Fase 1.5)
 * Epic: #93
 * 
 * Nota: El botón solo aparece en el scroll interno de la tabla (.lista-scroll-container),
 * no en el scroll de la página (B.2), ya que ese scroll es muy corto.
 */

(function() {
    'use strict';
    
    // Esperar a que el DOM esté listo
    document.addEventListener('DOMContentLoaded', function() {
        // Contenedor scrollable (C.2)
        const scrollContainer = document.querySelector('.lista-scroll-container');
        // Botón scroll-to-top
        const scrollBtn = document.getElementById('tabla-scroll-to-top');
        
        if (!scrollContainer) {
            console.warn('Contenedor .lista-scroll-container no encontrado');
            return;
        }
        
        if (!scrollBtn) {
            console.warn('Botón #tabla-scroll-to-top no encontrado');
            return;
        }
        
        // Umbral de scroll para mostrar botón (200px)
        // Como C.2 tiene min-height: 220px, esto es razonable
        const SCROLL_THRESHOLD = 200;
        
        /**
         * Muestra u oculta el botón según la posición de scroll en C.2
         */
        function toggleButton() {
            if (scrollContainer.scrollTop > SCROLL_THRESHOLD) {
                scrollBtn.classList.add('visible');
            } else {
                scrollBtn.classList.remove('visible');
            }
        }
        
        /**
         * Scroll suave al inicio de C.2
         */
        function scrollToTop() {
            scrollContainer.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        }
        
        // Event listeners
        scrollContainer.addEventListener('scroll', toggleButton);
        scrollBtn.addEventListener('click', scrollToTop);
        
        // Comprobar posición inicial (por si ya hay scroll al cargar)
        toggleButton();
    });
})();
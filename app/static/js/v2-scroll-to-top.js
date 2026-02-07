/**
 * v2-scroll-to-top.js
 * Botón flotante para volver al inicio de la página
 * 
 * Issue: #94 (Fase 1)
 * Epic: #93
 */

(function() {
    'use strict';
    
    // Esperar a que el DOM esté listo
    document.addEventListener('DOMContentLoaded', function() {
        const scrollBtn = document.getElementById('scroll-to-top');
        
        if (!scrollBtn) {
            console.warn('Botón #scroll-to-top no encontrado');
            return;
        }
        
        // Umbral de scroll para mostrar botón (300px)
        const SCROLL_THRESHOLD = 300;
        
        /**
         * Muestra u oculta el botón según la posición de scroll
         */
        function toggleButton() {
            if (window.scrollY > SCROLL_THRESHOLD) {
                scrollBtn.classList.add('visible');
            } else {
                scrollBtn.classList.remove('visible');
            }
        }
        
        /**
         * Scroll suave al inicio de la página
         */
        function scrollToTop() {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        }
        
        // Event listeners
        window.addEventListener('scroll', toggleButton);
        scrollBtn.addEventListener('click', scrollToTop);
        
        // Comprobar posición inicial (por si ya hay scroll al cargar)
        toggleButton();
    });
})();
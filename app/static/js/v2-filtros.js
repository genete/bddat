/**
 * FILTROS - Sistema de filtrado para listado de expedientes
 * 
 * PROPÓSITO:
 *   Implementa sistema de filtros para el listado de expedientes.
 *   Se integra con ScrollInfinito para recargar resultados al aplicar filtros.
 *   Valida entradas y proporciona feedback visual al usuario.
 * 
 * ARQUITECTURA:
 *   - Captura eventos de inputs de filtros
 *   - Botón "Filtrar" aplica filtros y recarga scroll infinito
 *   - Botón "Limpiar" resetea filtros y recarga
 *   - Permite filtrado con Enter en campo de búsqueda
 *   - Valida mínimo 2 caracteres en búsqueda
 * 
 * USO:
 *   HTML debe tener:
 *   - Input búsqueda: input[type="search"]
 *   - Select estado: .filters select
 *   - Botón filtrar: .btn-filtrar (o similar)
 *   - Botón limpiar: .btn-limpiar (o similar)
 * 
 *   Inicializar:
 *   const filtros = new FiltrosExpedientes(scrollInfinitoInstance);
 * 
 * VERSIÓN: 1.0
 * FECHA: 2026-02-08
 */

class FiltrosExpedientes {
    /**
     * Constructor de la clase FiltrosExpedientes.
     * 
     * @param {ScrollInfinito} scrollInfinitoInstance - Instancia de ScrollInfinito
     */
    constructor(scrollInfinitoInstance) {
        // Validar instancia de ScrollInfinito
        if (!scrollInfinitoInstance) {
            console.error('FiltrosExpedientes: Se requiere instancia de ScrollInfinito');
            return;
        }
        
        this.scrollInfinito = scrollInfinitoInstance;
        
        // Referencias DOM
        this.searchInput = document.querySelector('input[type="search"]');
        this.estadoSelect = document.querySelector('.filters select');
        this.btnFiltrar = document.querySelector('.btn-filtrar');
        this.btnLimpiar = document.querySelector('.btn-limpiar');
        
        // Si no existen los botones, buscar por texto (fallback)
        if (!this.btnFiltrar) {
            const buttons = document.querySelectorAll('.filters button');
            buttons.forEach(btn => {
                const text = btn.textContent.trim().toLowerCase();
                if (text.includes('filtrar') || text.includes('buscar')) {
                    this.btnFiltrar = btn;
                } else if (text.includes('limpiar') || text.includes('reset')) {
                    this.btnLimpiar = btn;
                }
            });
        }
        
        // Validar elementos mínimos
        if (!this.searchInput && !this.estadoSelect) {
            console.warn('FiltrosExpedientes: No se encontraron inputs de filtros');
            return;
        }
        
        // Estado
        this.isFiltering = false;
        
        // Inicializar
        this.init();
    }
    
    /**
     * Inicializa los filtros y listeners.
     */
    init() {
        // Listener: Enter en campo de búsqueda
        if (this.searchInput) {
            this.searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.aplicarFiltros();
                }
            });
            
            // Limpiar mensaje de error al escribir
            this.searchInput.addEventListener('input', () => {
                this.clearValidationError(this.searchInput);
            });
        }
        
        // Listener: Botón filtrar
        if (this.btnFiltrar) {
            this.btnFiltrar.addEventListener('click', (e) => {
                e.preventDefault();
                this.aplicarFiltros();
            });
        }
        
        // Listener: Botón limpiar
        if (this.btnLimpiar) {
            this.btnLimpiar.addEventListener('click', (e) => {
                e.preventDefault();
                this.limpiarFiltros();
            });
        }
        
        // Listener: Cambio en select estado (opcional: filtrar automáticamente)
        if (this.estadoSelect) {
            this.estadoSelect.addEventListener('change', () => {
                // Por ahora no filtramos automáticamente al cambiar estado
                // El usuario debe hacer click en "Filtrar"
                // Si se desea filtrado automático, descomentar:
                // this.aplicarFiltros();
            });
        }
        
        console.log('FiltrosExpedientes inicializado correctamente');
    }
    
    /**
     * Aplica los filtros y recarga el scroll infinito.
     */
    async aplicarFiltros() {
        // Prevenir múltiples llamadas simultáneas
        if (this.isFiltering) return;
        
        // Validar filtros
        if (!this.validarFiltros()) {
            return;
        }
        
        this.isFiltering = true;
        
        // Feedback visual: deshabilitar botón filtrar
        if (this.btnFiltrar) {
            this.btnFiltrar.disabled = true;
            this.btnFiltrar.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Filtrando...';
        }
        
        try {
            // Recargar scroll infinito con nuevos filtros
            await this.scrollInfinito.reload();
            
            // Feedback visual: resaltar que hay filtros activos
            this.marcarFiltrosActivos();
            
            console.log('Filtros aplicados correctamente');
            
        } catch (error) {
            console.error('Error aplicando filtros:', error);
            this.showError('Error al aplicar filtros. Inténtalo de nuevo.');
        } finally {
            this.isFiltering = false;
            
            // Restaurar botón filtrar
            if (this.btnFiltrar) {
                this.btnFiltrar.disabled = false;
                this.btnFiltrar.innerHTML = '<i class="fas fa-filter"></i> Filtrar';
            }
        }
    }
    
    /**
     * Valida los filtros antes de aplicar.
     * 
     * @returns {boolean} - true si los filtros son válidos
     */
    validarFiltros() {
        // Validar campo de búsqueda: mínimo 2 caracteres si no está vacío
        if (this.searchInput) {
            const searchValue = this.searchInput.value.trim();
            
            if (searchValue.length > 0 && searchValue.length < 2) {
                this.showValidationError(
                    this.searchInput,
                    'La búsqueda debe tener al menos 2 caracteres'
                );
                return false;
            }
        }
        
        // Validar que al menos haya un filtro activo
        const hasSearchFilter = this.searchInput && this.searchInput.value.trim().length >= 2;
        const hasEstadoFilter = this.estadoSelect && 
                                this.estadoSelect.value && 
                                this.estadoSelect.value !== 'Estado: Todos';
        
        if (!hasSearchFilter && !hasEstadoFilter) {
            // No hay filtros, pero esto es válido (mostrará todos)
            // Podríamos mostrar un mensaje informativo, pero no bloqueamos
            console.log('No hay filtros activos, mostrando todos los expedientes');
        }
        
        return true;
    }
    
    /**
     * Limpia todos los filtros y recarga.
     */
    async limpiarFiltros() {
        // Limpiar inputs
        if (this.searchInput) {
            this.searchInput.value = '';
            this.clearValidationError(this.searchInput);
        }
        
        if (this.estadoSelect) {
            this.estadoSelect.selectedIndex = 0; // Seleccionar primera opción
        }
        
        // Quitar resaltado de filtros activos
        this.desmarcarFiltrosActivos();
        
        // Feedback visual
        if (this.btnLimpiar) {
            this.btnLimpiar.disabled = true;
            this.btnLimpiar.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Limpiando...';
        }
        
        try {
            // Recargar scroll infinito sin filtros
            await this.scrollInfinito.reload();
            
            console.log('Filtros limpiados correctamente');
            
        } catch (error) {
            console.error('Error limpiando filtros:', error);
        } finally {
            // Restaurar botón limpiar
            if (this.btnLimpiar) {
                this.btnLimpiar.disabled = false;
                this.btnLimpiar.innerHTML = '<i class="fas fa-times"></i> Limpiar';
            }
        }
    }
    
    /**
     * Marca visualmente que hay filtros activos.
     */
    marcarFiltrosActivos() {
        const filtersContainer = document.querySelector('.filters-row');
        if (filtersContainer) {
            filtersContainer.classList.add('filters-active');
        }
        
        // Añadir clase a inputs con valor
        if (this.searchInput && this.searchInput.value.trim()) {
            this.searchInput.classList.add('filter-active');
        }
        
        if (this.estadoSelect && this.estadoSelect.value && this.estadoSelect.value !== 'Estado: Todos') {
            this.estadoSelect.classList.add('filter-active');
        }
    }
    
    /**
     * Desmarca el resaltado de filtros activos.
     */
    desmarcarFiltrosActivos() {
        const filtersContainer = document.querySelector('.filters-row');
        if (filtersContainer) {
            filtersContainer.classList.remove('filters-active');
        }
        
        if (this.searchInput) {
            this.searchInput.classList.remove('filter-active');
        }
        
        if (this.estadoSelect) {
            this.estadoSelect.classList.remove('filter-active');
        }
    }
    
    /**
     * Muestra un error de validación en un input.
     * 
     * @param {HTMLElement} input - Input con error
     * @param {string} mensaje - Mensaje de error
     */
    showValidationError(input, mensaje) {
        // Añadir clase de error al input
        input.classList.add('is-invalid');
        
        // Crear o actualizar mensaje de error
        let errorDiv = input.parentElement.querySelector('.invalid-feedback');
        
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.className = 'invalid-feedback';
            errorDiv.style.cssText = `
                display: block;
                color: var(--danger, #dc3545);
                font-size: 0.875rem;
                margin-top: 0.25rem;
            `;
            input.parentElement.appendChild(errorDiv);
        }
        
        errorDiv.textContent = mensaje;
        
        // Focus en el input
        input.focus();
    }
    
    /**
     * Limpia el error de validación de un input.
     * 
     * @param {HTMLElement} input - Input a limpiar
     */
    clearValidationError(input) {
        input.classList.remove('is-invalid');
        
        const errorDiv = input.parentElement.querySelector('.invalid-feedback');
        if (errorDiv) {
            errorDiv.remove();
        }
    }
    
    /**
     * Muestra un mensaje de error general.
     * 
     * @param {string} mensaje - Mensaje de error
     */
    showError(mensaje) {
        const filtersContainer = document.querySelector('.filters-row');
        if (!filtersContainer) return;
        
        // Crear elemento de error
        const errorDiv = document.createElement('div');
        errorDiv.className = 'filtros-error';
        errorDiv.style.cssText = `
            padding: 0.75rem 1rem;
            margin-top: 0.5rem;
            color: var(--danger, #dc3545);
            background: #f8d7da;
            border: 1px solid #f5c2c7;
            border-radius: 4px;
            font-size: 0.875rem;
        `;
        errorDiv.innerHTML = `
            <i class="fas fa-exclamation-triangle" style="margin-right: 0.5rem;"></i>
            ${mensaje}
        `;
        
        // Insertar después del contenedor de filtros
        filtersContainer.parentElement.insertBefore(errorDiv, filtersContainer.nextSibling);
        
        // Eliminar después de 5 segundos
        setTimeout(() => errorDiv.remove(), 5000);
    }
    
    /**
     * Obtiene los valores actuales de los filtros.
     * 
     * @returns {Object} - Objeto con los filtros activos
     */
    obtenerFiltrosActivos() {
        const filtros = {};
        
        if (this.searchInput && this.searchInput.value.trim()) {
            filtros.search = this.searchInput.value.trim();
        }
        
        if (this.estadoSelect && this.estadoSelect.value && this.estadoSelect.value !== 'Estado: Todos') {
            filtros.estado = this.estadoSelect.value;
        }
        
        return filtros;
    }
    
    /**
     * Comprueba si hay filtros activos.
     * 
     * @returns {boolean} - true si hay filtros activos
     */
    hayFiltrosActivos() {
        const filtros = this.obtenerFiltrosActivos();
        return Object.keys(filtros).length > 0;
    }
}

// Exportar para uso global o modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FiltrosExpedientes;
}

/**
 * SCROLL INFINITO - Carga progresiva de expedientes
 * 
 * PROPÓSITO:
 *   Implementa scroll infinito en listado de expedientes usando paginación
 *   por cursor. Detecta cuando el usuario llega al 80% del scroll del
 *   contenedor C.2 (.lista-scroll-container) y carga automáticamente más
 *   registros desde la API.
 * 
 * ARQUITECTURA:
 *   - Observa scroll de .lista-scroll-container (C.2)
 *   - Llama a API /api/expedientes con cursor
 *   - Renderiza filas dinámicamente en <tbody>
 *   - Actualiza contador "Mostrando X de Y"
 *   - Muestra loader mientras carga
 * 
 * USO:
 *   HTML debe tener:
 *   - Contenedor: .lista-scroll-container
 *   - Tabla: .expedientes-table con <tbody>
 *   - Contador: .pagination-info con <span> internos
 *   - Filtros: input[type="search"], select (opcional)
 * 
 *   Inicializar:
 *   const scrollInfinito = new ScrollInfinito({
 *     apiUrl: '/api/expedientes',
 *     limit: 50,
 *     threshold: 0.8
 *   });
 * 
 * VERSIÓN: 1.1
 * FECHA: 2026-02-12
 * CAMBIOS: Botón Ver ahora apunta a /expedientes/<id>/tramitacion_v3
 */

class ScrollInfinito {
    /**
     * Constructor de la clase ScrollInfinito.
     * 
     * @param {Object} options - Configuración
     * @param {string} options.apiUrl - URL de la API (default: '/api/expedientes')
     * @param {number} options.limit - Registros por página (default: 50)
     * @param {number} options.threshold - Umbral de scroll 0-1 (default: 0.8 = 80%)
     */
    constructor(options = {}) {
        // Configuración
        this.apiUrl = options.apiUrl || '/api/expedientes';
        this.limit = options.limit || 50;
        this.threshold = options.threshold || 0.8; // 80% del scroll
        
        // Estado
        this.cursor = 0;           // Cursor actual (ID del último expediente)
        this.hasMore = true;       // ¿Hay más páginas?
        this.loading = false;      // ¿Estamos cargando?
        this.totalLoaded = 0;      // Total de expedientes cargados
        this.totalAvailable = null; // Total disponible (si API lo provee)
        
        // Referencias DOM
        this.container = document.querySelector('.lista-scroll-container');
        this.tbody = document.querySelector('.expedientes-table tbody');
        this.paginationInfo = document.querySelector('.pagination-info');
        this.searchInput = document.querySelector('input[type="search"]');
        this.estadoSelect = document.querySelector('.filters select');
        
        // Validar elementos necesarios
        if (!this.container) {
            console.error('ScrollInfinito: No se encontró .lista-scroll-container');
            return;
        }
        if (!this.tbody) {
            console.error('ScrollInfinito: No se encontró tbody en .expedientes-table');
            return;
        }
        
        // Inicializar
        this.init();
    }
    
    /**
     * Inicializa el scroll infinito.
     */
    init() {
        // Limpiar tabla (eliminar datos estáticos si los hay)
        this.tbody.innerHTML = '';
        
        // Crear loader
        this.createLoader();
        
        // Cargar primera página
        this.loadMore();
        
        // Escuchar scroll del contenedor
        this.container.addEventListener('scroll', () => this.handleScroll());
        
        console.log('ScrollInfinito inicializado correctamente');
    }
    
    /**
     * Maneja el evento de scroll.
     */
    handleScroll() {
        // Si ya estamos cargando o no hay más datos, no hacer nada
        if (this.loading || !this.hasMore) return;
        
        // Calcular porcentaje de scroll
        const scrollTop = this.container.scrollTop;
        const scrollHeight = this.container.scrollHeight;
        const clientHeight = this.container.clientHeight;
        
        const scrollPercentage = (scrollTop + clientHeight) / scrollHeight;
        
        // Si llegamos al threshold, cargar más
        if (scrollPercentage >= this.threshold) {
            this.loadMore();
        }
    }
    
    /**
     * Carga más expedientes desde la API.
     */
    async loadMore() {
        if (this.loading || !this.hasMore) return;
        
        this.loading = true;
        this.showLoader();
        
        try {
            // Construir URL con parámetros
            const params = new URLSearchParams({
                cursor: this.cursor,
                limit: this.limit
            });
            
            // Añadir filtros si existen
            if (this.searchInput && this.searchInput.value.trim()) {
                params.append('search', this.searchInput.value.trim());
            }
            if (this.estadoSelect && this.estadoSelect.value && this.estadoSelect.value !== 'Estado: Todos') {
                params.append('estado', this.estadoSelect.value);
            }
            
            const url = `${this.apiUrl}?${params.toString()}`;
            
            // Llamar a API
            const response = await fetch(url);
            
            if (!response.ok) {
                throw new Error(`Error ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            // Actualizar estado
            this.cursor = data.next_cursor;
            this.hasMore = data.has_more;
            this.totalAvailable = data.total || null;
            
            // Renderizar expedientes
            this.renderExpedientes(data.data);
            
            // Actualizar contador
            this.totalLoaded += data.data.length;
            this.updatePaginationInfo();
            
            // Log para debugging
            console.log(`Cargados ${data.data.length} expedientes. Total: ${this.totalLoaded}. Cursor: ${this.cursor}. Has more: ${this.hasMore}`);
            
        } catch (error) {
            console.error('Error cargando expedientes:', error);
            this.showError('Error al cargar expedientes. Inténtalo de nuevo.');
        } finally {
            this.loading = false;
            this.hideLoader();
        }
    }
    
    /**
     * Renderiza una lista de expedientes en el tbody.
     * 
     * @param {Array} expedientes - Array de objetos expediente
     */
    renderExpedientes(expedientes) {
        const fragment = document.createDocumentFragment();
        
        expedientes.forEach(exp => {
            const tr = this.createExpedienteRow(exp);
            fragment.appendChild(tr);
        });
        
        this.tbody.appendChild(fragment);
    }
    
    /**
     * Crea una fila <tr> para un expediente.
     * 
     * @param {Object} exp - Objeto expediente
     * @returns {HTMLElement} - Elemento <tr>
     */
    createExpedienteRow(exp) {
        const tr = document.createElement('tr');
        
        // Columna: N° Expediente
        const tdNumero = document.createElement('td');
        tdNumero.innerHTML = `<strong>AT-${exp.numero_at}</strong>`;
        tr.appendChild(tdNumero);
        
        // Columna: Titular
        const tdTitular = document.createElement('td');
        tdTitular.textContent = exp.titular;
        tr.appendChild(tdTitular);
        
        // Columna: Solicitudes (mock por ahora)
        const tdSolicitudes = document.createElement('td');
        tdSolicitudes.textContent = '-'; // TODO: Añadir cuando API devuelva count
        tr.appendChild(tdSolicitudes);
        
        // Columna: Estado (mock por ahora)
        const tdEstado = document.createElement('td');
        const badgeClass = this.getEstadoBadgeClass(exp.estado || 'En trámite');
        tdEstado.innerHTML = `<span class="badge ${badgeClass}">${exp.estado || 'En trámite'}</span>`;
        tr.appendChild(tdEstado);
        
        // Columna: Vencimiento (mock por ahora)
        const tdVencimiento = document.createElement('td');
        tdVencimiento.textContent = exp.vencimiento || '-';
        tr.appendChild(tdVencimiento);
        
        // Columna: Acciones
        const tdAcciones = document.createElement('td');
        const btnVer = document.createElement('button');
        btnVer.className = 'btn btn-sm btn-primary';
        btnVer.textContent = 'Ver';
        btnVer.addEventListener('click', () => this.verExpediente(exp.id));
        tdAcciones.appendChild(btnVer);
        tr.appendChild(tdAcciones);
        
        return tr;
    }
    
    /**
     * Obtiene la clase CSS del badge según el estado.
     * 
     * @param {string} estado - Estado del expediente
     * @returns {string} - Clase CSS del badge
     */
    getEstadoBadgeClass(estado) {
        const estadoLower = estado.toLowerCase();
        
        if (estadoLower.includes('trámite')) return 'badge-info';
        if (estadoLower.includes('resuelto') || estadoLower.includes('completo')) return 'badge-success';
        if (estadoLower.includes('incompleto') || estadoLower.includes('pendiente')) return 'badge-warning';
        if (estadoLower.includes('vencido') || estadoLower.includes('urgente')) return 'badge-danger';
        
        return 'badge-info'; // Default
    }
    
    /**
     * Actualiza el contador de paginación.
     */
    updatePaginationInfo() {
        if (!this.paginationInfo) return;
        
        const spans = this.paginationInfo.querySelectorAll('span');
        
        if (spans.length >= 2) {
            // Actualizar "Mostrando 1-X"
            spans[0].textContent = this.totalLoaded > 0 ? `1-${this.totalLoaded}` : '0';
            
            // Actualizar "de Y"
            if (this.totalAvailable !== null) {
                spans[1].textContent = this.totalAvailable;
            } else if (!this.hasMore) {
                // Si ya no hay más, el total es lo cargado
                spans[1].textContent = this.totalLoaded;
            } else {
                // Si hay más pero no sabemos cuántos, mostrar "muchos"
                spans[1].textContent = 'muchos';
            }
        }
    }
    
    /**
     * Crea el elemento loader.
     */
    createLoader() {
        this.loader = document.createElement('div');
        this.loader.className = 'scroll-infinito-loader';
        this.loader.style.cssText = `
            display: none;
            padding: 2rem;
            text-align: center;
            color: var(--text-secondary, #666);
            font-size: 0.875rem;
        `;
        this.loader.innerHTML = `
            <i class="fas fa-spinner fa-spin" style="font-size: 1.5rem; margin-bottom: 0.5rem;"></i>
            <div>Cargando expedientes...</div>
        `;
        
        // Insertar después de la tabla
        this.container.appendChild(this.loader);
    }
    
    /**
     * Muestra el loader.
     */
    showLoader() {
        if (this.loader) {
            this.loader.style.display = 'block';
        }
    }
    
    /**
     * Oculta el loader.
     */
    hideLoader() {
        if (this.loader) {
            this.loader.style.display = 'none';
        }
    }
    
    /**
     * Muestra un mensaje de error.
     * 
     * @param {string} mensaje - Mensaje de error
     */
    showError(mensaje) {
        // Crear elemento de error
        const errorDiv = document.createElement('div');
        errorDiv.className = 'scroll-infinito-error';
        errorDiv.style.cssText = `
            padding: 1rem 2rem;
            text-align: center;
            color: var(--danger, #dc3545);
            background: var(--bg-subtle, #f8f9fa);
            border: 1px solid var(--danger, #dc3545);
            border-radius: 4px;
            margin: 1rem 0;
        `;
        errorDiv.innerHTML = `
            <i class="fas fa-exclamation-triangle" style="margin-right: 0.5rem;"></i>
            ${mensaje}
        `;
        
        // Insertar después de la tabla
        this.container.appendChild(errorDiv);
        
        // Eliminar después de 5 segundos
        setTimeout(() => errorDiv.remove(), 5000);
    }
    
    /**
     * Navega a la vista de tramitación jerárquica (Vista 3) de un expediente.
     * 
     * @param {number} id - ID del expediente
     */
    verExpediente(id) {
        window.location.href = `/expedientes/${id}/tramitacion_v3`;
    }
    
    /**
     * Recarga el listado desde cero.
     * Útil para aplicar filtros.
     */
    reload() {
        // Reset estado
        this.cursor = 0;
        this.hasMore = true;
        this.totalLoaded = 0;
        this.totalAvailable = null;
        
        // Limpiar tabla
        this.tbody.innerHTML = '';
        
        // Cargar primera página
        this.loadMore();
    }
}

// Exportar para uso global o modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ScrollInfinito;
}

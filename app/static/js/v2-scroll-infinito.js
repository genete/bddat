/**
 * SCROLL INFINITO - Carga progresiva de registros
 *
 * PROPÓSITO:
 *   Implementa scroll infinito en listados usando paginación por cursor.
 *   Detecta cuando el usuario llega al umbral del scroll del contenedor
 *   C.2 (.lista-scroll-container) y carga automáticamente más registros.
 *
 * ARQUITECTURA:
 *   - Observa scroll de .lista-scroll-container (C.2)
 *   - Llama a API con cursor
 *   - Renderiza filas dinámicamente en <tbody>
 *   - Actualiza contador "Mostrando X de Y"
 *   - Muestra loader mientras carga
 *
 * MODOS DE USO:
 *
 *   Modo legacy (expedientes, sin config columnas):
 *     const s = new ScrollInfinito({ apiUrl: '/api/expedientes' });
 *
 *   Modo genérico (cualquier entidad con config columnas):
 *     const s = new ScrollInfinito({
 *       apiUrl:      '/api/entidades',
 *       tableClass:  '.entidades-table',
 *       entityLabel: 'entidades',
 *       detailUrl:   id => `/entidades/${id}`,
 *       columns: [
 *         { key: 'nombre_completo', label: 'Nombre',  type: 'text'    },
 *         { key: 'cif_nif',         label: 'NIF/CIF', type: 'text'    },
 *         { key: 'tipo_entidad',    label: 'Tipo',    type: 'badge'   },
 *         { key: 'activo',          label: 'Activo',  type: 'bool'    },
 *         { key: '_acciones',       label: '',        type: 'acciones'}
 *       ]
 *     });
 *
 *   Tipos de columna soportados:
 *     - text     : textContent plano
 *     - badge    : <span class="badge badge-info">
 *     - bool     : icono check si true, vacío si false
 *     - acciones : botón "Ver" que navega a detailUrl(id)
 *
 * VERSIÓN: 1.2
 * FECHA: 2026-02-19
 * CAMBIOS v1.2: Generalizado con config columnas — backward compatible con v1.1
 * CAMBIOS v1.1: Botón Ver apunta a /expedientes/<id>/tramitacion_v3
 */

class ScrollInfinito {
    /**
     * @param {Object}   options
     * @param {string}   options.apiUrl      - URL de la API. Default: '/api/expedientes'
     * @param {number}   options.limit       - Registros por página. Default: 50
     * @param {number}   options.threshold   - Umbral de scroll 0-1. Default: 0.8
     * @param {Array}    options.columns     - Config columnas (modo genérico). Default: null (usa legacy)
     * @param {string}   options.tableClass  - Selector CSS de la tabla. Default: '.expedientes-table'
     * @param {string}   options.entityLabel - Nombre de la entidad para mensajes. Default: 'expedientes'
     * @param {Function} options.detailUrl   - Función id => URL del detalle. Default: V3 expedientes
     */
    constructor(options = {}) {
        // Configuración base
        this.apiUrl      = options.apiUrl      || '/api/expedientes';
        this.limit       = options.limit       || 50;
        this.threshold   = options.threshold   || 0.8;

        // Configuración genérica (nueva en v1.2)
        this.columns     = options.columns     || null;
        this.tableClass  = options.tableClass  || '.expedientes-table';
        this.entityLabel = options.entityLabel || 'expedientes';
        this.detailUrl   = options.detailUrl   || (id => `/expedientes/${id}/tramitacion_v3`);

        // Estado
        this.cursor         = 0;
        this.hasMore        = true;
        this.loading        = false;
        this.totalLoaded    = 0;
        this.totalAvailable = null;

        // Referencias DOM
        this.container      = document.querySelector('.lista-scroll-container');
        this.tbody          = document.querySelector(`${this.tableClass} tbody`);
        this.paginationInfo = document.querySelector('.pagination-info');
        this.searchInput    = document.querySelector('input[type="search"]');
        this.estadoSelect   = document.querySelector('.filters select');

        // Validar elementos necesarios
        if (!this.container) {
            console.error('ScrollInfinito: No se encontró .lista-scroll-container');
            return;
        }
        if (!this.tbody) {
            console.error(`ScrollInfinito: No se encontró tbody en ${this.tableClass}`);
            return;
        }

        this.init();
    }

    init() {
        this.tbody.innerHTML = '';
        this.createLoader();
        this.loadMore();
        this.container.addEventListener('scroll', () => this.handleScroll());
        console.log(`ScrollInfinito inicializado — ${this.entityLabel}`);
    }

    handleScroll() {
        if (this.loading || !this.hasMore) return;
        const scrollPercentage =
            (this.container.scrollTop + this.container.clientHeight) /
            this.container.scrollHeight;
        if (scrollPercentage >= this.threshold) {
            this.loadMore();
        }
    }

    async loadMore() {
        if (this.loading || !this.hasMore) return;
        this.loading = true;
        this.showLoader();

        try {
            const params = new URLSearchParams({ cursor: this.cursor, limit: this.limit });
            if (this.searchInput && this.searchInput.value.trim()) {
                params.append('search', this.searchInput.value.trim());
            }
            if (this.estadoSelect && this.estadoSelect.value &&
                this.estadoSelect.value !== 'Estado: Todos') {
                params.append('estado', this.estadoSelect.value);
            }

            const response = await fetch(`${this.apiUrl}?${params.toString()}`);
            if (!response.ok) throw new Error(`Error ${response.status}: ${response.statusText}`);

            const data = await response.json();

            this.cursor         = data.next_cursor;
            this.hasMore        = data.has_more;
            this.totalAvailable = data.total || null;

            this.renderItems(data.data);

            this.totalLoaded += data.data.length;
            this.updatePaginationInfo();

            console.log(`[${this.entityLabel}] Cargados ${data.data.length}. Total: ${this.totalLoaded}. HasMore: ${this.hasMore}`);

        } catch (error) {
            console.error(`Error cargando ${this.entityLabel}:`, error);
            this.showError(`Error al cargar ${this.entityLabel}. Inténtalo de nuevo.`);
        } finally {
            this.loading = false;
            this.hideLoader();
        }
    }

    // ---------------------------------------------------------------------------
    // RENDERIZADO
    // ---------------------------------------------------------------------------

    /**
     * Renderiza un array de items en el tbody.
     * Nombre genérico (antes: renderExpedientes).
     */
    renderItems(items) {
        const fragment = document.createDocumentFragment();
        items.forEach(item => fragment.appendChild(this.createRow(item)));
        this.tbody.appendChild(fragment);
    }

    /**
     * Dispatcher: usa motor genérico si hay columns config, legacy si no.
     */
    createRow(item) {
        if (this.columns) return this.createRowFromColumns(item);
        return this.createExpedienteRow(item);
    }

    /**
     * Motor genérico: crea fila a partir de config columnas.
     * Tipos soportados: text | badge | bool | acciones
     */
    createRowFromColumns(item) {
        const tr = document.createElement('tr');
        this.columns.forEach(col => {
            const td = document.createElement('td');
            switch (col.type) {
                case 'text':
                    td.textContent = (item[col.key] !== undefined && item[col.key] !== null)
                        ? item[col.key] : '-';
                    break;
                case 'badge': {
                    const val = item[col.key] || '-';
                    td.innerHTML = `<span class="badge badge-info">${val}</span>`;
                    break;
                }
                case 'bool':
                    td.innerHTML = item[col.key]
                        ? '<i class="fas fa-check-circle text-success"></i>'
                        : '';
                    break;
                case 'custom': {
                    const val = item[col.key];
                    td.innerHTML = col.renderFn ? col.renderFn(val, item) : (val ?? '-');
                    break;
                }
                case 'acciones': {
                    const btn = document.createElement('button');
                    btn.className = 'btn btn-sm btn-primary';
                    btn.innerHTML = '<i class="fas fa-eye"></i> Ver';
                    btn.addEventListener('click', () => {
                        window.location.href = this.detailUrl(item.id);
                    });
                    td.appendChild(btn);
                    break;
                }
                default:
                    td.textContent = item[col.key] || '-';
            }
            tr.appendChild(td);
        });
        return tr;
    }

    /**
     * Fila legacy para expedientes (v1.1 — intacta para compatibilidad).
     * Se usa cuando no se pasa options.columns.
     */
    createExpedienteRow(exp) {
        const tr = document.createElement('tr');

        const tdNumero = document.createElement('td');
        tdNumero.innerHTML = `<strong>AT-${exp.numero_at}</strong>`;
        tr.appendChild(tdNumero);

        const tdTitular = document.createElement('td');
        tdTitular.textContent = exp.titular;
        tr.appendChild(tdTitular);

        const tdSolicitudes = document.createElement('td');
        tdSolicitudes.textContent = '-';
        tr.appendChild(tdSolicitudes);

        const tdEstado = document.createElement('td');
        const badgeClass = this.getEstadoBadgeClass(exp.estado || 'En trámite');
        tdEstado.innerHTML = `<span class="badge ${badgeClass}">${exp.estado || 'En trámite'}</span>`;
        tr.appendChild(tdEstado);

        const tdVencimiento = document.createElement('td');
        tdVencimiento.textContent = exp.vencimiento || '-';
        tr.appendChild(tdVencimiento);

        const tdAcciones = document.createElement('td');
        const btnVer = document.createElement('button');
        btnVer.className = 'btn btn-sm btn-primary';
        btnVer.textContent = 'Ver';
        btnVer.addEventListener('click', () => this.verExpediente(exp.id));
        tdAcciones.appendChild(btnVer);
        tr.appendChild(tdAcciones);

        return tr;
    }

    getEstadoBadgeClass(estado) {
        const e = estado.toLowerCase();
        if (e.includes('trámite'))                               return 'badge-info';
        if (e.includes('resuelto') || e.includes('completo'))   return 'badge-success';
        if (e.includes('incompleto') || e.includes('pendiente')) return 'badge-warning';
        if (e.includes('vencido') || e.includes('urgente'))     return 'badge-danger';
        return 'badge-info';
    }

    verExpediente(id) {
        window.location.href = this.detailUrl(id);
    }

    // ---------------------------------------------------------------------------
    // PAGINACIÓN Y UI
    // ---------------------------------------------------------------------------

    updatePaginationInfo() {
        if (!this.paginationInfo) return;
        const spans = this.paginationInfo.querySelectorAll('span');
        if (spans.length >= 2) {
            spans[0].textContent = this.totalLoaded > 0 ? `1-${this.totalLoaded}` : '0';
            if (this.totalAvailable !== null) {
                spans[1].textContent = this.totalAvailable;
            } else if (!this.hasMore) {
                spans[1].textContent = this.totalLoaded;
            } else {
                spans[1].textContent = '...';
            }
        }
    }

    createLoader() {
        this.loader = document.createElement('div');
        this.loader.className = 'scroll-infinito-loader';
        this.loader.style.cssText = `
            display: none; padding: 2rem; text-align: center;
            color: var(--text-secondary, #666); font-size: 0.875rem;
        `;
        this.loader.innerHTML = `
            <i class="fas fa-spinner fa-spin" style="font-size:1.5rem;margin-bottom:0.5rem;"></i>
            <div>Cargando ${this.entityLabel}...</div>
        `;
        this.container.appendChild(this.loader);
    }

    showLoader() { if (this.loader) this.loader.style.display = 'block'; }
    hideLoader() { if (this.loader) this.loader.style.display = 'none';  }

    showError(mensaje) {
        const div = document.createElement('div');
        div.className = 'scroll-infinito-error';
        div.style.cssText = `
            padding: 1rem 2rem; text-align: center;
            color: var(--danger, #dc3545);
            background: var(--bg-subtle, #f8f9fa);
            border: 1px solid var(--danger, #dc3545);
            border-radius: 4px; margin: 1rem 0;
        `;
        div.innerHTML = `<i class="fas fa-exclamation-triangle" style="margin-right:0.5rem;"></i>${mensaje}`;
        this.container.appendChild(div);
        setTimeout(() => div.remove(), 5000);
    }

    reload() {
        this.cursor         = 0;
        this.hasMore        = true;
        this.totalLoaded    = 0;
        this.totalAvailable = null;
        this.tbody.innerHTML = '';
        this.loadMore();
    }
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = ScrollInfinito;
}

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
 *   Modo selección (ADR-023 — inspector overlay, #534):
 *     const s = new ScrollInfinito({
 *       ...
 *       selection: {
 *         fragmentUrl: id   => `/entidades/${id}/fragmento`,
 *         title:       item => item.nombre_completo || ''
 *       }
 *     });
 *     Con selection activo: no se renderiza columna type:'acciones'; cada fila
 *     recibe data-inspector-sel y un click handler que llama AppInspector.open.
 *     Requiere window.AppInspector (inspector-overlay.js) cargado antes.
 *
 *   Modo checkbox masivo (asignación en lote, #612):
 *     const s = new ScrollInfinito({
 *       ...
 *       bulkCheckbox: true
 *     });
 *     Con bulkCheckbox activo, el modo se enciende/apaga en runtime con
 *     `s.setBulkMode(true|false)` — no en el constructor. Mientras está activo:
 *     cada fila gana un checkbox inicial (sustituye al comportamiento de `selection`,
 *     que queda suspendido) y el <thead> gana un checkbox "seleccionar todos". La
 *     selección vive en `s._bulkSelected` (Set de ids) y cada cambio dispara
 *     `document.dispatchEvent(new CustomEvent('bulk:selection-changed', {detail}))`.
 *     `setBulkMode` fuerza `fixedParams.responsable = 'sin_asignar'` y hace `reload()`.
 *
 *   Tipos de columna soportados:
 *     - text     : textContent plano
 *     - badge    : <span class="badge badge-info">
 *     - bool     : icono check si true, vacío si false
 *     - acciones : botón "Ver" que navega a detailUrl(id); omitido en modo selección
 *
 * VERSIÓN: 1.7
 * FECHA: 2026-07-15
 * CAMBIOS v1.7: setFiltroExterno(name, value, label) — fija/quita un filtro que no es
 *               un <select> dentro de .filters (p. ej. SelectorBusqueda de municipio,
 *               que llamaba a un método que no existía y el filtro no aplicaba nunca, #642).
 * CAMBIOS v1.6: reload() ahora invalida con seguridad un loadMore() en vuelo (token
 *               _loadGen) en vez de quedar bloqueado por la guarda `this.loading`.
 *               Sin esto, llamar reload()/setBulkMode() justo tras construir la
 *               instancia (mientras la carga inicial del constructor sigue en curso)
 *               perdía el reload: la respuesta vieja, sin el filtro nuevo, acababa
 *               poblando la tabla (#612).
 * CAMBIOS v1.5: Modo checkbox masivo opt-in (bulkCheckbox / setBulkMode) para
 *               asignación en lote (#612). Sin bulkCheckbox, cero cambio de
 *               comportamiento — el resto de listados no lo pasan.
 * CAMBIOS v1.4: Multi-filtro — envía todos los .filters select por su atributo `name`
 *               (antes solo el primero como 'estado'). Habilita 2+ filtros por listado
 *               (usuarios: activo+rol) y activa filtros ya soportados por backend (#544).
 * CAMBIOS v1.3: Modo selección (selection option) para inspector overlay (ADR-023 / #534)
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
     * @param {string}   options.tableClass  - Selector CSS de la tabla. Default: '.lista-table'
     * @param {string}   options.entityLabel - Nombre de la entidad para mensajes. Default: 'expedientes'
     * @param {Function} options.detailUrl   - Función id => URL del detalle. Default: BC expedientes
     * @param {Object}   options.fixedParams - Parámetros fijos añadidos a cada petición. Default: {}
     * @param {Object}   options.selection   - Config modo selección (ADR-023). Si se pasa: activa inspector
     *                                         overlay en lugar del botón "Ver". Campos:
     *                                         { fragmentUrl: id => '...', title: item => '...' }
     * @param {boolean}  options.bulkCheckbox - Habilita el modo checkbox masivo (#612). Opt-in: sin esta
     *                                         opción, cero cambio de comportamiento. Ver setBulkMode().
     */
    constructor(options = {}) {
        // Configuración base
        this.apiUrl      = options.apiUrl      || '/api/expedientes';
        this.limit       = options.limit       || 50;
        this.threshold   = options.threshold   || 0.8;
        this.fixedParams = options.fixedParams || {};

        // Configuración genérica (nueva en v1.2)
        this.columns     = options.columns     || null;
        this.tableClass  = options.tableClass  || '.lista-table';
        this.entityLabel = options.entityLabel || 'expedientes';
        this.detailUrl   = options.detailUrl   || (id => `/expedientes/${id}/tramitacion`);

        // Modo selección — inspector overlay (v1.3 / ADR-023 / #534)
        this.selection   = options.selection   || null;

        // Modo checkbox masivo — asignación en lote (v1.5 / #612). Capacidad opt-in;
        // el modo en sí se enciende/apaga en runtime con setBulkMode().
        this.bulkCheckbox     = options.bulkCheckbox || false;
        this._bulkModeActive  = false;
        this._bulkSelected    = new Set();

        // Estado
        this.cursor         = 0;
        this.hasMore        = true;
        this.loading        = false;
        this.totalLoaded    = 0;
        this.totalAvailable = null;
        // Token de generación: invalida cualquier loadMore() en vuelo cuando reload()
        // se dispara antes de que termine (p.ej. setBulkMode() llamado justo tras
        // construir la instancia, mientras la carga inicial del constructor sigue en
        // curso — sin esto, la guarda `this.loading` bloquea la recarga con el filtro
        // nuevo y la respuesta vieja, sin filtrar, acaba poblando la tabla).
        this._loadGen        = 0;

        // Referencias DOM
        this.container      = document.querySelector('.lista-scroll-container');
        this.tbody          = document.querySelector(`${this.tableClass} tbody`);
        this.paginationInfo = document.querySelector('.pagination-info');
        this.searchInput    = document.querySelector('.filters input[type="search"]');

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
        if (this.selection) {
            document.addEventListener('inspector:closed', () => this._clearSelected());
        }
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
        const myGen = this._loadGen;
        this.loading = true;
        this.showLoader();

        try {
            const params = new URLSearchParams({ cursor: this.cursor, limit: this.limit, ...this.fixedParams });
            if (this.searchInput && this.searchInput.value.trim()) {
                params.append('search', this.searchInput.value.trim());
            }
            // Filtros select (multi-filtro): cada select activo se envía por su atributo `name`.
            // Se consultan en cada carga para incluir selects inyectados de forma diferida
            // (p. ej. un SelectorFiltro creado tras una llamada async). Un select sin `name`
            // cae al parámetro 'estado' por compatibilidad con listados legacy.
            document.querySelectorAll('.filters select').forEach(sel => {
                const val = (sel.value || '').trim();
                if (!val) return;
                params.append(sel.getAttribute('name') || 'estado', val);
            });

            const response = await fetch(`${this.apiUrl}?${params.toString()}`);
            if (!response.ok) throw new Error(`Error ${response.status}: ${response.statusText}`);

            const data = await response.json();
            // Una recarga más reciente (reload()) invalidó esta petición mientras
            // estaba en vuelo — descartar en silencio, no tocar tbody ni estado.
            if (myGen !== this._loadGen) return;

            this.cursor         = data.next_cursor;
            this.hasMore        = data.has_more;
            this.totalAvailable = data.total || null;

            this.renderItems(data.data);

            this.totalLoaded += data.data.length;
            this.updatePaginationInfo();

            console.log(`[${this.entityLabel}] Cargados ${data.data.length}. Total: ${this.totalLoaded}. HasMore: ${this.hasMore}`);

        } catch (error) {
            if (myGen !== this._loadGen) return;
            console.error(`Error cargando ${this.entityLabel}:`, error);
            this.showError(`Error al cargar ${this.entityLabel}. Inténtalo de nuevo.`);
        } finally {
            if (myGen === this._loadGen) {
                this.loading = false;
                this.hideLoader();
            }
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
        if (this.selection) this._reapplySelected();
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
     * Tipos soportados: text | badge | bool | custom | acciones (omitido en modo selection)
     */
    createRowFromColumns(item) {
        const tr = document.createElement('tr');
        if (this.bulkCheckbox && this._bulkModeActive) {
            tr.appendChild(this._createBulkCheckCell(item));
        } else if (this.selection) {
            tr.setAttribute('data-inspector-sel', String(item.id));
            tr.classList.add('is-selectable');
            tr.addEventListener('click', () => this._handleRowClick(tr, item));
        }
        this.columns.forEach(col => {
            if (col.type === 'acciones' && this.selection) return;
            const td = document.createElement('td');
            // Clases declarativas de ocultación responsive y truncado (ADR-022 §3).
            // col.hide = 'xl'|'lg'|'md'; col.truncate = true. El <th> equivalente
            // las recibe en lista_v2_base.html.
            if (col.hide)     td.classList.add('lt-hide-' + col.hide);
            if (col.truncate) td.classList.add('lt-truncate');
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
                    btn.className = 'btn-accion-ver';
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
    // MODO SELECCIÓN (ADR-023 / #534)
    // ---------------------------------------------------------------------------

    _handleRowClick(tr, item) {
        const selId = String(item.id);
        if (window.AppInspector && AppInspector.isOpen() && AppInspector.currentSel() === selId) {
            AppInspector.close();
        } else {
            this._clearSelected();
            tr.classList.add('is-selected');
            if (window.AppInspector) {
                AppInspector.open({
                    selId:       selId,
                    title:       this.selection.title ? this.selection.title(item) : '',
                    fragmentUrl: this.selection.fragmentUrl(item.id),
                });
            }
        }
    }

    _clearSelected() {
        this.tbody.querySelectorAll('tr.is-selected').forEach(r => r.classList.remove('is-selected'));
    }

    _reapplySelected() {
        if (!window.AppInspector || !AppInspector.isOpen()) return;
        const cur = AppInspector.currentSel();
        if (!cur) return;
        this.tbody.querySelectorAll(`tr[data-inspector-sel="${cur}"]`).forEach(r => r.classList.add('is-selected'));
    }

    // ---------------------------------------------------------------------------
    // MODO CHECKBOX MASIVO — asignación en lote (v1.5 / #612)
    // ---------------------------------------------------------------------------

    _createBulkCheckCell(item) {
        const td = document.createElement('td');
        const chk = document.createElement('input');
        chk.type = 'checkbox';
        chk.className = 'form-check-input bulk-row-check';
        chk.dataset.id = String(item.id);
        chk.checked = this._bulkSelected.has(item.id);
        chk.addEventListener('change', () => {
            if (chk.checked) this._bulkSelected.add(item.id);
            else this._bulkSelected.delete(item.id);
            this._dispatchBulkChange();
        });
        td.appendChild(chk);
        return td;
    }

    _dispatchBulkChange() {
        document.dispatchEvent(new CustomEvent('bulk:selection-changed', {
            detail: { size: this._bulkSelected.size, ids: Array.from(this._bulkSelected) },
        }));
    }

    _toggleAllVisibleBulk(checked) {
        this.tbody.querySelectorAll('.bulk-row-check').forEach(chk => {
            chk.checked = checked;
            const id = parseInt(chk.dataset.id, 10);
            if (checked) this._bulkSelected.add(id);
            else this._bulkSelected.delete(id);
        });
        this._dispatchBulkChange();
    }

    /**
     * Vacía la selección sin salir del modo masivo (a diferencia de setBulkMode(false),
     * no toca el filtro ni recarga). Cubre lo que hoy solo se lograba con doble click
     * en "seleccionar todos" del thead.
     */
    clearBulkSelection() {
        this._toggleAllVisibleBulk(false);
        const headChk = this.tbody.closest('table')?.querySelector('thead .bulk-check-col input');
        if (headChk) headChk.checked = false;
    }

    /**
     * Enciende/apaga el modo checkbox masivo en runtime. Requiere bulkCheckbox:true
     * en el constructor. Al activar, fuerza el filtro a expedientes sin asignar y
     * recarga desde cero (misma entrada siempre limpia — no hay selección previa que
     * conservar). Al desactivar, retira ese filtro y recarga.
     */
    setBulkMode(active) {
        if (!this.bulkCheckbox) return;
        this._bulkModeActive = active;
        this._bulkSelected.clear();
        this._dispatchBulkChange();

        const headRow = this.tbody.closest('table')?.querySelector('thead tr');
        if (headRow) {
            let th = headRow.querySelector('.bulk-check-col');
            if (active && !th) {
                th = document.createElement('th');
                th.className = 'bulk-check-col';
                th.style.width = '2rem';
                const chk = document.createElement('input');
                chk.type = 'checkbox';
                chk.className = 'form-check-input';
                chk.title = 'Seleccionar / deseleccionar todos';
                chk.addEventListener('change', () => this._toggleAllVisibleBulk(chk.checked));
                th.appendChild(chk);
                headRow.prepend(th);
            } else if (!active && th) {
                th.remove();
            }
        }

        if (active) {
            this.fixedParams = { ...this.fixedParams, responsable: 'sin_asignar' };
        } else {
            const { responsable, ...rest } = this.fixedParams;
            this.fixedParams = rest;
        }
        this.reload();
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

    /**
     * Fija (o quita, si value es vacío) un filtro que no viene de un <select>
     * dentro de .filters — p. ej. un SelectorBusqueda (municipio), que no es un
     * <select> nativo y por tanto no lo recoge el escaneo de loadMore(). Se
     * añade a fixedParams y se recarga el listado desde cero.
     * label se acepta por compatibilidad con la firma existente en las
     * llamadas (p. ej. `Mun: Sevilla`); no hay UI de chip que lo consuma hoy.
     */
    setFiltroExterno(name, value, label) {
        const nuevo = { ...this.fixedParams };
        if (value === null || value === undefined || value === '') {
            delete nuevo[name];
        } else {
            nuevo[name] = value;
        }
        this.fixedParams = nuevo;
        this.reload();
    }

    reload() {
        this._loadGen++;
        this.cursor         = 0;
        this.hasMore        = true;
        this.loading        = false;
        this.totalLoaded    = 0;
        this.totalAvailable = null;
        this.tbody.innerHTML = '';
        this.loadMore();
    }
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = ScrollInfinito;
}

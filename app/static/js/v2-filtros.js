/**
 * FiltrosListado — filtrado con debounce para listados V2
 *
 * Debounce automático en el input de búsqueda. Los selects disparan
 * recarga inmediata. btn-filtrar es opcional (dispara recarga manual).
 * btn-limpiar vacía todos los campos y recarga.
 * El icono .filtro-indicador se activa (verde) cuando hay filtros activos.
 *
 * USO:
 *   const filtros = new FiltrosListado(scrollInfinitoInstance);
 *   const filtros = new FiltrosListado(scrollInfinitoInstance, { delay: 300 });
 *
 * VERSIÓN: 2.1 — indicador de filtros activos (#206)
 */

class FiltrosListado {
    constructor(scrollInfinitoInstance, opciones = {}) {
        if (!scrollInfinitoInstance) {
            console.error('FiltrosListado: Se requiere instancia de ScrollInfinito');
            return;
        }

        this.scroll  = scrollInfinitoInstance;
        this.delay   = opciones.delay ?? 400;

        this.searchInput  = document.querySelector('input[type="search"]');
        this.selects      = document.querySelectorAll('.filters-row select');
        this.btnFiltrar   = document.querySelector('.btn-filtrar');
        this.btnLimpiar   = document.querySelector('.btn-limpiar');
        this._filtersRow  = document.querySelector('.filters-row');

        this._timer = null;
        this._init();
    }

    _init() {
        // Debounce en campo de búsqueda
        if (this.searchInput) {
            this.searchInput.addEventListener('input', () => {
                clearTimeout(this._timer);
                this._timer = setTimeout(() => {
                    this.scroll.reload();
                    this._actualizarIndicador();
                }, this.delay);
            });
        }

        // Selects: recarga inmediata al cambiar
        this.selects.forEach(sel => {
            sel.addEventListener('change', () => {
                this.scroll.reload();
                this._actualizarIndicador();
            });
        });

        // btn-filtrar: disparo manual (complementario al debounce)
        if (this.btnFiltrar) {
            this.btnFiltrar.addEventListener('click', (e) => {
                e.preventDefault();
                clearTimeout(this._timer);
                this.scroll.reload();
                this._actualizarIndicador();
            });
        }

        // btn-limpiar: vaciar todo y recargar
        if (this.btnLimpiar) {
            this.btnLimpiar.addEventListener('click', (e) => {
                e.preventDefault();
                this._limpiar();
            });
        }
    }

    _actualizarIndicador() {
        if (!this._filtersRow) return;
        const hayFiltros = (this.searchInput && this.searchInput.value.trim())
            || Array.from(this.selects).some(s => s.value);
        this._filtersRow.classList.toggle('filtros-activos', !!hayFiltros);
    }

    _limpiar() {
        if (this.searchInput) this.searchInput.value = '';
        this.selects.forEach(sel => { sel.selectedIndex = 0; });
        clearTimeout(this._timer);
        this._actualizarIndicador();
        this.scroll.reload();
    }
}

// Alias para compatibilidad con instanciaciones anteriores
const FiltrosExpedientes = FiltrosListado;

if (typeof module !== 'undefined' && module.exports) {
    module.exports = FiltrosListado;
}

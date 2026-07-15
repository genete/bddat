/**
 * FiltrosListado — filtrado con debounce para listados V2
 *
 * Debounce automático en el input de búsqueda y en los InputFiltro (.if-input).
 * Los selects (incluidos los de SelectorFiltro) disparan recarga inmediata.
 * btn-filtrar es opcional (dispara recarga manual).
 * btn-limpiar vacía todos los campos y recarga.
 * El icono .filtro-indicador se activa (verde) cuando hay filtros activos.
 *
 * USO:
 *   const filtros = new FiltrosListado(scrollInfinitoInstance);
 *   const filtros = new FiltrosListado(scrollInfinitoInstance, { delay: 300 });
 *
 * COMPONENTES COMPATIBLES (detección automática en .filters-row):
 *   - input[type="search"]  — buscador principal (debounce)
 *   - select / .sf-select   — SelectorFiltro y selects nativos (inmediato)
 *   - .if-input             — InputFiltro (debounce)
 *
 * VERSIÓN: 2.3 — btn-limpiar y .filtro-indicador también reaccionan a los filtros
 *                 externos de ScrollInfinito.setFiltroExterno (p. ej. municipio, #642)
 */

class FiltrosListado {
    constructor(scrollInfinitoInstance, opciones = {}) {
        if (!scrollInfinitoInstance) {
            console.error('FiltrosListado: Se requiere instancia de ScrollInfinito');
            return;
        }

        this.scroll  = scrollInfinitoInstance;
        this.delay   = opciones.delay ?? 400;

        this.searchInput  = document.querySelector('.filters input[type="search"]');
        this.selects      = document.querySelectorAll('.filters-row select');
        this.inputsFiltro = document.querySelectorAll('.filters-row .if-input');
        this.btnFiltrar   = document.querySelector('.btn-filtrar');
        this.btnLimpiar   = document.querySelector('.btn-limpiar');
        this._filtersRow  = document.querySelector('.filters-row');

        this._timer     = null;
        this._limpiando = false;   // suprime recargas durante _limpiar()
        this._init();

        // Filtros externos (ScrollInfinito.setFiltroExterno, p. ej. municipio, #642):
        // no son <select> dentro de .filters-row, así que el indicador/btn-limpiar
        // no los veía. Reaccionar al evento que dispara setFiltroExterno.
        document.addEventListener('scroll:filtros-externos-changed', () => this._actualizarIndicador());
    }

    _init() {
        // Debounce en campo de búsqueda principal
        if (this.searchInput) {
            this.searchInput.addEventListener('input', () => {
                if (this._limpiando) return;
                clearTimeout(this._timer);
                this._timer = setTimeout(() => {
                    this.scroll.reload();
                    this._actualizarIndicador();
                }, this.delay);
            });
        }

        // Selects (nativos y SelectorFiltro): recarga inmediata al cambiar
        this.selects.forEach(sel => {
            sel.addEventListener('change', () => {
                if (this._limpiando) return;
                this.scroll.reload();
                this._actualizarIndicador();
            });
        });

        // InputFiltro (.if-input): debounce igual que el buscador principal
        this.inputsFiltro.forEach(inp => {
            inp.addEventListener('input', () => {
                if (this._limpiando) return;
                clearTimeout(this._timer);
                this._timer = setTimeout(() => {
                    this.scroll.reload();
                    this._actualizarIndicador();
                }, this.delay);
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
        const hayFiltrosExternos = !!Object.keys(this.scroll._filtrosExternos || {}).length;
        const hayFiltros = (this.searchInput && this.searchInput.value.trim())
            || Array.from(this.selects).some(s => s.value)
            || Array.from(this.inputsFiltro).some(inp => inp.value.trim())
            || hayFiltrosExternos;
        this._filtersRow.classList.toggle('filtros-activos', !!hayFiltros);
        if (this.btnLimpiar) this.btnLimpiar.disabled = !hayFiltros;
    }

    _limpiar() {
        this._limpiando = true;
        if (this.searchInput) this.searchInput.value = '';

        // Delegar en .clear() de SelectorFiltro (actualiza CSS + dispara change suprimido)
        // o resetear directamente si es un select nativo sin instancia
        this.selects.forEach(sel => {
            if (sel._sfInstance) sel._sfInstance.clear();
            else sel.selectedIndex = 0;
        });

        // Igual para InputFiltro
        this.inputsFiltro.forEach(inp => {
            if (inp._ifInstance) inp._ifInstance.clear();
            else inp.value = '';
        });

        // Filtros externos (#642) — quitar cada uno; dispara 'scroll:filtros-externos-changed'
        // para que quien los originó (p. ej. el selector de municipio) resetee su propia UI.
        Object.keys(this.scroll._filtrosExternos || {}).forEach(name => {
            this.scroll.setFiltroExterno(name, null);
        });

        this._limpiando = false;
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

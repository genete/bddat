/**
 * InputFiltro — campo de texto para filtros con icono de lupa y estado activo
 *
 * Compañero de SelectorFiltro para filtros de texto. Compatible con
 * FiltrosListado (requiere v2-filtros.js ≥ 2.2): el input interno
 * (.if-input) es detectado y gestionado automáticamente.
 *
 * FICHEROS:
 *   app/static/js/input_filtro.js
 *   app/static/css/input_filtro.css
 *
 * USO:
 *   new InputFiltro('#mi-div', {
 *     placeholder: 'Filtrar por NIF...',
 *     name: 'nif',                       // name del <input> para lectura en JS
 *     onChange: (v) => {}                // opcional — llamado en cada tecla
 *   });
 *
 * API PÚBLICA:
 *   .getValue()     → string con el valor actual o ''
 *   .setValue(v)    → establece el valor programáticamente (dispara onChange)
 *   .clear()        → limpia el campo (dispara onChange con '')
 *   .enable() / .disable()
 *
 * NOTA INTERNA:
 *   El <input> expone ._ifInstance apuntando a esta instancia para que
 *   FiltrosListado pueda actualizar el estado visual en _limpiar() sin
 *   disparar eventos extra.
 *
 * VERSIÓN: 1.0
 */
class InputFiltro {
    constructor(selector, config = {}) {
        this._wrap = typeof selector === 'string'
            ? document.querySelector(selector)
            : selector;
        if (!this._wrap) {
            console.error('InputFiltro: elemento no encontrado', selector);
            return;
        }

        this._placeholder = config.placeholder || 'Filtrar...';
        this._name        = config.name        || '';
        this._onChange    = config.onChange    || null;

        this._build();
        this._bindEvents();
    }

    _build() {
        this._wrap.className = 'if-wrap';

        // Icono lupa — decorativo, no interactivo
        this._icon = document.createElement('span');
        this._icon.className = 'if-icon';
        this._icon.setAttribute('aria-hidden', 'true');
        this._icon.innerHTML = '<i class="fas fa-search"></i>';

        this._input = document.createElement('input');
        this._input.type = 'text';
        this._input.className = 'if-input';
        this._input.placeholder = this._placeholder;
        this._input.autocomplete = 'off';
        if (this._name) this._input.name = this._name;

        this._btnX = document.createElement('button');
        this._btnX.type = 'button';
        this._btnX.className = 'if-btn-x';
        this._btnX.tabIndex = -1;
        this._btnX.textContent = '×';
        this._btnX.setAttribute('aria-label', 'Limpiar filtro');

        this._wrap.appendChild(this._icon);
        this._wrap.appendChild(this._input);
        this._wrap.appendChild(this._btnX);

        // Referencia inversa para que FiltrosListado pueda llamar _actualizarEstado()
        this._input._ifInstance = this;

        this._actualizarEstado();
    }

    _bindEvents() {
        this._input.addEventListener('input', () => {
            this._actualizarEstado();
            if (this._onChange) this._onChange(this._input.value);
        });

        this._btnX.addEventListener('mousedown', e => e.preventDefault());
        this._btnX.addEventListener('click', () => this.clear());
    }

    _actualizarEstado() {
        this._wrap.classList.toggle('if-activo', !!this._input.value.trim());
    }

    getValue() {
        return this._input.value;
    }

    setValue(v) {
        this._input.value = v;
        this._actualizarEstado();
        if (this._onChange) this._onChange(v);
    }

    clear() {
        this._input.value = '';
        this._actualizarEstado();
        this._input.focus();
        if (this._onChange) this._onChange('');
        // Notifica a FiltrosListado igual que haría un cambio manual del usuario
        this._input.dispatchEvent(new Event('input', { bubbles: true }));
    }

    enable() {
        this._input.disabled = false;
        this._wrap.classList.remove('if-disabled');
    }

    disable() {
        this._input.disabled = true;
        this._wrap.classList.add('if-disabled');
    }
}

/**
 * SelectorFiltro — selector de filtro con etiqueta contextual y estado activo
 *
 * Wrapper sobre un <select> nativo. Compatible con FiltrosListado sin
 * configuración adicional: el <select> interno es detectado automáticamente
 * al estar dentro de .filters-row.
 *
 * FICHEROS:
 *   app/static/js/selector_filtro.js
 *   app/static/css/selector_filtro.css
 *
 * USO:
 *   new SelectorFiltro('#mi-div', opciones, {
 *     label: 'Tipo expediente',       // → muestra "Tipo expediente (todos)" vacío
 *     name: 'tipo_expediente_id',     // name del <select> para que FiltrosListado lo lea
 *     onChange: (v, t) => {}          // opcional
 *   });
 *
 *   El array opciones tiene la forma [{ v: 'valor', t: 'texto visible' }, ...]
 *
 * API PÚBLICA:
 *   .getValue()           → valor seleccionado o ''
 *   .setValue(v)          → selecciona programáticamente (dispara onChange)
 *   .clear()              → vuelve al estado "todos" (dispara onChange con v='')
 *   .setOpciones(nuevas)  → reemplaza opciones sin disparar onChange
 *   .enable() / .disable()
 *
 * NOTA INTERNA:
 *   El <select> expone ._sfInstance apuntando a esta instancia para que
 *   FiltrosListado pueda actualizar el estado visual en _limpiar() sin
 *   disparar eventos extra.
 *
 * VERSIÓN: 1.0
 */
class SelectorFiltro {
    constructor(selector, opciones, config = {}) {
        this._wrap = typeof selector === 'string'
            ? document.querySelector(selector)
            : selector;
        if (!this._wrap) {
            console.error('SelectorFiltro: elemento no encontrado', selector);
            return;
        }

        this._opciones = opciones || [];
        this._label    = config.label    || 'Seleccione';
        this._name     = config.name     || '';
        this._onChange = config.onChange || null;

        this._build();
        this._bindEvents();
    }

    _build() {
        this._wrap.className = 'sf-wrap';

        this._select = document.createElement('select');
        this._select.className = 'sf-select';
        if (this._name) this._select.name = this._name;

        // Primera opción: el estado "sin filtro"
        const optTodos = document.createElement('option');
        optTodos.value = '';
        optTodos.textContent = `${this._label} (todos)`;
        this._select.appendChild(optTodos);

        this._opciones.forEach(op => {
            const opt = document.createElement('option');
            opt.value       = op.v;
            opt.textContent = op.t;
            this._select.appendChild(opt);
        });

        this._btnX = document.createElement('button');
        this._btnX.type = 'button';
        this._btnX.className = 'sf-btn-x';
        this._btnX.tabIndex = -1;
        this._btnX.textContent = '×';
        this._btnX.setAttribute('aria-label', 'Limpiar filtro');

        this._wrap.appendChild(this._select);
        this._wrap.appendChild(this._btnX);

        // Referencia inversa para que FiltrosListado pueda llamar _actualizarEstado()
        this._select._sfInstance = this;

        this._actualizarEstado();
    }

    _bindEvents() {
        this._select.addEventListener('change', () => {
            this._actualizarEstado();
            if (this._onChange) {
                const idx = this._select.selectedIndex;
                this._onChange(this._select.value, this._select.options[idx]?.text || '');
            }
        });

        // mousedown + preventDefault evita que el blur del select dispare antes de procesar
        this._btnX.addEventListener('mousedown', e => e.preventDefault());
        this._btnX.addEventListener('click', () => this.clear());
    }

    _actualizarEstado() {
        this._wrap.classList.toggle('sf-activo', !!this._select.value);
    }

    getValue() {
        return this._select.value;
    }

    setValue(v) {
        this._select.value = v;
        this._actualizarEstado();
        if (this._onChange) {
            const idx = this._select.selectedIndex;
            this._onChange(v, this._select.options[idx]?.text || '');
        }
    }

    clear() {
        this._select.value = '';
        this._actualizarEstado();
        this._select.focus();
        if (this._onChange) this._onChange('', '');
        // Notifica a FiltrosListado igual que haría un cambio manual del usuario
        this._select.dispatchEvent(new Event('change', { bubbles: true }));
    }

    setOpciones(nuevas) {
        // Mantener solo la primera opción ("todos") y sustituir el resto
        while (this._select.options.length > 1) this._select.remove(1);
        nuevas.forEach(op => {
            const opt = document.createElement('option');
            opt.value       = op.v;
            opt.textContent = op.t;
            this._select.appendChild(opt);
        });
        this._select.value = '';
        this._actualizarEstado();
    }

    enable() {
        this._select.disabled = false;
        this._wrap.classList.remove('sf-disabled');
    }

    disable() {
        this._select.disabled = true;
        this._wrap.classList.add('sf-disabled');
    }
}

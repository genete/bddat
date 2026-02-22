/**
 * SelectorBusqueda — Control de selección con filtrado por texto
 *
 * Uso:
 *   new SelectorBusqueda('#mi-wrap', opciones, config)
 *
 * opciones: [{ v: 'valor', t: 'texto visible' }, ...]
 *
 * config (todos opcionales):
 *   placeholder  — texto del estado vacío (por defecto '— Seleccione —')
 *   name         — atributo name del input hidden (para envío de formulario)
 *
 * API pública:
 *   .getValue()      → valor actualmente seleccionado ('' si vacío)
 *   .setValue(v, t)  → selecciona programáticamente
 *   .clear()         → limpia la selección
 */
class SelectorBusqueda {

  constructor(destino, opciones, config = {}) {
    this.el       = typeof destino === 'string' ? document.querySelector(destino) : destino;
    this.opciones = opciones;
    this.ph       = config.placeholder || '— Seleccione —';
    this.name     = config.name || '';
    this._valor   = '';
    this._idx     = -1;
    this._abierto = false;
    this.onChange = config.onChange || null;
    this._construir();
    this._bind();
  }

  // ── Construcción del DOM ──────────────────────────────────────────────────

  _construir() {
    this.el.classList.add('sb-wrap');
    this.el.innerHTML = `
      <input  type="text"   class="form-control sb-input" autocomplete="off"
              placeholder="${this.ph}" title="Escriba para filtrar. ESC limpia.">
      <input  type="hidden" ${this.name ? `name="${this.name}"` : ''}>
      <button type="button" class="sb-btn-x" tabindex="-1" title="Limpiar selección">
        &times;
      </button>
      <button type="button" class="sb-btn-v" tabindex="-1" title="Abrir lista">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="12" viewBox="0 0 16 16">
          <path fill="none" stroke="currentColor" stroke-linecap="round"
                stroke-linejoin="round" stroke-width="2" d="m2 5 6 6 6-6"/>
        </svg>
      </button>
      <ul class="sb-lista dropdown-menu"></ul>
    `;
    this._input  = this.el.querySelector('.sb-input');
    this._hidden = this.el.querySelector('input[type="hidden"]');
    this._btnX   = this.el.querySelector('.sb-btn-x');
    this._btnV   = this.el.querySelector('.sb-btn-v');
    this._lista  = this.el.querySelector('.sb-lista');
  }

  // ── Renderizado de la lista ───────────────────────────────────────────────

  _items() {
    return this._lista.querySelectorAll('li:not(.sb-placeholder)');
  }

  _renderizar(filtro) {
    const filtradas = filtro
      ? this.opciones.filter(o => o.t.toLowerCase().includes(filtro.toLowerCase()))
      : this.opciones;

    this._lista.innerHTML =
      `<li class="sb-placeholder dropdown-item" data-v="">${this.ph}</li>`;

    filtradas.forEach(o => {
      const li = document.createElement('li');
      li.className   = 'dropdown-item';
      li.dataset.v   = o.v;
      li.textContent = o.t;
      this._lista.appendChild(li);
    });

    this._idx = -1;
  }

  // ── Apertura / cierre ─────────────────────────────────────────────────────

  _abrir() {
    this._renderizar(this._valor ? '' : this._input.value);
    this._lista.classList.add('show');
    this._abierto = true;
  }

  _cerrar() {
    this._lista.classList.remove('show');
    this._abierto = false;
  }

  // ── Selección y limpieza ──────────────────────────────────────────────────

  _seleccionar(v, t) {
    this._valor        = v;
    this._input.value  = v ? t : '';
    this._hidden.value = v;
    this._cerrar();
    if (this.onChange) this.onChange(v, t);
  }

  _limpiar() {
    this._seleccionar('', '');
    this._input.focus();
  }

  // ── API pública ───────────────────────────────────────────────────────────

  getValue()       { return this._valor; }
  setValue(v, t)   { this._seleccionar(v, t); }
  clear()          { this._limpiar(); }

  // Actualiza la lista de opciones sin disparar onChange ni cambiar el valor visible
  setOpciones(opciones) {
    this.opciones      = opciones;
    this._valor        = '';
    this._input.value  = '';
    this._hidden.value = '';
    this._cerrar();
  }

  disable() {
    this._input.disabled = true;
    this._btnV.disabled  = true;
    this._cerrar();
  }

  enable() {
    this._input.disabled = false;
    this._btnV.disabled  = false;
  }

  // ── Eventos ───────────────────────────────────────────────────────────────

  _bind() {
    // Abrir al enfocar
    this._input.addEventListener('focus', () => this._abrir());

    // Filtrar al escribir
    this._input.addEventListener('input', () => {
      this._valor = '';
      this._renderizar(this._input.value);
      this._lista.classList.add('show');
      this._abierto = true;
    });

    // Cerrar al perder foco (con retardo para que el clic en lista se procese)
    this._input.addEventListener('blur', () => setTimeout(() => {
      if (!this._valor) this._input.value = '';
      this._cerrar();
    }, 150));

    // Navegación por teclado
    this._input.addEventListener('keydown', (e) => {
      const its = this._items();
      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          this._idx = Math.min(this._idx + 1, its.length - 1);
          its.forEach((li, i) => li.classList.toggle('active', i === this._idx));
          its[this._idx]?.scrollIntoView({ block: 'nearest' });
          break;
        case 'ArrowUp':
          e.preventDefault();
          this._idx = Math.max(this._idx - 1, -1);
          its.forEach((li, i) => li.classList.toggle('active', i === this._idx));
          break;
        case 'Enter':
          e.preventDefault();
          if (this._idx >= 0)
            this._seleccionar(its[this._idx].dataset.v, its[this._idx].textContent);
          break;
        case 'Escape':
          this._limpiar();
          break;
      }
    });

    // Clic en la lista (mousedown para no disparar blur antes)
    this._lista.addEventListener('mousedown', (e) => {
      e.preventDefault();
      const li = e.target.closest('li');
      if (li) this._seleccionar(li.dataset.v, li.textContent);
    });

    // Botón ×
    this._btnX.addEventListener('click', () => this._limpiar());

    // Botón ▾ — alterna abrir/cerrar
    this._btnV.addEventListener('mousedown', (e) => {
      e.preventDefault();
      if (this._abierto) this._cerrar();
      else { this._abrir(); this._input.focus(); }
    });
  }
}

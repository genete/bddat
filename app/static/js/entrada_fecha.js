// entrada_fecha.js — componente EntradaFecha
// Uso: new EntradaFecha('#contenedor', { name, placeholder, onChange })

class EntradaFecha {
  constructor(selector, config = {}) {
    this._contenedor = document.querySelector(selector);
    if (!this._contenedor) throw new Error(`EntradaFecha: no se encontró "${selector}"`);

    this._name        = config.name        || '';
    this._placeholder = config.placeholder || 'dd/mm/aaaa';
    this._onChange    = config.onChange    || null;

    this._construir();
    this._conectar();
  }

  // ── HTML interno ──────────────────────────────────────────────
  _construir() {
    this._contenedor.classList.add('ef-wrap');
    this._contenedor.innerHTML = `
      <input type="text"   class="form-control ef-input" placeholder="${this._placeholder}" autocomplete="off"
             data-bs-toggle="tooltip" data-bs-placement="top" title="Escape para borrar">
      <input type="hidden" name="${this._name}" class="ef-hidden">
      <button type="button" class="ef-btn-x" tabindex="-1" title="Limpiar">&times;</button>
    `;
    this._input   = this._contenedor.querySelector('.ef-input');
    this._hidden  = this._contenedor.querySelector('.ef-hidden');
    this._btnX    = this._contenedor.querySelector('.ef-btn-x');
    this._tooltip = new bootstrap.Tooltip(this._input, { trigger: 'hover' });
  }

  // ── Eventos ───────────────────────────────────────────────────
  _conectar() {
    this._input.addEventListener('blur',    () => this._alSalir());
    this._input.addEventListener('focus',   () => this._input.classList.remove('is-invalid'));
    this._input.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') { this.clear(); e.preventDefault(); }
      if (e.key === 'Enter')  { this._alSalir(); e.preventDefault(); }
    });
    // mousedown en vez de click para no disparar blur antes de tiempo
    this._btnX.addEventListener('mousedown', (e) => {
      e.preventDefault();
      this.clear();
      this._input.focus();
    });
  }

  // ── Lógica de parseo ──────────────────────────────────────────
  _parsear(str) {
    if (!str.trim()) return null;
    const partes = str.trim().split(/[\/\-\.\s]+/);
    if (partes.length !== 3) return null;
    let [d, m, y] = partes.map(Number);
    if (isNaN(d) || isNaN(m) || isNaN(y)) return null;
    if (y >= 0 && y < 100) y += 2000;
    if (m < 1 || m > 12 || d < 1 || d > 31) return null;
    const fecha = new Date(y, m - 1, d);
    if (fecha.getFullYear() !== y || fecha.getMonth() !== m - 1 || fecha.getDate() !== d) return null;
    const p = n => String(n).padStart(2, '0');
    return { d, m, y, iso: `${y}-${p(m)}-${p(d)}`, display: `${p(d)}/${p(m)}/${y}` };
  }

  _alSalir() {
    const str = this._input.value.trim();
    if (!str) {
      this._limpiarEstado();
      return;
    }
    const r = this._parsear(str);
    if (r) {
      this._input.classList.remove('is-invalid');
      this._input.value  = r.display;
      this._hidden.value = r.iso;
      this._btnX.style.display = '';
      if (this._onChange) this._onChange(r.iso);
    } else {
      this._input.classList.add('is-invalid');
      this._hidden.value = '';
    }
  }

  _limpiarEstado() {
    this._input.classList.remove('is-invalid');
    this._hidden.value = '';
    this._btnX.style.display = 'none';
  }

  // ── API pública ───────────────────────────────────────────────
  getValue() { return this._hidden.value; }

  setValue(iso) {
    const m = iso && iso.match(/^(\d{4})-(\d{2})-(\d{2})$/);
    if (!m) return;
    const [, y, mo, d] = m;
    this._input.value  = `${d}/${mo}/${y}`;
    this._hidden.value = iso;
    this._input.classList.remove('is-invalid');
    this._btnX.style.display = '';
    if (this._onChange) this._onChange(iso);
  }

  clear() {
    this._input.value = '';
    this._limpiarEstado();
    if (this._onChange) this._onChange('');
  }

  enable() {
    this._input.disabled = false;
    this._btnX.disabled  = false;
  }

  disable() {
    this._input.disabled = true;
    this._btnX.disabled  = true;
  }
}

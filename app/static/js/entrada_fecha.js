// Mockup de referencia original: docs/mockups/fecha-mockup.html (commit 028451f)
// entrada_fecha.js — componente EntradaFecha
// Uso: new EntradaFecha('#contenedor', { name, placeholder, onChange, maxHoy })
//
// maxHoy (#824): fecha ISO tope, normalmente la de trabajo del sistema
// ({{ hoy_sistema }}, que respeta el reloj de desarrollo). Con ella, una fecha
// posterior se rechaza igual que una mal formada — marca is-invalid y deja el
// hidden vacío, así que el formulario no la puede enviar.
//
// Es opcional por instancia y no por defecto: el componente es genérico y no
// toda fecha que recoja es administrativa. Las que sí lo son la activan; una
// fecha de hito o de previsión, legítimamente futura, no.

class EntradaFecha {
  constructor(selector, config = {}) {
    this._contenedor = document.querySelector(selector);
    if (!this._contenedor) throw new Error(`EntradaFecha: no se encontró "${selector}"`);

    this._name        = config.name        || '';
    this._placeholder = config.placeholder || 'dd/mm/aaaa';
    this._onChange    = config.onChange    || null;
    this._maxHoy      = config.maxHoy      || null;

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

    // Aviso de fecha futura (#824). Va FUERA del wrap a propósito: la X de
    // limpiar se posiciona respecto a él (top: 50%), y un mensaje dentro lo
    // descentraría al aparecer. Mismo aspecto que el error del wizard paso 2,
    // que es el patrón de la casa para el mensaje de una EntradaFecha.
    this._aviso = null;
    if (this._maxHoy) {
      this._aviso = document.createElement('div');
      this._aviso.className = 'text-danger small mt-1 ef-aviso';
      this._aviso.style.display = 'none';
      this._contenedor.insertAdjacentElement('afterend', this._aviso);
    }
  }

  _mostrarAvisoFutura() {
    if (!this._aviso) return;
    const [y, m, d] = this._maxHoy.split('-');
    this._aviso.textContent = `No puede ser posterior a ${d}/${m}/${y}.`;
    this._aviso.style.display = '';
  }

  _ocultarAviso() {
    if (this._aviso) this._aviso.style.display = 'none';
  }

  // ── Eventos ───────────────────────────────────────────────────
  _conectar() {
    this._input.addEventListener('blur',    () => this._alSalir());
    this._input.addEventListener('focus',   () => {
      this._input.classList.remove('is-invalid');
      this._ocultarAviso();
    });
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
    if (r && !this._esFutura(r.iso)) {
      this._ocultarAviso();
      this._input.classList.remove('is-invalid');
      this._input.value  = r.display;
      this._hidden.value = r.iso;
      this._btnX.style.display = '';
      if (this._onChange) this._onChange(r.iso);
    } else {
      this._input.classList.add('is-invalid');
      this._hidden.value = '';
      if (r) {
        // Bien formada pero futura: se deja escrita —borrarla obligaría a
        // teclearla entera para corregir un dígito— y se explica el porqué.
        this._input.value = r.display;
        this._mostrarAvisoFutura();
      } else {
        this._ocultarAviso();
      }
    }
  }

  // Comparación de cadenas ISO — 'AAAA-MM-DD' ordena lexicográficamente igual
  // que cronológicamente, y así no hay husos horarios de por medio.
  _esFutura(iso) {
    return !!this._maxHoy && iso > this._maxHoy;
  }

  _limpiarEstado() {
    this._input.classList.remove('is-invalid');
    this._hidden.value = '';
    this._btnX.style.display = 'none';
    this._ocultarAviso();
  }

  // ── API pública ───────────────────────────────────────────────
  getValue() { return this._hidden.value; }

  setValue(iso) {
    const m = iso && iso.match(/^(\d{4})-(\d{2})-(\d{2})$/);
    if (!m) return;
    const [, y, mo, d] = m;
    this._input.value  = `${d}/${mo}/${y}`;
    this._hidden.value = iso;
    this._btnX.style.display = '';
    // Aquí se avisa pero NO se rechaza, al revés que al teclear (#824): setValue
    // carga valores que ya existen —un documento antiguo con fecha futura, el
    // autorrelleno del parseo de un justificante— y vaciar el hidden haría que
    // guardar sin tocar el campo borrase la fecha en silencio. Conservado, el
    // intento de guardarla lo rechaza el invariante del modelo, que es quien
    // debe decidirlo.
    if (this._esFutura(iso)) {
      this._input.classList.add('is-invalid');
      this._mostrarAvisoFutura();
    } else {
      this._input.classList.remove('is-invalid');
      this._ocultarAviso();
    }
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

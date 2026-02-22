/**
 * MunicipiosSelector — Gestor de municipios afectados en la vista de edición
 *
 * Usa SelectorBusqueda (debe cargarse antes) para los controles de provincia
 * y municipio. Gestiona una lista acumulativa con checkboxes para borrado.
 *
 * Uso:
 *   const selector = new MunicipiosSelector();
 *   selector.inicializar(municipiosExistentes);  // En edición
 */
class MunicipiosSelector {

    constructor() {
        this.btnBorrar        = document.getElementById('btn_borrar_municipios');
        this.listaMunicipios  = document.getElementById('lista_municipios');
        this.campoObligatorio = document.getElementById('campo_obligatorio');
        this.formulario       = document.getElementById('form_expediente');

        this.municipiosSeleccionados = new Map(); // { id: {nombre, codigo} }

        this._construirSelectores();
        this._bindEventos();
    }

    // ── Selectores encadenados provincia → municipio ──────────────────────

    _construirSelectores() {
        // Selector de municipio: se habilita cuando se elige provincia
        this.sbMunicipio = new SelectorBusqueda('#sb-municipio', [], {
            placeholder: '— Seleccione primero una provincia —',
            onChange: (v, t) => {
                if (!v) return;
                this._anadirMunicipio(v, t);
                this.sbMunicipio.clear();  // limpia sin perder las opciones de la provincia
            }
        });
        this.sbMunicipio.disable();

        // Selector de provincia: al seleccionar carga los municipios
        this.sbProvincia = new SelectorBusqueda('#sb-provincia', [], {
            placeholder: '— Seleccione una provincia —',
            onChange: async (v, t) => {
                this.sbMunicipio.setOpciones([]);
                if (!t) { this.sbMunicipio.disable(); return; }
                try {
                    const resp = await fetch(`/api/municipios?provincia=${encodeURIComponent(t)}`);
                    const data = await resp.json();
                    this.sbMunicipio.setOpciones(
                        data.map(m => ({ v: String(m.id), t: `${m.nombre} (${m.codigo})` }))
                    );
                    this.sbMunicipio.enable();
                } catch (e) {
                    console.error('Error cargando municipios:', e);
                }
            }
        });

        // Cargar provincias desde API al inicio
        fetch('/api/provincias')
            .then(r => r.json())
            .then(lista => this.sbProvincia.setOpciones(lista.map(n => ({ v: n, t: n }))))
            .catch(e => console.error('Error cargando provincias:', e));
    }

    // ── Eventos ───────────────────────────────────────────────────────────

    _bindEventos() {
        this.btnBorrar.addEventListener('click', () => this._borrarSeleccionados());

        this.formulario.addEventListener('submit', (e) => {
            if (!this._validarAntesSubmit()) e.preventDefault();
        });
    }

    // ── Gestión de la lista de municipios ─────────────────────────────────

    _anadirMunicipio(id, texto) {
        if (this.municipiosSeleccionados.has(id)) return;

        // El texto tiene formato "Nombre (COD)" — separar ambos campos
        const match = texto.match(/^(.+?)\s+\(([^)]+)\)$/);
        this.municipiosSeleccionados.set(id, {
            nombre: match ? match[1] : texto,
            codigo: match ? match[2] : ''
        });

        this._actualizarLista();
        this._actualizarObligatorio();
    }

    _actualizarLista() {
        this.listaMunicipios.innerHTML = '';

        if (this.municipiosSeleccionados.size === 0) {
            this.listaMunicipios.innerHTML =
                '<li class="list-group-item text-muted"><em>No hay municipios añadidos</em></li>';
            this.btnBorrar.disabled = true;
            return;
        }

        this.municipiosSeleccionados.forEach((mun, id) => {
            const li = document.createElement('li');
            li.className = 'list-group-item d-flex justify-content-between align-items-center';
            li.innerHTML = `
                <div>
                    <input type="checkbox" class="form-check-input me-2" data-municipio-id="${id}">
                    <strong>${mun.nombre}</strong>
                    ${mun.codigo ? `<small class="text-muted ms-2">(${mun.codigo})</small>` : ''}
                </div>
                <input type="hidden" name="municipios[]" value="${id}">
            `;
            this.listaMunicipios.appendChild(li);
        });

        // Activar botón borrar cuando haya checkboxes marcados
        this.listaMunicipios.querySelectorAll('input[type="checkbox"]').forEach(cb => {
            cb.addEventListener('change', () => {
                const alguno = Array.from(
                    this.listaMunicipios.querySelectorAll('input[type="checkbox"]')
                ).some(c => c.checked);
                this.btnBorrar.disabled = !alguno;
            });
        });
        this.btnBorrar.disabled = true;
    }

    _borrarSeleccionados() {
        this.listaMunicipios.querySelectorAll('input[type="checkbox"]:checked').forEach(cb => {
            this.municipiosSeleccionados.delete(cb.dataset.municipioId);
        });
        this._actualizarLista();
        this._actualizarObligatorio();
    }

    _actualizarObligatorio() {
        this.campoObligatorio.innerHTML = this.municipiosSeleccionados.size === 0
            ? '<span class="text-danger">*</span> Campo obligatorio'
            : '<span class="text-success">✔</span> Campo completado';
    }

    _validarAntesSubmit() {
        if (this.municipiosSeleccionados.size === 0) {
            alert('⚠️ Debe añadir al menos un municipio afectado');
            this.campoObligatorio.scrollIntoView({ behavior: 'smooth', block: 'center' });
            return false;
        }
        return true;
    }

    // ── API pública ───────────────────────────────────────────────────────

    /** Precarga municipios existentes al entrar en modo edición */
    inicializar(municipiosExistentes) {
        if (!municipiosExistentes || !municipiosExistentes.length) return;
        municipiosExistentes.forEach(m => {
            this.municipiosSeleccionados.set(m.id.toString(), {
                nombre: m.nombre,
                codigo: m.codigo
            });
        });
        this._actualizarLista();
        this._actualizarObligatorio();
    }
}

// Instanciar automáticamente al cargar la página
document.addEventListener('DOMContentLoaded', () => {
    window.selectorMunicipios = new MunicipiosSelector();
});

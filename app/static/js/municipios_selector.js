/**
 * Selector de Municipios con Búsqueda Substring
 * 
 * Funcionalidad:
 * - Dropdown provincia con búsqueda case-insensitive
 * - Dropdown municipio filtrado por provincia
 * - Lista acumulativa de municipios seleccionados
 * - Checkboxes para borrado múltiple
 * - Validación obligatoriedad antes de submit
 * - Hidden inputs para POST del formulario
 * 
 * Uso:
 *   const selector = new MunicipiosSelector();
 *   selector.inicializar(municipiosExistentes);  // En edición
 */

class MunicipiosSelector {
    constructor() {
        // Referencias DOM
        this.selectProvincia = document.getElementById('select_provincia');
        this.selectMunicipio = document.getElementById('select_municipio');
        this.inputBuscadorProvincia = document.getElementById('buscador_provincia');
        this.inputBuscadorMunicipio = document.getElementById('buscador_municipio');
        this.btnAnadir = document.getElementById('btn_anadir_municipio');
        this.btnBorrar = document.getElementById('btn_borrar_municipios');
        this.listaMunicipios = document.getElementById('lista_municipios');
        this.campoObligatorio = document.getElementById('campo_obligatorio');
        this.formulario = document.getElementById('form_expediente');
        
        // Estado
        this.municipiosSeleccionados = new Map(); // {id: {nombre, provincia, codigo}}
        this.todasProvincias = [];
        this.todosMunicipios = [];
        
        // Bind eventos
        this.bindEventos();
        
        // Cargar provincias al inicio
        this.cargarProvincias();
    }
    
    bindEventos() {
        // Búsqueda provincia
        this.inputBuscadorProvincia.addEventListener('input', () => {
            this.filtrarProvincias();
        });

        // Teclado en buscador provincia: ArrowDown/Enter pasan el foco al select
        this.inputBuscadorProvincia.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowDown' || e.key === 'Enter') {
                e.preventDefault();
                const primera = this.selectProvincia.querySelector('option:not([value=""])');
                if (primera) {
                    this.selectProvincia.value = primera.value;
                    this.selectProvincia.dispatchEvent(new Event('change'));
                    this.selectProvincia.focus();
                }
            }
        });

        // Cambio provincia
        this.selectProvincia.addEventListener('change', () => {
            this.onCambioProvincia();
        });

        // Teclado en select provincia: Escape vuelve al buscador
        this.selectProvincia.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                e.preventDefault();
                this.inputBuscadorProvincia.focus();
            }
        });

        // Búsqueda municipio
        this.inputBuscadorMunicipio.addEventListener('input', () => {
            this.filtrarMunicipios();
        });

        // Teclado en buscador municipio: ArrowDown/Enter pasan el foco al select
        this.inputBuscadorMunicipio.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowDown' || e.key === 'Enter') {
                e.preventDefault();
                const primera = this.selectMunicipio.querySelector('option:not([value=""])');
                if (primera) {
                    this.selectMunicipio.value = primera.value;
                    this.selectMunicipio.dispatchEvent(new Event('change'));
                    this.selectMunicipio.focus();
                }
            }
        });

        // Cambio municipio (habilitar botón añadir)
        this.selectMunicipio.addEventListener('change', () => {
            this.btnAnadir.disabled = !this.selectMunicipio.value;
        });

        // Teclado en select municipio: Enter añade; Escape vuelve al buscador
        this.selectMunicipio.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.anadirMunicipio();
                this.inputBuscadorMunicipio.focus();
            }
            if (e.key === 'Escape') {
                e.preventDefault();
                this.inputBuscadorMunicipio.focus();
            }
        });

        // Botón añadir
        this.btnAnadir.addEventListener('click', () => {
            this.anadirMunicipio();
        });
        
        // Botón borrar
        this.btnBorrar.addEventListener('click', () => {
            this.borrarMunicipiosSeleccionados();
        });
        
        // Validación submit formulario
        this.formulario.addEventListener('submit', (e) => {
            if (!this.validarAntesSubmit()) {
                e.preventDefault();
            }
        });
    }
    
    async cargarProvincias() {
        try {
            const response = await fetch('/api/provincias');
            this.todasProvincias = await response.json();
            this.renderProvincias(this.todasProvincias);
        } catch (error) {
            console.error('Error cargando provincias:', error);
            alert('❌ Error al cargar provincias');
        }
    }
    
    renderProvincias(provincias) {
        this.selectProvincia.innerHTML = '<option value="">-- Seleccione provincia --</option>';
        provincias.forEach(provincia => {
            const option = document.createElement('option');
            option.value = provincia;
            option.textContent = provincia;
            this.selectProvincia.appendChild(option);
        });
    }
    
    filtrarProvincias() {
        const query = this.inputBuscadorProvincia.value.toLowerCase();
        const provinciasFiltradas = this.todasProvincias.filter(p => 
            p.toLowerCase().includes(query)
        );
        this.renderProvincias(provinciasFiltradas);
    }
    
    async onCambioProvincia() {
        const provincia = this.selectProvincia.value;
        
        if (!provincia) {
            // Limpiar municipios
            this.selectMunicipio.innerHTML = '<option value="">-- Primero seleccione provincia --</option>';
            this.selectMunicipio.disabled = true;
            this.inputBuscadorMunicipio.disabled = true;
            this.inputBuscadorMunicipio.value = '';
            return;
        }
        
        // Habilitar dropdown municipios
        this.selectMunicipio.disabled = false;
        this.inputBuscadorMunicipio.disabled = false;
        this.inputBuscadorMunicipio.value = '';
        
        // Cargar municipios de la provincia
        try {
            const response = await fetch(`/api/municipios?provincia=${encodeURIComponent(provincia)}`);
            this.todosMunicipios = await response.json();
            this.renderMunicipios(this.todosMunicipios);
        } catch (error) {
            console.error('Error cargando municipios:', error);
            alert('❌ Error al cargar municipios');
        }
    }
    
    renderMunicipios(municipios) {
        this.selectMunicipio.innerHTML = '<option value="">-- Seleccione municipio --</option>';
        municipios.forEach(m => {
            const option = document.createElement('option');
            option.value = m.id;
            option.textContent = `${m.nombre} (${m.codigo})`;
            option.dataset.nombre = m.nombre;
            option.dataset.provincia = m.provincia;
            option.dataset.codigo = m.codigo;
            this.selectMunicipio.appendChild(option);
        });
    }
    
    filtrarMunicipios() {
        const query = this.inputBuscadorMunicipio.value.toLowerCase();
        const municipiosFiltrados = this.todosMunicipios.filter(m => 
            m.nombre.toLowerCase().includes(query)
        );
        this.renderMunicipios(municipiosFiltrados);
    }
    
    anadirMunicipio() {
        const municipioId = this.selectMunicipio.value;
        if (!municipioId) return;
        
        // Verificar duplicado
        if (this.municipiosSeleccionados.has(municipioId)) {
            alert('⚠️ Este municipio ya está en la lista');
            return;
        }
        
        // Obtener datos del option seleccionado
        const option = this.selectMunicipio.selectedOptions[0];
        const municipio = {
            nombre: option.dataset.nombre,
            provincia: option.dataset.provincia,
            codigo: option.dataset.codigo
        };
        
        // Añadir a colección
        this.municipiosSeleccionados.set(municipioId, municipio);
        
        // Actualizar UI
        this.actualizarListaMunicipios();
        this.actualizarCampoObligatorio();
        
        // Limpiar selección
        this.selectMunicipio.value = '';
        this.btnAnadir.disabled = true;
    }
    
    actualizarListaMunicipios() {
        // Limpiar lista
        this.listaMunicipios.innerHTML = '';
        
        if (this.municipiosSeleccionados.size === 0) {
            this.listaMunicipios.innerHTML = '<li class="list-group-item text-muted"><em>No hay municipios añadidos</em></li>';
            return;
        }
        
        // Renderizar cada municipio
        this.municipiosSeleccionados.forEach((municipio, id) => {
            const li = document.createElement('li');
            li.className = 'list-group-item d-flex justify-content-between align-items-center';
            
            li.innerHTML = `
                <div>
                    <input type="checkbox" class="form-check-input me-2" 
                           data-municipio-id="${id}">
                    <strong>${municipio.nombre}</strong>
                    <span class="badge bg-secondary ms-2">${municipio.provincia}</span>
                    <small class="text-muted ms-2">(${municipio.codigo})</small>
                </div>
                <input type="hidden" name="municipios[]" value="${id}">
            `;
            
            this.listaMunicipios.appendChild(li);
        });
        
        // Actualizar estado botón borrar
        this.actualizarBotonBorrar();
    }
    
    actualizarBotonBorrar() {
        const checkboxes = this.listaMunicipios.querySelectorAll('input[type="checkbox"]');
        const algunoMarcado = Array.from(checkboxes).some(cb => cb.checked);
        this.btnBorrar.disabled = !algunoMarcado;
        
        // Bind evento change a checkboxes
        checkboxes.forEach(cb => {
            cb.addEventListener('change', () => this.actualizarBotonBorrar());
        });
    }
    
    borrarMunicipiosSeleccionados() {
        const checkboxes = this.listaMunicipios.querySelectorAll('input[type="checkbox"]:checked');
        
        checkboxes.forEach(cb => {
            const municipioId = cb.dataset.municipioId;
            this.municipiosSeleccionados.delete(municipioId);
        });
        
        this.actualizarListaMunicipios();
        this.actualizarCampoObligatorio();
    }
    
    actualizarCampoObligatorio() {
        if (this.municipiosSeleccionados.size === 0) {
            this.campoObligatorio.innerHTML = '<span class="text-danger">*</span> Campo obligatorio';
        } else {
            this.campoObligatorio.innerHTML = '<span class="text-success">✔</span> Campo completado';
        }
    }
    
    validarAntesSubmit() {
        if (this.municipiosSeleccionados.size === 0) {
            alert('⚠️ Debe añadir al menos un municipio afectado');
            this.campoObligatorio.scrollIntoView({ behavior: 'smooth', block: 'center' });
            return false;
        }
        return true;
    }
    
    // Método para inicializar con municipios existentes (modo edición)
    inicializar(municipiosExistentes) {
        if (!municipiosExistentes || municipiosExistentes.length === 0) return;
        
        municipiosExistentes.forEach(m => {
            this.municipiosSeleccionados.set(m.id.toString(), {
                nombre: m.nombre,
                provincia: m.provincia,
                codigo: m.codigo
            });
        });
        
        this.actualizarListaMunicipios();
        this.actualizarCampoObligatorio();
    }
}

// Instanciar automáticamente al cargar la página
document.addEventListener('DOMContentLoaded', () => {
    window.selectorMunicipios = new MunicipiosSelector();
});

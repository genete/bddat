# CHANGELOG - Fix Email Duplicado en Usuarios

**Fecha**: 22 de enero de 2026  
**Issues relacionados**: #12, #13  
**Pull Request**: #18  
**Rama**: `fix/email-unique-constraint-issues-12-13`

---

## Problema Identificado

### Síntomas

Al intentar editar usuarios (cambiar siglas, modificar contraseña, etc.) se producía el siguiente error:

```
Error al actualizar usuario: (psycopg2.errors.UniqueViolation) 
llave duplicada viola restricción de unicidad «usuarios_email_key» 
DETAIL: Ya existe la llave (email)=().
```

### Casos afectados

1. **Issue #12**: Al cambiar siglas y contraseña simultáneamente
2. **Issue #13**: Al modificar siglas de un usuario sin email

### Causa Raíz

- La tabla `usuarios` tiene constraint `UNIQUE` en el campo `email`
- Múltiples usuarios tenían `email = ''` (cadena vacía)
- PostgreSQL considera múltiples cadenas vacías como valores idénticos
- Al intentar actualizar cualquier usuario con email vacío, se violaba el constraint UNIQUE

---

## Solución Implementada

### 1. Modelo Usuario (`app/models/usuarios.py`)

**Cambio principal**: Property setter que convierte emails vacíos a `NULL`

```python
# Antes: campo simple
email = db.Column(db.String(120), unique=True, nullable=True)

# Después: property con validación
_email = db.Column('email', db.String(120), unique=True, nullable=True)

@property
def email(self):
    return self._email

@email.setter
def email(self, value):
    """Convierte cadenas vacías a None para evitar violación de constraint UNIQUE"""
    if value == '' or (isinstance(value, str) and value.strip() == ''):
        self._email = None
    else:
        self._email = value
```

**Ventajas**:
- PostgreSQL trata múltiples valores `NULL` como distintos (no viola UNIQUE)
- Aplica automáticamente tanto en creación como en edición
- No requiere cambios en la estructura de la BD

### 2. Rutas (`app/routes/usuarios.py`)

**Añadido**: Importación de `IntegrityError`
```python
from sqlalchemy.exc import IntegrityError
```

**Cambios en `index()` (creación)**:

1. Variable `error_email` para capturar errores específicos
2. Asignación explícita del email (el setter lo convierte)
   ```python
   nuevo_usuario.email = email  # El setter convertirá '' a None
   ```
3. Captura específica de error de email duplicado:
   ```python
   except IntegrityError as e:
       db.session.rollback()
       if 'usuarios_email_key' in str(e.orig):
           error_email = 'Este email ya está registrado por otro usuario. Usa uno diferente o déjalo vacío.'
           return render_template('usuarios/index.html', 
                                usuarios=usuarios, 
                                roles=todos_los_roles,
                                form_data=form_data,
                                error_email=error_email,
                                show_modal=True)
   ```

**Cambios en `editar()` (actualización)**:

1. Variable `error_email` para capturar errores
2. Asignación del email con conversión automática:
   ```python
   usuario.email = request.form.get('email')  # El setter convertirá '' a None
   ```
3. Captura de error con preservación de datos:
   ```python
   except IntegrityError as e:
       db.session.rollback()
       if 'usuarios_email_key' in str(e.orig):
           error_email = 'Este email ya está registrado por otro usuario. Usa uno diferente o déjalo vacío.'
           form_data = {...}  # Preservar todos los datos
           return render_template('usuarios/editar.html', 
                                usuario=usuario, 
                                roles=todos_los_roles,
                                error_email=error_email,
                                form_data=form_data)
   ```

### 3. Template de Edición (`app/templates/usuarios/editar.html`)

**Cambio en campo email**:
```html
<input type="email" 
       class="form-control {% if error_email %}is-invalid{% endif %}" 
       id="email" 
       name="email" 
       value="{{ form_data.email if form_data else (usuario.email or '') }}" 
       placeholder="usuario@ejemplo.com">
{% if error_email %}
<div class="invalid-feedback">
    {{ error_email }}
</div>
{% endif %}
```

**Comportamiento**:
- Clase `is-invalid` marca el campo en rojo
- Mensaje `invalid-feedback` aparece bajo el campo
- Desaparece automáticamente al editar (Bootstrap nativo)

### 4. Template de Creación (`app/templates/usuarios/index.html`)

**Añadido**: Campo email en modal (antes no existía)
```html
<div class="row mb-3">
    <div class="col-md-12">
        <label for="email" class="form-label">Email</label>
        <input type="email" 
               class="form-control {% if error_email %}is-invalid{% endif %}" 
               id="email" 
               name="email" 
               placeholder="usuario@ejemplo.com"
               value="{{ form_data.email if form_data else '' }}">
        {% if error_email %}
        <div class="invalid-feedback">
            {{ error_email }}
        </div>
        {% endif %}
    </div>
</div>
```

---

## Migración de Datos

**Comando SQL necesario** (ejecutar antes de merge):

```sql
UPDATE usuarios SET email = NULL WHERE email = '';
```

**Resultado esperado**:
```
UPDATE n
```
Donde `n` es el número de usuarios con email vacío convertidos a NULL.

---

## Comportamiento Antes vs Después

### Antes del Fix

❌ **Problema**: Error al guardar usuario  
❌ **UX**: Diálogo se cierra perdiendo todos los datos ingresados  
❌ **Feedback**: Mensaje genérico sin indicar campo responsable  
❌ **Datos**: Múltiples usuarios con `email = ''` causan conflictos  

### Después del Fix

✅ **Prevención**: Email vacío se guarda como `NULL` automáticamente  
✅ **UX**: Diálogo permanece abierto con todos los datos preservados  
✅ **Feedback**: Mensaje claro bajo el campo email responsable  
✅ **Datos**: Múltiples `NULL` permitidos por PostgreSQL (no violan UNIQUE)  
✅ **Experiencia**: Mensaje tipo tooltip no intrusivo  

---

## Testing Realizado

### Casos de Prueba

- [x] **Crear usuario sin email** (campo vacío) → Se guarda correctamente como NULL
- [x] **Editar usuario dejando email vacío** → Se guarda como NULL sin errores
- [x] **Crear dos usuarios con mismo email** → Muestra error en campo, modal permanece abierto
- [x] **Editar usuario con email existente** → Muestra error en campo, formulario permanece abierto
- [x] **Preservación de datos** → Todos los campos mantienen sus valores cuando hay error
- [x] **Cambiar siglas + contraseña** (Issue #12) → Funciona correctamente
- [x] **Editar usuario sin email** (Issue #13) → Funciona correctamente

### Verificaciones Adicionales

- Email vacío en BD se almacena como `NULL`
- Múltiples usuarios pueden tener email `NULL` sin conflictos
- Mensaje de error desaparece al editar el campo
- Campos de contraseña se limpian adecuadamente (Issue #12)
- Otros campos se preservan correctamente

---

## Commits del Fix

1. `fc190de` - MODELO: Convertir email vacío a NULL automáticamente
2. `56207bf` - RUTA: Capturar error email duplicado y mantener diálogo abierto
3. `84d1f67` - TEMPLATE: Añadir validación visual de email duplicado (edición)
4. `b9f9e39` - TEMPLATE: Añadir validación de email en modal creación

---

## Impacto

### Archivos Modificados

- `app/models/usuarios.py` - Property setter email
- `app/routes/usuarios.py` - Captura IntegrityError + preservación form_data
- `app/templates/usuarios/editar.html` - Validación visual email
- `app/templates/usuarios/index.html` - Campo email + validación en modal

### Sin Cambios en BD

- No requiere migraciones de estructura
- Solo limpieza de datos existentes (SQL proporcionado)

### Compatibilidad

- ✅ Compatible con PostgreSQL (múltiples NULL permitidos en UNIQUE)
- ✅ No afecta funcionalidad existente
- ✅ Mejora UX sin cambios disruptivos

---

## Referencias

- **Issues cerrados**: #12, #13
- **Pull Request**: #18
- **Documentación del proyecto**: `Reglas De Desarrollo Con IA.docx`
- **Convenciones**: snake_case, validación no intrusiva, preservación de datos
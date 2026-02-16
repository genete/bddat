# Vista V0 - Login

## Información General

**Epic:** #93 - Sistema de Navegación UI Modular  
**Vista:** V0 - Login (Pantalla de autenticación)  
**Fecha creación:** 08/02/2026  
**Estado:** ✅ Completada  
**Rama:** `feature/epic-93-vista-v0-login`  

---

## Descripción

Pantalla de inicio de sesión (login) del sistema BDDAT con diseño split-screen moderno. La zona izquierda (60%) muestra información de bienvenida, ayuda y enlaces útiles. La zona derecha (40%) contiene el formulario de autenticación centrado. Utiliza el layout V2 (header + main + footer) pero simplificado sin breadcrumb ni menú de usuario.

---

## Características

### Layout
- **Base:** `layout/base_login.html` (V2 simplificado)
- **Header:** Logo BDDAT únicamente (sin breadcrumb, sin usuario)
- **Footer:** Igual que V1/V2 (copyright + enlaces)
- **Split-screen:** 60% izquierda + 40% derecha
- **Responsive:** Columnas apiladas en mobile (izquierda arriba, derecha abajo)

### Zona Izquierda (60%)
- **Bienvenida:** Título grande "Bienvenido a BDDAT"
- **Descripción:** Sistema de tramitación administrativa AT
- **Información de Acceso:**
  - Instrucciones para usar siglas de usuario
  - Navegadores recomendados
  - Resolución mínima
- **Ayuda:**
  - Enlace recuperar contraseña (futuro)
  - Contacto soporte técnico
  - Manual de usuario (futuro)
- **Aviso:** Acceso restringido personal autorizado

### Zona Derecha (40%)
- **Card centrada** con formulario login
- **Campos:**
  - Siglas de usuario (required, autofocus)
  - Contraseña (required, type=password)
- **Botón:** "Entrar" (verde corporativo)
- **Enlace:** "¿Olvidaste tu contraseña?" (debajo formulario)
- **Mensajes flash:** Errores/éxito de autenticación

### Colores
- **Verde corporativo Junta de Andalucía:** `#087021`
- **Variables CSS:** Reutiliza `v2-theme.css`
- **Gradiente fondo izquierda:** De `var(--primary-lighter)` a blanco
- **Hover effects:** Botón con elevación y sombra

---

## Estructura de Archivos

### Archivos NUEVOS

```
app/
├── static/
│   └── css/
│       └── v0-login.css              # Estilos específicos login
└── templates/
    ├── auth/
    │   └── login_v0.html             # Template login V0
    └── layout/
        └── base_login.html           # Base V2 sin breadcrumb/usuario
```

### Archivos MODIFICADOS

```
app/
└── routes/
    └── auth.py                       # Apunta a login_v0.html
```

### Archivos NO TOCADOS (convivencia)

```
app/
└── templates/
    └── auth/
        └── login.html                    # Login antiguo (intacto)
```

---

## Jerarquía de Niveles

### Estructura HTML

```
A: app-container (grid principal)
├── B.1: app-header (sticky top) ← Header simplificado (solo logo)
├── B.2: app-main (scrollable)
│   └── login-container (grid 60/40)
│       ├── login-info (zona izquierda)
│       │   └── info-content (bienvenida + ayuda)
│       └── login-form-zone (zona derecha)
│           └── login-card (formulario centrado)
└── B.3: app-footer (sticky bottom) ← Footer V2
```

### Diferencias con otras vistas

**V0 (Login):**
- Header sin breadcrumb ni usuario (más simple)
- Split-screen 60/40 (información + formulario)
- Sin autenticación requerida
- Pantalla pública (acceso sin login)

**V1 (Dashboard):**
- Header completo (breadcrumb + usuario)
- Grid de cards
- Requiere autenticación
- Primera pantalla post-login

**V2 (Listado):**
- Header completo
- Tabla con scroll infinito
- Requiere autenticación
- Listado de datos

---

## CSS v0-login.css

### Estructura Split-Screen

```css
.login-container {
  display: grid;
  grid-template-columns: 60% 40%;
  min-height: calc(100vh - var(--header-height) - var(--footer-height));
}
```

### Zona Izquierda

```css
.login-info {
  background: linear-gradient(135deg, var(--primary-lighter) 0%, #ffffff 100%);
  padding: 4rem;
  display: flex;
  flex-direction: column;
  justify-content: center;
}
```

**Elementos:**
- `.welcome-title` - Título grande (2.5rem) con icono
- `.welcome-subtitle` - Descripción del sistema
- `.info-section` - Bloques de información con iconos
- `.info-footer` - Aviso de acceso restringido

### Zona Derecha

```css
.login-form-zone {
  background: var(--bg-page);
  padding: 4rem 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-card {
  width: 100%;
  max-width: 420px;
  background: var(--bg-card);
  border-radius: var(--border-radius-lg);
  padding: 2.5rem;
  box-shadow: var(--shadow-lg);
}
```

**Elementos:**
- `.login-card-header` - Título "Iniciar Sesión"
- `.login-form` - Formulario con campos
- `.form-control` - Inputs con focus verde corporativo
- `.btn-login` - Botón con hover elevation
- `.login-links` - Enlaces secundarios

### Botón Login

```css
.btn-login {
  width: 100%;
  padding: 0.875rem 1.5rem;
  background: var(--primary);
  background-image: var(--gradient);
  color: var(--text-inverse);
  transition: all 0.3s ease;
}

.btn-login:hover {
  background: var(--primary-hover);
  transform: translateY(-2px);
  box-shadow: var(--shadow);
}
```

### Responsive

```css
@media (max-width: 991px) {
  .login-container {
    grid-template-columns: 1fr;
    grid-template-rows: auto 1fr;
  }
}
```

---

## Flujo de Autenticación
### GET /auth/login

1. Usuario accede a `/auth/login`
2. Se renderiza `login_v0.html`
3. Se muestra split-screen con información y formulario

### POST /auth/login

1. Usuario introduce siglas + contraseña
2. Backend valida credenciales:
   - Usuario existe?
   - Contraseña correcta?
   - Usuario activo?
3. **Si OK:**
   - `login_user()` (Flask-Login)
   - Flash: "Bienvenido, {nombre}!"
   - Redirect: `/dashboard` (o `next` param)
4. **Si ERROR:**
   - Flash: "Siglas o contraseña incorrectos"
   - Renderiza login de nuevo con mensaje error

### Código Backend (auth.py)

```python
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        siglas = request.form.get('siglas')
        password = request.form.get('password')
        
        usuario = Usuario.query.filter_by(siglas=siglas).first()
        
        if usuario and usuario.check_password(password):
            if not usuario.activo:
                flash('Cuenta desactivada', 'danger')
                return redirect(url_for('auth.login'))
            
            login_user(usuario)
            flash(f'Bienvenido, {usuario.nombre}!', 'success')
            
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard.index'))
        else:
            flash('Siglas o contraseña incorrectos.', 'danger')
    
    return render_template('auth/login_v0.html')
```

---

## Mensajes Flash

### Tipos de Mensajes

| Tipo | Clase CSS | Uso |
|------|-----------|-----|
| `success` | `alert-success` | Login correcto, bienvenida |
| `danger` | `alert-danger` | Credenciales incorrectas, cuenta desactivada |
| `info` | `alert-info` | Logout correcto |

### Ejemplo Template

```jinja
{% with messages = get_flashed_messages(with_categories=true) %}
    {% if messages %}
        {% for category, message in messages %}
        <div class="alert alert-{{ category }}" role="alert">
            {{ message }}
        </div>
        {% endfor %}
    {% endif %}
{% endwith %}
```

---

## Testing

### Casos de Prueba

#### 1. Testing Visual
- ✅ Split-screen 60/40 funciona
- ✅ Header simplificado (solo logo, sin breadcrumb/usuario)
- ✅ Footer V2 visible
- ✅ Zona izquierda: bienvenida + información visible
- ✅ Zona derecha: formulario centrado en card
- ✅ Gradiente fondo izquierda correcto
- ✅ Iconos Font Awesome visibles

#### 2. Testing Funcional
- ✅ GET `/auth/login` renderiza login_v0.html
- ✅ POST con credenciales correctas → login exitoso → redirect dashboard
- ✅ POST con credenciales incorrectas → mensaje error
- ✅ Usuario desactivado → mensaje error específico
- ✅ Logout → redirect a login con mensaje info

#### 3. Testing Responsive
- ✅ Desktop (>991px): Split-screen 60/40
- ✅ Tablet/Mobile (≤991px): Columnas apiladas (izquierda arriba)
- ✅ Mobile pequeño (<576px): Títulos y padding ajustados

#### 4. Testing Seguridad
- ✅ Campos con `required`
- ✅ Password con `type="password"`
- ✅ Autocomplete: `username` y `current-password`
- ✅ Backend valida usuario activo
- ✅ Backend valida credenciales con `check_password()`

---

## Accesibilidad

### Focus Visible
```css
.form-control:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 0.25rem var(--focus-ring);
}

.btn-login:focus-visible {
  outline: 2px solid var(--primary);
  outline-offset: 2px;
}
```

### Semántica HTML
- `<form>` con `method="POST"`
- `<label>` con `for` asociado a inputs
- `<input>` con `required` y `autofocus`
- `<button type="submit">`
- Mensajes flash con `role="alert"`

### Atributos ARIA
- Autocomplete para navegadores/gestores contraseñas
- Focus automático en campo "Siglas"
- Roles ARIA en alertas

---

## Convivencia con Sistema Antiguo

### Estrategia No Destructiva

**Archivos nuevos:**
- `v0-login.css` (no toca estilos antiguos)
- `login_v0.html` (no toca `login.html`)
- `base_login.html` (no toca `base.html`)

**Login antiguo intacto:**
- `app/templates/auth/login.html` permanece sin cambios
- Si se revierte `auth.py`, vuelve a funcionar el antiguo

**Migración progresiva:**
- V0 activa por defecto en `auth.py`
- Sistema antiguo disponible cambiando 1 línea en `auth.py`

---

## Commits Realizados

### Rama: `feature/epic-93-vista-v0-login`

1. **[STYLE]** Crear CSS para Vista V0 Login con split-screen 60/40
2. **[TEMPLATE]** Crear base_login.html - layout V2 sin breadcrumb ni usuario
3. **[TEMPLATE]** Crear login_v0.html con split-screen 60/40 e información
4. **[RUTA]** Actualizar auth.py para usar login_v0.html (Vista V0)
5. **[DOCS]** Documentar Vista V0 (Login) - split-screen con información y formulario

---

## Próximos Pasos

### Fase Actual (Completada)
- ✅ Vista V0 (Login) implementada y funcional
- ✅ Testing completo visual y funcional
- ✅ Responsive completo
- ✅ Documentación creada
- ✅ Listo para PR a `develop`

### Funcionalidades Futuras (Login)
- **Recuperar contraseña:** Implementar flujo completo
- **Remember me:** Checkbox "Recordarme"
- **2FA:** Autenticación de dos factores
- **Captcha:** Anti-bot en intentos fallidos
- **Registro:** Autoregistro de usuarios (si aplica)

### Siguientes Vistas (Epic #93)
- **Vista V0:** Login ✅ COMPLETADA (este PR)
- **Vista V1:** Dashboard ✅ COMPLETADA (PR #98)
- **Vista V2:** Listado expedientes ✅ COMPLETADA (PR #97)
- **Vista V3:** Tramitación con sidebar acordeón (pendiente)

---

## Referencias

- **Epic #93:** Sistema de Navegación UI Modular
- **PR #97:** Vista V2 (Listado expedientes)
- **PR #98:** Vista V1 (Dashboard)
- **Issue #58:** Colores Junta de Andalucía
- **PATRONES_UI.md:** Especificación patrones UI
- **CSS_v2_GUIA_USO.md:** Guía CSS V2
- **VISTA_V1_DASHBOARD.md:** Documentación Vista V1

---

## Historial de Cambios

**08/02/2026 - Vista V0 Completada:**
- Implementado login con split-screen 60/40
- Zona izquierda: bienvenida + información + ayuda
- Zona derecha: formulario login centrado en card
- CSS específico v0-login.css
- Layout base_login.html (header simplificado)
- Testing completo visual, funcional y responsive
- Documentación completa creada
- Listo para PR a develop

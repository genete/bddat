"""
Helpers Jinja para montar islas React (#499, ADR-015).

- react_bundle(nombre): lee app/static/js/react/manifest.json y emite las
  etiquetas <link>/<script type=module> con el hash actual de esa isla.
- user_ctx_attrs(): emite los data-* (user, permisos, rol activo) que las islas
  leen vía shared/auth.js para condicionar la UI.

El manifest lo genera `npm run build` (script scripts/build_react.sh). El formato
es el manifest nativo de Vite: clave = ruta de entry, valor con file/name/css/imports.
"""
import json
import os

from flask import current_app, session, url_for
from flask_login import current_user
from markupsafe import Markup, escape

from app.utils.permisos import PERMISOS


def _ruta_manifest():
    return os.path.join(current_app.static_folder, 'js', 'react', 'manifest.json')


def _leer_manifest():
    # Sin caché a propósito: el fichero es pequeño y en desarrollo cambia con
    # cada "Build React". En producción el coste por request es despreciable.
    try:
        with open(_ruta_manifest(), encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, ValueError):
        current_app.logger.warning(
            'manifest.json de React no disponible (%s). ¿Ejecutaste "Build React"?',
            _ruta_manifest(),
        )
        return {}


def react_bundle(nombre):
    """Emite las etiquetas <link>/<script type=module> de la isla `nombre`.

    Devuelve Markup vacío (y loguea) si no hay manifest o la isla no existe,
    para que la página siga sirviéndose sin romperse.
    """
    manifest = _leer_manifest()
    entry = next(
        (v for v in manifest.values() if v.get('isEntry') and v.get('name') == nombre),
        None,
    )
    if entry is None:
        current_app.logger.warning("Isla React '%s' no está en manifest.json", nombre)
        return Markup('')

    def static_react(fichero):
        return url_for('static', filename=f'js/react/{fichero}')

    # CSS a enlazar: el de los chunks importados (transitivo) + el del propio entry,
    # sin duplicar. Cuando dos islas comparten una librería con CSS (p. ej. xyflow),
    # Vite extrae ese CSS al chunk compartido; si solo enlazáramos entry['css'] se
    # perdería. Recorremos imports en profundidad PRIMERO para que el CSS compartido
    # quede antes que el del entry y el tematizado de la isla pueda sobrescribirlo.
    css_files = []
    vistos = set()

    def recoger_css(nodo):
        for imp in nodo.get('imports', []):
            chunk = manifest.get(imp)
            if chunk:
                recoger_css(chunk)
        for css in nodo.get('css', []):
            if css not in vistos:
                vistos.add(css)
                css_files.append(css)

    recoger_css(entry)

    tags = []
    for css in css_files:
        tags.append(f'<link rel="stylesheet" href="{static_react(css)}">')
    # Precarga de los chunks compartidos (React, etc.) que el módulo importa.
    for imp in entry.get('imports', []):
        chunk_file = manifest.get(imp, {}).get('file')
        if chunk_file:
            tags.append(f'<link rel="modulepreload" href="{static_react(chunk_file)}">')
    # El entry, como módulo ES: el navegador resuelve sus imports automáticamente.
    tags.append(f'<script type="module" src="{static_react(entry["file"])}"></script>')
    return Markup('\n'.join(tags))


def user_ctx_attrs():
    """Emite data-user / data-permisos / data-rol del usuario y rol activo actuales.

    Las islas lo leen con shared/auth.js. NO es autenticación cliente: solo
    condiciona la UI; la autorización real la imponen los decoradores del backend.
    """
    if not current_user.is_authenticated:
        return Markup('')
    rol = session.get('rol_activo_nombre')
    permisos = sorted(n for n, roles in PERMISOS.items() if rol in roles)
    user = {
        'id': current_user.id,
        'siglas': current_user.siglas,
        'nombre_completo': f'{current_user.nombre} {current_user.apellido1}'.strip(),
    }
    attrs = {
        'data-user':     json.dumps(user, ensure_ascii=False),
        'data-permisos': json.dumps(permisos, ensure_ascii=False),
        'data-rol':      rol or '',
    }
    return Markup(' '.join(f'{k}="{escape(v)}"' for k, v in attrs.items()))

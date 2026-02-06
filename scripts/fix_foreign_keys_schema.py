#!/usr/bin/env python3
"""
Script para añadir referent_schema='public' a todas las ForeignKey en modelos.

PROPÓSITO:
    Sincronizar modelos Python con la BD después de aplicar migración que añade
    referent_schema='public' a todas las foreign keys.

USO:
    python scripts/fix_foreign_keys_schema.py
    
PRECAUCIÓN:
    - Hace backup de cada archivo antes de modificarlo (.bak)
    - Revisa los cambios con git diff antes de commitear
    - Solo procesa archivos en app/models/ (excepto __init__.py)
"""

import os
import re
from pathlib import Path

def fix_foreign_key_in_line(line):
    """
    Añade referent_schema='public' a ForeignKey si no lo tiene ya.
    
    Patrones a detectar:
        db.ForeignKey('public.tabla.campo')
        db.ForeignKey('public.tabla.campo', ...)
        
    Casos especiales:
        - Si ya tiene referent_schema, lo ignora
        - Si apunta a tabla sin 'public.' al inicio, lo ignora (tablas maestras sin schema explícito)
        - Maneja use_alter, ondelete, name, etc.
    """
    # Patrón: db.ForeignKey('public.XXXX.YYYY'
    pattern = r"db\.ForeignKey\('public\.([^']+)'"
    
    # Si ya tiene referent_schema, no tocar
    if 'referent_schema=' in line:
        return line
    
    # Si no es una FK a public, no tocar
    if not re.search(pattern, line):
        return line
    
    # Encontrar dónde insertar referent_schema
    # Casos:
    # 1. db.ForeignKey('public.tabla.campo')
    # 2. db.ForeignKey('public.tabla.campo', other_param=value)
    # 3. db.ForeignKey('public.tabla.campo', ondelete='CASCADE')
    
    # Buscar el patrón y determinar dónde insertar
    match = re.search(pattern, line)
    if not match:
        return line
    
    # Buscar el cierre del ForeignKey
    # Si termina con ')' sin más parámetros: añadir ", referent_schema='public'"
    # Si tiene más parámetros: añadir ", referent_schema='public'" después de la tabla
    
    # Patrón más específico: capturar todo el ForeignKey
    fk_pattern = r"(db\.ForeignKey\('public\.[^']+')(\)|,)"
    
    def replacer(m):
        fk_part = m.group(1)  # db.ForeignKey('public.tabla.campo')
        separator = m.group(2)  # ) o ,
        
        if separator == ')':
            # Caso: db.ForeignKey('public.tabla.campo')
            return f"{fk_part}, referent_schema='public')"
        else:
            # Caso: db.ForeignKey('public.tabla.campo', otros_params...)
            return f"{fk_part}, referent_schema='public',"
    
    return re.sub(fk_pattern, replacer, line)

def process_file(filepath):
    """Procesa un archivo de modelo añadiendo referent_schema donde corresponda."""
    # Leer contenido original
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Procesar línea por línea
    modified = False
    new_lines = []
    
    for line in lines:
        new_line = fix_foreign_key_in_line(line)
        if new_line != line:
            modified = True
        new_lines.append(new_line)
    
    if modified:
        # Hacer backup
        backup_path = f"{filepath}.bak"
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        # Escribir archivo modificado
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
        return True
    
    return False

def main():
    """Procesa todos los archivos de modelos."""
    models_dir = Path('app/models')
    
    if not models_dir.exists():
        print("❌ Error: No se encuentra el directorio app/models/")
        return
    
    print("🔍 Buscando archivos de modelos...")
    
    modified_files = []
    skipped_files = []
    
    for py_file in models_dir.glob('*.py'):
        # Ignorar __init__.py y archivos de backup
        if py_file.name == '__init__.py' or py_file.name.endswith('.bak'):
            continue
        
        print(f"   Procesando: {py_file.name}...", end=' ')
        
        if process_file(py_file):
            print("✅ MODIFICADO")
            modified_files.append(py_file.name)
        else:
            print("⏭️  Sin cambios")
            skipped_files.append(py_file.name)
    
    print("\n" + "="*60)
    print("📊 RESUMEN")
    print("="*60)
    print(f"✅ Archivos modificados: {len(modified_files)}")
    for f in modified_files:
        print(f"   - {f}")
    
    print(f"\n⏭️  Archivos sin cambios: {len(skipped_files)}")
    for f in skipped_files[:5]:  # Mostrar solo los primeros 5
        print(f"   - {f}")
    if len(skipped_files) > 5:
        print(f"   ... y {len(skipped_files) - 5} más")
    
    if modified_files:
        print("\n" + "="*60)
        print("⚠️  IMPORTANTE:")
        print("="*60)
        print("1. Se han creado backups (.bak) de los archivos modificados")
        print("2. Revisa los cambios con: git diff app/models/")
        print("3. Si todo está bien: git add app/models/*.py")
        print("4. Si algo salió mal: restaura desde los .bak")
        print("\n5. Después de revisar, borra los backups:")
        print("   rm app/models/*.bak")

if __name__ == '__main__':
    main()

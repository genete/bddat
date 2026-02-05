#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merge_tables.py - Reconstruye Tablas.md desde archivos individuales

DESCRIPCIÓN:
    Lee los archivos individuales de tablas (generados por split_tables.py)
    y los concatena en un único archivo Tablas.md, manteniendo el orden
    correcto y regenerando el índice automático.

CARACTERÍSTICAS:
    - Lee archivos con nomenclatura E_nnn (Estructura) y O_nnn (Operacional)
    - Escalabilidad infinita por categoría
    - Concatena: filosofía + tablas estructura + tablas operacionales
    - Genera índice automático con enlaces
    - Elimina metadatos de generación (comentarios HTML)
    - Añade header con fecha de regeneración
    - Valida que no falten tablas críticas

USO:
    # Modo básico (usa rutas por defecto)
    python scripts/merge_tables.py

    # Especificar rutas personalizadas
    python scripts/merge_tables.py --input docs/tablas/ --output docs/Tablas.md

    # Ver ayuda
    python scripts/merge_tables.py --help

ENTRADA:
    docs/fuentesIA/referencias/tablas/*.md

SALIDA:
    docs/fuentesIA/referencias/Tablas.md (regenerado)

FLUJO RECOMENDADO:
    1. Ejecutar split_tables.py (una vez, para crear estructura)
    2. Editar archivos individuales en tablas/
    3. Ejecutar merge_tables.py (cada vez que actualices una tabla)
    4. Commit de ambos: tablas/*.md y Tablas.md regenerado

AUTOR: Sistema BDDAT
VERSIÓN: 3.0
FECHA: 2026-02-01
"""

import re
import argparse
from datetime import datetime
from pathlib import Path


# ============================================================================
# CONFIGURACIÓN
# ============================================================================

# Tablas críticas que DEBEN existir (validación)
REQUIRED_TABLES = [
    'EXPEDIENTES', 'PROYECTOS', 'SOLICITUDES', 'DOCUMENTOS',
    'TAREAS', 'FASES', 'TRAMITES', 'USUARIOS'
]


# ============================================================================
# FUNCIONES DE LECTURA
# ============================================================================

def read_markdown_file(filepath):
    """
    Lee archivo markdown y elimina metadatos de generación automática.
    
    Args:
        filepath: Path al archivo .md
    
    Returns:
        str: Contenido limpio (sin comentarios HTML de metadatos)
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Eliminar bloque de metadatos <!-- ... -->
    content = re.sub(r'<!--.*?-->\s*', '', content, flags=re.DOTALL)
    
    return content.strip()


def extract_table_name_from_filename(filename):
    """
    Extrae nombre de tabla desde nombre de archivo con nomenclatura E_/O_.
    
    Args:
        filename: Nombre del archivo (ej: 'E_001_TIPOS_EXPEDIENTES.md', 'O_013_ENTIDADES.md')
    
    Returns:
        tuple: (prefix, table_name) o (None, None) si formato inválido
               prefix: 'E_001' u 'O_013'
               table_name: 'TIPOS_EXPEDIENTES' o 'ENTIDADES'
    """
    match = re.match(r'^([EO]_\d{3})_([A-Z_]+)\.md$', filename)
    if match:
        return match.group(1), match.group(2)
    return None, None


def collect_tables(input_dir):
    """
    Recolecta y organiza archivos de tablas.
    
    Args:
        input_dir: Path al directorio con archivos .md
    
    Returns:
        tuple: (philosophy_content, tables_estructura, tables_operacionales)
               donde tables_* son dicts {name: content} ordenados
    
    Raises:
        FileNotFoundError: Si no existe el directorio
        ValueError: Si falta el archivo de filosofía
    """
    if not input_dir.exists():
        raise FileNotFoundError(f"No existe directorio: {input_dir}")
    
    philosophy_content = None
    tables_estructura = {}  # {name: content}
    tables_operacionales = {}
    
    # Leer todos los archivos .md en orden
    for filepath in sorted(input_dir.glob('*.md')):
        filename = filepath.name
        
        # Filosofía (00_FILOSOFIA.md)
        if filename == '00_FILOSOFIA.md':
            philosophy_content = read_markdown_file(filepath)
            print(f"   ✓ {filename}")
            continue
        
        # Extraer nombre de tabla
        prefix, table_name = extract_table_name_from_filename(filename)
        if not table_name:
            print(f"   ⚠️  Ignorado (formato no válido): {filename}")
            continue
        
        # Leer contenido
        content = read_markdown_file(filepath)
        
        # Clasificar estructura vs operacional (prefijo E_ vs O_)
        if prefix.startswith('E_'):
            tables_estructura[table_name] = content
            print(f"   ✓ {filename} [ESTRUCTURA]")
        elif prefix.startswith('O_'):
            tables_operacionales[table_name] = content
            print(f"   ✓ {filename} [OPERACIONAL]")
    
    # Validar filosofía
    if not philosophy_content:
        raise ValueError("No se encontró archivo 00_FILOSOFIA.md")
    
    return philosophy_content, tables_estructura, tables_operacionales


# ============================================================================
# FUNCIONES DE GENERACIÓN
# ============================================================================

def generate_header():
    """
    Genera encabezado del documento con metadatos de generación.
    
    Returns:
        str: Header en formato markdown
    """
    timestamp = datetime.now().strftime('%d/%m/%Y')
    time_full = datetime.now().strftime('%d/%m/%Y %H:%M')
    
    return f"""# Definiciones de Tablas Principales v3.1

**Sistema de Tramitación de Expedientes de Alta Tensión (BDDAT)**  
**Formato agnóstico a la base de datos**  
**Fecha:** {timestamp}  
**Generado automáticamente:** {time_full} por merge_tables.py

---
"""


def generate_table_index(tables_estructura, tables_operacionales):
    """
    Genera índice markdown automático con enlaces internos.
    
    Args:
        tables_estructura: Lista de nombres de tablas de estructura
        tables_operacionales: Lista de nombres de tablas operacionales
    
    Returns:
        str: Sección de índice en formato markdown
    """
    index_lines = [
        '## Índice',
        '',
        '- [Filosofía del Diseño](#filosofía-del-diseño)',
        '- [Tablas de Estructura](#tablas-de-estructura)'
    ]
    
    # Añadir tablas de estructura al índice
    for table_name in tables_estructura:
        anchor = table_name.lower().replace('_', '')
        index_lines.append(f'  - [{table_name}](#{anchor})')
    
    index_lines.extend([
        '- [Tablas Operacionales](#tablas-operacionales)'
    ])
    
    # Añadir tablas operacionales al índice
    for table_name in tables_operacionales:
        anchor = table_name.lower().replace('_', '')
        index_lines.append(f'  - [{table_name}](#{anchor})')
    
    return '\n'.join(index_lines)


# ============================================================================
# VALIDACIÓN
# ============================================================================

def validate_tables(tables_estructura, tables_operacionales):
    """
    Valida que existan tablas críticas.
    
    Args:
        tables_estructura: Dict de tablas de estructura
        tables_operacionales: Dict de tablas operacionales
    
    Returns:
        list: Nombres de tablas críticas faltantes (vacía si todo OK)
    """
    all_tables = set(tables_estructura.keys()) | set(tables_operacionales.keys())
    missing = [t for t in REQUIRED_TABLES if t not in all_tables]
    
    if missing:
        print(f"\n⚠️  ADVERTENCIA: Faltan tablas críticas:")
        for t in missing:
            print(f"   • {t}")
        print()
    
    return missing


# ============================================================================
# PROCESO PRINCIPAL
# ============================================================================

def merge_tables(input_dir, output_file):
    """
    Reconstruye Tablas.md desde archivos individuales.
    
    Args:
        input_dir: Path al directorio con archivos .md
        output_file: Path al archivo Tablas.md de salida
    
    Returns:
        int: 0 si éxito, 1 si error
    """
    print(f"📖 Leyendo archivos desde {input_dir}/...")
    
    # Recolectar contenido
    try:
        philosophy, tables_estr, tables_oper = collect_tables(input_dir)
    except (FileNotFoundError, ValueError) as e:
        print(f"❌ ERROR: {e}")
        return 1
    
    # Validar
    missing = validate_tables(tables_estr, tables_oper)
    
    print(f"\n📝 Generando Tablas.md...")
    
    # Construir documento completo
    document_parts = []
    
    # 1. Header
    document_parts.append(generate_header())
    
    # 2. Índice
    document_parts.append(generate_table_index(
        sorted(tables_estr.keys()),
        sorted(tables_oper.keys())
    ))
    document_parts.append('\n---\n')
    
    # 3. Filosofía
    document_parts.append(philosophy)
    document_parts.append('\n---\n')
    
    # 4. Tablas de Estructura
    document_parts.append('## Tablas de Estructura\n')
    for table_name in sorted(tables_estr.keys()):
        document_parts.append(tables_estr[table_name])
        document_parts.append('\n---\n')
    
    # 5. Tablas Operacionales
    document_parts.append('## Tablas Operacionales\n')
    for table_name in sorted(tables_oper.keys()):
        document_parts.append(tables_oper[table_name])
        document_parts.append('\n---\n')
    
    # Unir todo
    full_content = '\n'.join(document_parts)
    
    # Guardar
    print(f"💾 Guardando en {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(full_content)
    
    # Resumen
    print(f"\n✅ Proceso completado:")
    print(f"   • Filosofía: ✓")
    print(f"   • Tablas de estructura: {len(tables_estr)}")
    print(f"   • Tablas operacionales: {len(tables_oper)}")
    print(f"   • Total secciones: {len(tables_estr) + len(tables_oper) + 1}")
    print(f"   • Tablas críticas faltantes: {len(missing)}")
    print(f"   • Archivo generado: {output_file}")
    print(f"   • Tamaño: {len(full_content):,} caracteres")
    
    return 0


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Punto de entrada con parsing de argumentos."""
    
    parser = argparse.ArgumentParser(
        description='Reconstruye Tablas.md desde archivos individuales',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  
  # Modo básico (rutas por defecto)
  python scripts/merge_tables.py
  
  # Rutas personalizadas
  python scripts/merge_tables.py -i docs/tablas/ -o docs/Tablas.md
  
  # Ver este mensaje
  python scripts/merge_tables.py --help

Flujo recomendado:
  1. Editar archivos en tablas/ (ej: O_003_SOLICITUDES.md)
  2. Ejecutar este script
  3. Commit de ambos: tablas/*.md y Tablas.md regenerado
        """
    )
    
    parser.add_argument(
        '-i', '--input',
        type=Path,
        default=Path('docs/fuentesIA/referencias/tablas'),
        help='Directorio con archivos .md (default: docs/fuentesIA/referencias/tablas/)'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=Path,
        default=Path('docs/fuentesIA/referencias/Tablas.md'),
        help='Archivo Tablas.md de salida (default: docs/fuentesIA/referencias/Tablas.md)'
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("MERGE TABLES - Reconstruir Tablas.md desde archivos individuales")
    print("=" * 80)
    print()
    
    exit_code = merge_tables(args.input, args.output)
    
    if exit_code == 0:
        print()
        print("=" * 80)
        print("¡Listo! Tablas.md regenerado correctamente")
        print("Recuerda hacer commit de ambos:")
        print("  - docs/fuentesIA/referencias/tablas/*.md (editados)")
        print("  - docs/fuentesIA/referencias/Tablas.md (regenerado)")
        print("=" * 80)
    
    return exit_code


if __name__ == '__main__':
    exit(main())

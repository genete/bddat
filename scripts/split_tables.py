#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
split_tables.py - Divide Tablas.md en archivos individuales por tabla

DESCRIPCIÓN:
    Toma el archivo monolítico Tablas.md y lo divide en archivos individuales,
    uno por cada tabla, más un archivo separado para la Filosofía del Diseño.
    Cada archivo recibe un prefijo numérico para mantener el orden.

MEJORAS v2.0:
    - Numeración con prefijos (01-19 operacionales, 20-39 maestras)
    - Filosofía separada en 00_FILOSOFIA.md
    - Metadatos con timestamp de generación
    - Validación de estructura markdown
    - Manejo robusto de encabezados y secciones

USO:
    # Modo básico (usa rutas por defecto)
    python scripts/split_tables.py

    # Especificar rutas personalizadas
    python scripts/split_tables.py --input docs/Tablas.md --output docs/tablas/

    # Ver ayuda
    python scripts/split_tables.py --help

ENTRADA:
    docs/fuentesIA/referencias/Tablas.md

SALIDA:
    docs/fuentesIA/referencias/tablas/
    ├── 00_FILOSOFIA.md
    ├── 01_EXPEDIENTES.md
    ├── 02_PROYECTOS.md
    ├── 03_SOLICITUDES.md
    ├── 04_SOLICITUDES_TIPOS.md (si existe)
    ├── ...
    └── 30_TIPOS_RESULTADOS_FASES.md

SIGUIENTE PASO:
    Después de editar archivos individuales, ejecutar merge_tables.py
    para regenerar Tablas.md completo.

AUTOR: Sistema BDDAT
VERSIÓN: 2.0
FECHA: 2026-01-31
"""

import re
import argparse
from datetime import datetime
from pathlib import Path


# ============================================================================
# CONFIGURACIÓN
# ============================================================================

# Mapeo de tablas a números (para ordenación)
# Operacionales: 01-19, Maestras: 20-39
TABLE_ORDER = {
    # Operacionales
    'EXPEDIENTES': '01',
    'PROYECTOS': '02',
    'SOLICITUDES': '03',
    'SOLICITUDES_TIPOS': '04',
    'DOCUMENTOS': '05',
    'DOCUMENTOS_PROYECTO': '06',
    'TAREAS': '07',
    'FASES': '08',
    'TRAMITES': '09',
    'MUNICIPIOS_PROYECTO': '10',
    # Maestras
    'USUARIOS': '20',
    'ROLES': '21',
    'USUARIOS_ROLES': '22',
    'TIPOS_EXPEDIENTES': '23',
    'TIPOS_SOLICITUDES': '24',
    'TIPOS_FASES': '25',
    'TIPOS_TRAMITES': '26',
    'TIPOS_TAREAS': '27',
    'TIPOS_IA': '28',
    'MUNICIPIOS': '29',
    'TIPOS_RESULTADOS_FASES': '30',
}


# ============================================================================
# FUNCIONES DE EXTRACCIÓN
# ============================================================================

def extract_header_and_philosophy(content):
    """
    Extrae encabezado (título + índice) y filosofía del diseño.
    
    Args:
        content: Contenido completo de Tablas.md
    
    Returns:
        tuple: (header_content, philosophy_content, tables_start_index)
    
    Raises:
        ValueError: Si no encuentra la estructura esperada
    """
    lines = content.split('\n')
    
    philosophy_start = None
    philosophy_end = None
    tables_start = None
    
    for i, line in enumerate(lines):
        # Filosofía empieza
        if line.strip().startswith('## Filosofía del Diseño'):
            philosophy_start = i
        
        # Tablas Operacionales empieza (fin de filosofía)
        if line.strip().startswith('## Tablas Operacionales'):
            philosophy_end = i
            tables_start = i
            break
    
    if philosophy_start is None or philosophy_end is None:
        raise ValueError("No se encontró la sección 'Filosofía del Diseño'")
    
    # Header: desde inicio hasta filosofía
    header_content = '\n'.join(lines[:philosophy_start])
    
    # Filosofía: desde "## Filosofía" hasta "## Tablas Operacionales"
    philosophy_content = '\n'.join(lines[philosophy_start:philosophy_end])
    
    return header_content.strip(), philosophy_content.strip(), tables_start


def extract_tables(content, tables_start_index):
    """
    Extrae cada tabla individual desde la sección de tablas.
    
    Args:
        content: Contenido completo de Tablas.md
        tables_start_index: Línea donde empiezan las tablas
    
    Returns:
        dict: {table_name: table_content}
    """
    lines = content.split('\n')
    tables = {}
    current_table = None
    current_content = []
    in_tables_section = False
    
    for i in range(tables_start_index, len(lines)):
        line = lines[i]
        
        # Detectar inicio de tabla (### NOMBRE_TABLA)
        match = re.match(r'^### ([A-Z_]+)\s*$', line.strip())
        
        if match:
            # Guardar tabla anterior si existe
            if current_table:
                tables[current_table] = '\n'.join(current_content).strip()
            
            # Iniciar nueva tabla
            current_table = match.group(1)
            current_content = [line]
            in_tables_section = True
        
        elif in_tables_section:
            current_content.append(line)
    
    # Guardar última tabla
    if current_table:
        tables[current_table] = '\n'.join(current_content).strip()
    
    return tables


# ============================================================================
# FUNCIONES DE ESCRITURA
# ============================================================================

def create_metadata_header(table_name):
    """
    Crea header con metadatos para archivo individual.
    
    Args:
        table_name: Nombre de la tabla
    
    Returns:
        str: Header en formato HTML comment
    """
    timestamp = datetime.now().strftime('%d/%m/%Y %H:%M')
    
    return f"""<!--
Tabla: {table_name}
Generado automáticamente por: scripts/split_tables.py
Fecha de generación: {timestamp}
IMPORTANTE: No editar Tablas.md directamente.
            Editar este archivo y ejecutar merge_tables.py para regenerar.
-->

"""


def save_philosophy(philosophy_content, output_dir):
    """
    Guarda la filosofía en archivo separado.
    
    Args:
        philosophy_content: Contenido de la filosofía
        output_dir: Directorio de salida
    """
    output_file = output_dir / '00_FILOSOFIA.md'
    
    metadata = f"""<!--
Filosofía del Diseño v3.1
Generado automáticamente por: scripts/split_tables.py
Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}
-->

"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(metadata)
        f.write(philosophy_content)
        f.write('\n')
    
    print(f"   ✓ {output_file.name}")


def save_table(table_name, table_content, output_dir):
    """
    Guarda una tabla individual con numeración.
    
    Args:
        table_name: Nombre de la tabla
        table_content: Contenido markdown de la tabla
        output_dir: Directorio de salida
    """
    # Obtener prefijo numérico
    prefix = TABLE_ORDER.get(table_name, '99')
    
    output_file = output_dir / f'{prefix}_{table_name}.md'
    
    metadata = create_metadata_header(table_name)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(metadata)
        f.write(table_content)
        f.write('\n')
    
    print(f"   ✓ {output_file.name}")


# ============================================================================
# PROCESO PRINCIPAL
# ============================================================================

def split_tables(input_file, output_dir):
    """
    Divide Tablas.md en archivos individuales.
    
    Args:
        input_file: Path al archivo Tablas.md
        output_dir: Path al directorio de salida
    
    Returns:
        int: 0 si éxito, 1 si error
    """
    # Validar archivo entrada
    if not input_file.exists():
        print(f"❌ ERROR: No existe {input_file}")
        return 1
    
    # Crear directorio salida
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📖 Leyendo {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extraer secciones
    print("🔍 Extrayendo filosofía del diseño...")
    try:
        header, philosophy, tables_start = extract_header_and_philosophy(content)
    except ValueError as e:
        print(f"❌ ERROR: {e}")
        return 1
    
    print("🔍 Extrayendo tablas individuales...")
    tables = extract_tables(content, tables_start)
    
    # Guardar archivos
    print(f"\n💾 Guardando archivos en {output_dir}/...")
    save_philosophy(philosophy, output_dir)
    
    for table_name, table_content in sorted(tables.items()):
        save_table(table_name, table_content, output_dir)
    
    # Resumen
    print(f"\n✅ Proceso completado:")
    print(f"   • Archivos generados: {len(tables) + 1}")
    print(f"     - 1 archivo de filosofía")
    print(f"     - {len(tables)} tablas individuales")
    print(f"   • Directorio: {output_dir}/")
    
    # Listar tablas no mapeadas (usarán prefijo 99_)
    unmapped = [t for t in tables.keys() if t not in TABLE_ORDER]
    if unmapped:
        print(f"\n⚠️  Tablas sin numeración definida (prefijo 99_):")
        for t in unmapped:
            print(f"   • {t}")
        print(f"\n💡 Añadir a TABLE_ORDER en split_tables.py si son permanentes")
    
    return 0


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Punto de entrada con parsing de argumentos."""
    
    parser = argparse.ArgumentParser(
        description='Divide Tablas.md en archivos individuales por tabla',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  
  # Modo básico (rutas por defecto)
  python scripts/split_tables.py
  
  # Rutas personalizadas
  python scripts/split_tables.py -i docs/Tablas.md -o docs/tablas/
  
  # Ver este mensaje
  python scripts/split_tables.py --help

Siguiente paso:
  Editar archivos en tablas/ y ejecutar merge_tables.py para regenerar
        """
    )
    
    parser.add_argument(
        '-i', '--input',
        type=Path,
        default=Path('docs/fuentesIA/referencias/Tablas.md'),
        help='Archivo Tablas.md de entrada (default: docs/fuentesIA/referencias/Tablas.md)'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=Path,
        default=Path('docs/fuentesIA/referencias/tablas'),
        help='Directorio de salida (default: docs/fuentesIA/referencias/tablas/)'
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("SPLIT TABLES - Dividir Tablas.md en archivos individuales")
    print("=" * 80)
    print()
    
    exit_code = split_tables(args.input, args.output)
    
    if exit_code == 0:
        print()
        print("=" * 80)
        print("SIGUIENTE PASO:")
        print("  1. Editar archivos en tablas/")
        print("  2. Ejecutar: python scripts/merge_tables.py")
        print("=" * 80)
    
    return exit_code


if __name__ == '__main__':
    exit(main())

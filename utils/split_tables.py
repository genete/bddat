import os
import re

def split_markdown_tables(input_file):
    if not os.path.exists(input_file):
        print(f"Error: No se encuentra el archivo {input_file}")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Definir la estructura de carpetas
    base_dir = "Tablas_Generadas"
    folders = {
        "Operacionales": [
            "EXPEDIENTES", "PROYECTOS", "SOLICITUDES", "DOCUMENTOS", 
            "DOCUMENTOS_PROYECTO", "TAREAS", "FASES", "TRAMITES", 
            "MUNICIPIOS_PROYECTO"
        ],
        "Maestras": [
            "USUARIOS", "TIPOS_EXPEDIENTES", "TIPOS_SOLICITUDES", 
            "TIPOS_FASES", "TIPOS_TRAMITES", "TIPOS_TAREAS", 
            "TIPOS_IA", "MUNICIPIOS", "TIPOS_RESULTADOS_FASES"
        ]
    }

    # Crear directorios si no existen
    for subfolder in folders.keys():
        os.makedirs(os.path.join(base_dir, subfolder), exist_ok=True)

    # El script busca el nombre de la tabla justo después de los encabezados ## o ###
    sections = re.split(r'\n(?:##|###) +', content)
    
    count = 0
    all_targets = folders["Operacionales"] + folders["Maestras"]

    for section in sections:
        lines = section.strip().split('\n')
        if not lines:
            continue
            
        header = lines[0].strip()
        
        # Verificar si el encabezado es una de nuestras tablas
        if header in all_targets:
            # Determinar en qué subcarpeta guardarlo
            subfolder = "Operacionales" if header in folders["Operacionales"] else "Maestras"
            
            filepath = os.path.join(base_dir, subfolder, f"{header}.md")
            
            # Mantener el formato original con su encabezado
            table_content = f"### {section.strip()}"
            
            with open(filepath, 'w', encoding='utf-8') as f_out:
                f_out.write(table_content)
            
            print(f"Generado: {subfolder}/{header}.md")
            count += 1

    print(f"\n¡Listo! Se han organizado {count} tablas en '{base_dir}'")

if __name__ == "__main__":
    split_markdown_tables('Tablas.md')
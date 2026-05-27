import os
import pathlib
import argparse

# --- CONFIGURACIÓN ---
# Carpetas a ignorar
CARPETAS_IGNORAR = {"venv", ".venv", "__pycache__", ".git", ".playwright-mcp", "docs_prueba", "utils", "node_modules", "dist", ".vite", "normas", "react-diagramas"}
# Archivos específicos a ignorar
ARCHIVOS_IGNORAR = {".env", ".DS_Store", "contexto_completo_gemini.txt", "package-lock.json", "diagrama-esftt.iife.js"}
# Extensiones permitidas
EXTENSIONES_VALIDAS = {
    ".py", ".html", ".md", ".css", ".js", ".json", 
    ".sql", ".toml", ".yaml", ".yml", ".ini", 
    ".mako", ".sh", ".ps1", ".bat", ".vbs", ".txt"
}

def generar_contexto():
    parser = argparse.ArgumentParser(description="Genera volcado de contexto del proyecto")
    parser.add_argument("--out", help="Ruta adicional de salida (ej: carpeta Google Drive)")
    args = parser.parse_args()

    # Definir rutas relativas al script
    script_path = pathlib.Path(__file__).parent.resolve()
    project_root = script_path.parent
    output_file = project_root / "contexto_completo_gemini.txt"
    output_extra = pathlib.Path(args.out) if args.out else None

    print(f"--- INICIANDO EMPAQUETADO RÁPIDO CON PYTHON ---")
    print(f"Raíz del proyecto: {project_root}")

    try:
        with open(output_file, "w", encoding="utf-8") as f_out:
            f_out.write("--- INICIO DE DUMP DE PROYECTO BDDAT ---\n")
            
            # Caminata por el árbol de directorios
            for root, dirs, files in os.walk(project_root):
                # Modificar dirs in-place para ignorar carpetas recursivamente
                dirs[:] = [d for d in dirs if d not in CARPETAS_IGNORAR]
                
                for file in files:
                    if file in ARCHIVOS_IGNORAR:
                        continue
                    
                    file_path = pathlib.Path(root) / file
                    extension = file_path.suffix.lower()
                    
                    # Condición: Extensión válida o archivo LICENSE
                    if extension in EXTENSIONES_VALIDAS or file == "LICENSE":
                        rel_path = file_path.relative_to(project_root)
                        
                        print(f"Incluyendo: {rel_path}")
                        
                        f_out.write(f"\n--- FILE: {rel_path} ---\n")
                        
                        try:
                            with open(file_path, "r", encoding="utf-8", errors="replace") as f_in:
                                f_out.write(f_in.read())
                                f_out.write("\n")
                        except Exception as e:
                            print(f"  [!] Error leyendo {rel_path}: {e}")

        # Copia adicional si se especificó --out
        if output_extra:
            output_extra.parent.mkdir(parents=True, exist_ok=True)
            output_extra.write_bytes(output_file.read_bytes())
            print(f"Copia adicional en:  {output_extra}")

        print(f"\n--- PROCESO FINALIZADO ---")
        print(f"Archivo generado en: {output_file}")

    except Exception as e:
        print(f"Error crítico al crear el archivo de salida: {e}")

if __name__ == "__main__":
    generar_contexto()
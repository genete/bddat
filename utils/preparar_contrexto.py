import os
import pathlib

# --- CONFIGURACIÓN ---
# Carpetas a ignorar
CARPETAS_IGNORAR = {"venv", ".venv", "__pycache__", ".git", ".playwright-mcp", "docs_prueba", "utils"}
# Archivos específicos a ignorar
ARCHIVOS_IGNORAR = {".env", ".DS_Store", "contexto_completo_gemini.txt"}
# Extensiones permitidas
EXTENSIONES_VALIDAS = {
    ".py", ".html", ".md", ".css", ".js", ".json", 
    ".sql", ".toml", ".yaml", ".yml", ".ini", 
    ".mako", ".sh", ".ps1", ".bat", ".vbs", ".txt"
}

def generar_contexto():
    # Definir rutas relativas al script
    script_path = pathlib.Path(__file__).parent.resolve()
    project_root = script_path.parent
    output_file = project_root / "contexto_completo_gemini.txt"

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

        print(f"\n--- PROCESO FINALIZADO ---")
        print(f"Archivo generado en: {output_file}")

    except Exception as e:
        print(f"Error crítico al crear el archivo de salida: {e}")

if __name__ == "__main__":
    generar_contexto()
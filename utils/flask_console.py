import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox
import subprocess
import threading
import os
import signal
import re
from datetime import datetime

class FlaskControlGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("BDDAT - Flask Server Control")
        self.root.geometry("650x550")
        self.process = None
        
        # Frame superior para botones de control
        control_frame = tk.Frame(root)
        control_frame.pack(pady=10)
        
        # Botones de control del servidor
        self.btn_start = tk.Button(
            control_frame, 
            text="Encender Servidor", 
            command=self.start_server, 
            width=20,
            font=("Arial", 10)
        )
        self.btn_start.grid(row=0, column=0, padx=5)
        
        self.btn_stop = tk.Button(
            control_frame, 
            text="Apagar Servidor", 
            command=self.stop_server, 
            width=20,
            font=("Arial", 10),
            state=tk.DISABLED
        )
        self.btn_stop.grid(row=0, column=1, padx=5)
        
        # Frame para botones de logs
        log_buttons_frame = tk.Frame(root)
        log_buttons_frame.pack(pady=5)
        
        self.btn_copy = tk.Button(
            log_buttons_frame,
            text="Copiar Logs",
            command=self.copy_logs,
            width=15,
            font=("Arial", 9)
        )
        self.btn_copy.grid(row=0, column=0, padx=5)
        
        self.btn_export = tk.Button(
            log_buttons_frame,
            text="Exportar Log",
            command=self.export_log,
            width=15,
            font=("Arial", 9)
        )
        self.btn_export.grid(row=0, column=1, padx=5)
        
        self.btn_clear = tk.Button(
            log_buttons_frame,
            text="Limpiar Consola",
            command=self.clear_logs,
            width=15,
            font=("Arial", 9)
        )
        self.btn_clear.grid(row=0, column=2, padx=5)
        
        # Etiqueta de estado
        self.status_label = tk.Label(
            root, 
            text="Estado: Servidor detenido", 
            font=("Arial", 10, "bold"),
            fg="gray"
        )
        self.status_label.pack(pady=5)
        
        # Consola de Logs
        log_label = tk.Label(root, text="Consola de logs:", font=("Arial", 9))
        log_label.pack(anchor="w", padx=10)
        
        self.log_area = scrolledtext.ScrolledText(
            root, 
            height=20, 
            bg="black", 
            fg="lightgreen",
            font=("Consolas", 9),
            wrap=tk.WORD
        )
        self.log_area.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)
        
        # Configurar tags de colores para ANSI
        self.setup_color_tags()
        
    def setup_color_tags(self):
        """Configura los tags de colores para simular salida ANSI"""
        self.log_area.tag_config("default", foreground="lightgreen")
        self.log_area.tag_config("red", foreground="#FF5555")
        self.log_area.tag_config("green", foreground="#50FA7B")
        self.log_area.tag_config("yellow", foreground="#F1FA8C")
        self.log_area.tag_config("blue", foreground="#8BE9FD")
        self.log_area.tag_config("magenta", foreground="#FF79C6")
        self.log_area.tag_config("cyan", foreground="#8BE9FD")
        self.log_area.tag_config("white", foreground="#F8F8F2")
        self.log_area.tag_config("bright_red", foreground="#FF6E6E")
        self.log_area.tag_config("bright_green", foreground="#69FF94")
        self.log_area.tag_config("bright_yellow", foreground="#FFFFA5")
        self.log_area.tag_config("bright_blue", foreground="#D6ACFF")
        self.log_area.tag_config("bright_magenta", foreground="#FF92DF")
        self.log_area.tag_config("bright_cyan", foreground="#A4FFFF")
        self.log_area.tag_config("bold", font=("Consolas", 9, "bold"))
        
    def parse_ansi_colors(self, text):
        """Parsea códigos ANSI y devuelve lista de (texto, tag)"""
        ansi_map = {
            '0': 'default',
            '1': 'bold',
            '31': 'red',
            '32': 'green',
            '33': 'yellow',
            '34': 'blue',
            '35': 'magenta',
            '36': 'cyan',
            '37': 'white',
            '91': 'bright_red',
            '92': 'bright_green',
            '93': 'bright_yellow',
            '94': 'bright_blue',
            '95': 'bright_magenta',
            '96': 'bright_cyan',
        }
        
        ansi_pattern = re.compile(r'\x1b\[([0-9;]+)m')
        result = []
        current_tag = 'default'
        last_end = 0
        
        for match in ansi_pattern.finditer(text):
            if match.start() > last_end:
                result.append((text[last_end:match.start()], current_tag))
            
            codes = match.group(1).split(';')
            for code in codes:
                if code in ansi_map:
                    current_tag = ansi_map[code]
            
            last_end = match.end()
        
        if last_end < len(text):
            result.append((text[last_end:], current_tag))
        
        return result if result else [(text, 'default')]
    
    def insert_colored_text(self, text):
        """Inserta texto con colores parseando códigos ANSI"""
        segments = self.parse_ansi_colors(text)
        for segment_text, tag in segments:
            self.log_area.insert(tk.END, segment_text, tag)
        self.log_area.see(tk.END)
        
    def start_server(self):
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self.status_label.config(text="Estado: Iniciando servidor...", fg="orange")
        self.log_area.insert(tk.END, "=" * 60 + "\n", "cyan")
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.log_area.insert(tk.END, f"Iniciando servidor Flask BDDAT - {timestamp}\n", "bright_green")
        self.log_area.insert(tk.END, "Directorio base: D:\\BDDAT\n", "yellow")
        self.log_area.insert(tk.END, "=" * 60 + "\n\n", "cyan")
        
        os.chdir(r"D:\BDDAT")
        
        venv_python = r"D:\BDDAT\venv\Scripts\python.exe"
        
        if os.path.exists(venv_python):
            python_cmd = venv_python
            self.log_area.insert(tk.END, "Usando entorno virtual: venv\\Scripts\\python.exe\n\n", "green")
        else:
            python_cmd = "python"
            self.log_area.insert(tk.END, "Usando Python global del sistema\n\n", "yellow")
        
        try:
            env = os.environ.copy()
            env['PYTHONUNBUFFERED'] = '1'
            env['FORCE_COLOR'] = '1'
            
            self.process = subprocess.Popen(
                [python_cmd, 'run.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=r"D:\BDDAT",
                env=env,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
            
            self.status_label.config(text="Estado: Servidor en ejecución", fg="green")
            threading.Thread(target=self.read_logs, daemon=True).start()
            
        except Exception as e:
            self.log_area.insert(tk.END, f"\nERROR al iniciar servidor:\n{str(e)}\n", "red")
            self.status_label.config(text="Estado: Error al iniciar", fg="red")
            self.btn_start.config(state=tk.NORMAL)
            self.btn_stop.config(state=tk.DISABLED)
    
    def read_logs(self):
        try:
            for line in iter(self.process.stdout.readline, ''):
                if line:
                    self.insert_colored_text(line)
        except Exception as e:
            self.log_area.insert(tk.END, f"\nError leyendo logs: {str(e)}\n", "yellow")
    
    def stop_server(self):
        if self.process:
            try:
                os.kill(self.process.pid, signal.CTRL_BREAK_EVENT)
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            except Exception as e:
                self.log_area.insert(tk.END, f"\nAdvertencia al detener: {str(e)}\n", "yellow")
            finally:
                self.process = None
                
            self.log_area.insert(tk.END, "\n" + "=" * 60 + "\n", "cyan")
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.log_area.insert(tk.END, f"--- Servidor Detenido - {timestamp} ---\n", "red")
            self.log_area.insert(tk.END, "=" * 60 + "\n\n", "cyan")
            
        self.status_label.config(text="Estado: Servidor detenido", fg="gray")
        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)
    
    def copy_logs(self):
        """Copia todo el contenido de los logs al portapapeles"""
        try:
            log_content = self.log_area.get("1.0", tk.END)
            self.root.clipboard_clear()
            self.root.clipboard_append(log_content)
            self.root.update()
            messagebox.showinfo("Copiar Logs", "Logs copiados al portapapeles correctamente")
        except Exception as e:
            messagebox.showerror("Error", f"Error al copiar logs:\n{str(e)}")
    
    def export_log(self):
        """Exporta los logs a un archivo de texto"""
        try:
            log_content = self.log_area.get("1.0", tk.END)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            default_filename = f"bddat_flask_log_{timestamp}.txt"
            
            filepath = filedialog.asksaveasfilename(
                initialdir=r"D:\BDDAT\utils",
                initialfile=default_filename,
                defaultextension=".txt",
                filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")],
                title="Exportar Log del Servidor Flask"
            )
            
            if filepath:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write("BDDAT - Flask Server Log\n")
                    export_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    f.write(f"Exportado: {export_time}\n")
                    f.write("=" * 80 + "\n\n")
                    f.write(log_content)
                
                messagebox.showinfo("Exportar Log", f"Log exportado correctamente:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar log:\n{str(e)}")
    
    def clear_logs(self):
        """Limpia el contenido de la consola de logs"""
        response = messagebox.askyesno(
            "Limpiar Consola", 
            "¿Está seguro de que desea limpiar la consola de logs?\n\nEsta acción no se puede deshacer."
        )
        if response:
            self.log_area.delete("1.0", tk.END)
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.log_area.insert(tk.END, f"Consola limpiada - {timestamp}\n\n", "cyan")

if __name__ == "__main__":
    root = tk.Tk()
    gui = FlaskControlGUI(root)
    root.mainloop()

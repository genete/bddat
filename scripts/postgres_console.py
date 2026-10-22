import tkinter as tk
from tkinter import scrolledtext, messagebox
import subprocess
import threading
import os
from datetime import datetime

# PostgreSQL portable (sin servicio de Windows): binarios en D:\pgsql, datos en D:\POSTGRESQL
PG_BIN = r"D:\pgsql\bin"
PG_DATA = r"D:\POSTGRESQL"
PG_HOST = "localhost"
PG_PORT = "5432"

POSTGRES = os.path.join(PG_BIN, "postgres.exe")
PG_CTL = os.path.join(PG_BIN, "pg_ctl.exe")
PG_ISREADY = os.path.join(PG_BIN, "pg_isready.exe")

# Sin ventana de consola propia para los procesos auxiliares
SIN_VENTANA = subprocess.CREATE_NO_WINDOW


class PostgresControlGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("BDDAT - PostgreSQL Control")
        self.root.geometry("780x520")
        self.process = None  # postgres.exe lanzado desde esta consola (None si lo lanzó otro)

        control_frame = tk.Frame(root)
        control_frame.pack(pady=10)

        self.btn_start = tk.Button(
            control_frame, text="Encender PostgreSQL", command=self.start_server,
            width=20, font=("Arial", 10),
        )
        self.btn_start.grid(row=0, column=0, padx=5)

        self.btn_stop = tk.Button(
            control_frame, text="Apagar PostgreSQL", command=self.stop_server,
            width=20, font=("Arial", 10), state=tk.DISABLED,
        )
        self.btn_stop.grid(row=0, column=1, padx=5)

        log_buttons_frame = tk.Frame(root)
        log_buttons_frame.pack(pady=5)
        tk.Button(
            log_buttons_frame, text="Copiar Logs", command=self.copy_logs,
            width=15, font=("Arial", 9),
        ).grid(row=0, column=0, padx=5)
        tk.Button(
            log_buttons_frame, text="Limpiar Consola", command=self.clear_logs,
            width=15, font=("Arial", 9),
        ).grid(row=0, column=1, padx=5)

        self.status_label = tk.Label(
            root, text="Estado: comprobando...", font=("Arial", 10, "bold"), fg="gray",
        )
        self.status_label.pack(pady=5)

        tk.Label(root, text="Consola de logs:", font=("Arial", 9)).pack(anchor="w", padx=10)
        self.log_area = scrolledtext.ScrolledText(
            root, height=20, bg="black", fg="lightgreen", font=("Consolas", 9), wrap=tk.WORD,
        )
        self.log_area.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)
        self.log_area.tag_config("red", foreground="#FF5555")
        self.log_area.tag_config("green", foreground="#50FA7B")
        self.log_area.tag_config("yellow", foreground="#F1FA8C")
        self.log_area.tag_config("cyan", foreground="#8BE9FD")
        self.log_area.tag_config("bright_green", foreground="#69FF94")

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.refresh_status()

    # --- Estado ---
    def server_is_ready(self):
        """True si algún PostgreSQL (lanzado desde aquí o no) acepta conexiones en el puerto."""
        try:
            r = subprocess.run(
                [PG_ISREADY, "-h", PG_HOST, "-p", PG_PORT],
                capture_output=True, timeout=5, creationflags=SIN_VENTANA,
            )
            return r.returncode == 0
        except Exception:
            return False

    def refresh_status(self):
        """Sondea cada 3 s en un hilo para no congelar la ventana; la UI se actualiza en el hilo principal."""
        def sondear():
            listo = self.server_is_ready()
            self.root.after(0, lambda: self.apply_status(listo))
        threading.Thread(target=sondear, daemon=True).start()
        self.root.after(3000, self.refresh_status)

    def apply_status(self, listo):
        if listo:
            origen = "lanzado desde esta consola" if self.process else "lanzado desde fuera"
            self.status_label.config(
                text=f"Estado: PostgreSQL en marcha en {PG_HOST}:{PG_PORT}  ({origen})", fg="green",
            )
        else:
            self.status_label.config(text="Estado: PostgreSQL detenido", fg="gray")
        self.btn_start.config(state=tk.DISABLED if listo else tk.NORMAL)
        self.btn_stop.config(state=tk.NORMAL if listo else tk.DISABLED)

    # --- Control ---
    def log(self, texto, tag=None):
        self.log_area.insert(tk.END, texto, tag)
        self.log_area.see(tk.END)

    def start_server(self):
        self.btn_start.config(state=tk.DISABLED)
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log("=" * 60 + "\n", "cyan")
        self.log(f"Iniciando PostgreSQL - {ahora}\n", "bright_green")
        self.log(f"Datos: {PG_DATA}\n", "yellow")
        self.log("=" * 60 + "\n\n", "cyan")
        try:
            # postgres.exe en primer plano con el log por stderr (logging_collector=off),
            # igual que hace la consola de Flask: así se ve aquí lo que escribe el servidor.
            self.process = subprocess.Popen(
                [POSTGRES, "-D", PG_DATA, "-c", "logging_collector=off"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=SIN_VENTANA,
            )
            threading.Thread(target=self.read_logs, args=(self.process,), daemon=True).start()
        except Exception as e:
            self.log(f"\nERROR al iniciar PostgreSQL:\n{e}\n", "red")
            self.process = None
            self.btn_start.config(state=tk.NORMAL)

    def read_logs(self, proc):
        try:
            for line in iter(proc.stdout.readline, ""):
                if line:
                    self.root.after(0, self.log, line)
        except Exception as e:
            self.root.after(0, self.log, f"\nError leyendo logs: {e}\n", "yellow")
        finally:
            # El proceso terminó (parada normal o fallo al arrancar)
            self.root.after(0, self.on_process_exit, proc)

    def on_process_exit(self, proc):
        if self.process is proc:
            self.process = None
            self.log(f"\n--- postgres.exe terminó (código {proc.poll()}) ---\n", "red")

    def stop_server(self):
        """Parada ordenada con pg_ctl (modo fast): sirve también si lo arrancó otro."""
        self.btn_stop.config(state=tk.DISABLED)
        self.log("\nApagando PostgreSQL (modo fast)...\n", "yellow")

        def parar():
            r = subprocess.run(
                [PG_CTL, "stop", "-D", PG_DATA, "-m", "fast"],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                creationflags=SIN_VENTANA,
            )
            salida = (r.stdout + r.stderr).strip()
            tag = "green" if r.returncode == 0 else "red"
            self.root.after(0, self.log, f"{salida}\n", tag)
        threading.Thread(target=parar, daemon=True).start()

    def on_close(self):
        # Si se cierra la ventana con el servidor lanzado desde aquí, hay que decidir qué pasa con él
        if self.process is not None and self.process.poll() is None:
            if messagebox.askyesno("Cerrar", "PostgreSQL sigue en marcha.\n\n¿Apagarlo antes de cerrar?"):
                subprocess.run(
                    [PG_CTL, "stop", "-D", PG_DATA, "-m", "fast"],
                    capture_output=True, creationflags=SIN_VENTANA,
                )
        self.root.destroy()

    # --- Logs ---
    def copy_logs(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.log_area.get("1.0", tk.END))
        self.root.update()
        messagebox.showinfo("Copiar Logs", "Logs copiados al portapapeles correctamente")

    def clear_logs(self):
        if messagebox.askyesno("Limpiar Consola", "¿Limpiar la consola de logs?"):
            self.log_area.delete("1.0", tk.END)


if __name__ == "__main__":
    root = tk.Tk()
    PostgresControlGUI(root)
    root.mainloop()

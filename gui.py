import os
import platform
import threading
import tkinter as tk
from tkinter import ttk, messagebox

from ..interfaces.file_service_interface import FileServiceInterface
from ..interfaces.ftp_service_interface import FTPServiceInterface


class FTPClientGUI:
    """
    The main application GUI. It is responsible for the user interface and
    delegates all FTP and file system operations to the respective services.
    """
    def __init__(self, master: tk.Tk, ftp_service: FTPServiceInterface, file_service: FileServiceInterface):
        self.master = master
        self.ftp_service = ftp_service
        self.file_service = file_service

        self.current_local_path = self.file_service.get_user_home()
        self.current_remote_path = "/"

        self._setup_ui()
        self.populate_local_tree()

    def _setup_ui(self):
        self.master.title("Cliente FTP Moderno (SOLID)")
        self.master.geometry("1200x750")

        # --- Style ---
        self.style = ttk.Style(self.master)
        self.style.theme_use("clam")
        self.style.configure("TButton", padding=6, relief="flat", font=('Helvetica', 10))
        self.style.configure("Treeview", rowheight=25)
        self.style.configure("Treeview.Heading", font=('Helvetica', 10, 'bold'))
        self.style.configure("Green.TButton", background='green')
        self.style.configure("Red.TButton", background='red')

        # --- Connection Frame ---
        connection_frame = ttk.LabelFrame(self.master, text="Conexión FTP", padding=(10, 5))
        connection_frame.pack(fill="x", padx=10, pady=5)

        # Entries for host, user, password
        self.host_entry = self._create_entry(connection_frame, "Servidor:", 0, "ftp.dlptest.com")
        self.user_entry = self._create_entry(connection_frame, "Usuario:", 2, "dlpuser")
        self.pass_entry = self._create_entry(connection_frame, "Contraseña:", 4, "rNrKYTX9g7z3RgJRmxWuGHbeu", show="*")

        self.connect_button = ttk.Button(connection_frame, text="Conectar", command=self.toggle_connection, style="Red.TButton")
        self.connect_button.grid(row=0, column=6, padx=10, pady=5)

        self.status_label = ttk.Label(connection_frame, text="Estado: Desconectado", foreground="red")
        self.status_label.grid(row=0, column=7, padx=20, pady=5)

        # --- Paned Window for File Views ---
        paned_window = ttk.PanedWindow(self.master, orient=tk.HORIZONTAL)
        paned_window.pack(fill="both", expand=True, padx=10, pady=5)

        # --- Local Files Panel ---
        local_frame, self.local_path_label, self.local_tree = self._create_file_panel(paned_window, "Local")
        self.setup_drive_selector(local_frame.winfo_children()[0]) # Pass the controls frame
        paned_window.add(local_frame, weight=1)

        # --- Transfer Buttons ---
        transfer_frame = self._create_transfer_panel(paned_window)
        paned_window.add(transfer_frame, weight=0)

        # --- Remote Files Panel ---
        remote_frame, self.remote_path_label, self.remote_tree = self._create_file_panel(paned_window, "Remoto")
        paned_window.add(remote_frame, weight=1)

        # --- Log Frame ---
        log_frame = ttk.LabelFrame(self.master, text="Log de Actividad", padding=(10, 5))
        log_frame.pack(fill="x", padx=10, pady=5)
        self.log_text = tk.Text(log_frame, height=5, state="disabled")
        self.log_text.pack(fill="x", expand=True)

    def _create_entry(self, parent, label_text, column, default_value, show=None):
        ttk.Label(parent, text=label_text).grid(row=0, column=column, padx=5, pady=5)
        entry = ttk.Entry(parent, width=20, show=show)
        entry.grid(row=0, column=column + 1, padx=5, pady=5)
        entry.insert(0, default_value)
        return entry

    def _create_file_panel(self, parent, title):
        frame = ttk.Frame(parent, width=550)

        controls_frame = ttk.Frame(frame)
        controls_frame.pack(fill="x", pady=(0, 5))

        path_label = ttk.Label(controls_frame, text=f"{title}: /", anchor="w", wraplength=400)
        path_label.pack(side="left", fill="x", expand=True, padx=5)

        if title == "Remoto":
            refresh_button = ttk.Button(controls_frame, text="Refrescar", command=self.refresh_remote_view)
            refresh_button.pack(side="right", padx=5)

        tree = self._create_treeview(frame)

        return frame, path_label, tree

    def _create_transfer_panel(self, parent):
        frame = ttk.Frame(parent, width=80)
        frame.pack_propagate(False)

        upload_button = ttk.Button(frame, text="▶", command=self.upload_file, width=4)
        upload_button.pack(pady=(150, 20), padx=5)

        download_button = ttk.Button(frame, text="◀", command=self.download_file, width=4)
        download_button.pack(pady=20, padx=5)
        return frame

    def setup_drive_selector(self, parent_frame):
        if platform.system() == "Windows":
            ttk.Label(parent_frame, text="Unidad:").pack(side="left", padx=(0, 5))
            drives = self.file_service.get_available_drives()
            self.drive_var = tk.StringVar()
            self.drive_selector = ttk.Combobox(parent_frame, textvariable=self.drive_var, values=drives, width=5, state="readonly")
            self.drive_selector.pack(side="left")
            self.drive_selector.bind("<<ComboboxSelected>>", self.change_local_drive)

            current_drive = os.path.splitdrive(self.current_local_path)[0]
            if current_drive and f"{current_drive}\\" in drives:
                self.drive_var.set(f"{current_drive}\\")

    def _create_treeview(self, parent):
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True)

        tree = ttk.Treeview(frame, columns=("size", "type"), show="tree headings")
        tree.heading("#0", text="Nombre")
        tree.heading("size", text="Tamaño")
        tree.heading("type", text="Tipo")
        tree.column("#0", minwidth=250, width=300, stretch=tk.YES)
        tree.column("size", width=80, anchor="e")
        tree.column("type", width=120, anchor="w")

        tree.bind("<Double-1>", lambda event: self.on_double_click(event, tree))

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        tree.pack(side="left", fill="both", expand=True)

        return tree

    def log(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def toggle_connection(self):
        if self.ftp_service.is_connected:
            self.disconnect_ftp()
        else:
            self.connect_ftp()

    def connect_ftp(self):
        host = self.host_entry.get()
        user = self.user_entry.get()
        password = self.pass_entry.get()

        if not host:
            messagebox.showerror("Error", "El campo 'Servidor' no puede estar vacío.")
            return

        def do_connect():
            try:
                self.log(f"Conectando a {host}...")
                welcome_msg = self.ftp_service.connect(host, user, password)
                self.master.after(0, lambda: self.update_ui_on_connect(welcome_msg))
            except Exception as e:
                self.master.after(0, lambda: messagebox.showerror("Error de Conexión", str(e)))
                self.log(f"Error de conexión: {e}")

        threading.Thread(target=do_connect, daemon=True).start()

    def update_ui_on_connect(self, welcome_msg):
        self.status_label.config(text="Estado: Conectado", foreground="green")
        self.connect_button.config(text="Desconectar", style="Green.TButton")
        self.log(f"Conexión exitosa: {welcome_msg}")
        self.populate_remote_tree()

    def disconnect_ftp(self):
        try:
            self.ftp_service.disconnect()
        except Exception as e:
            self.log(f"Error al desconectar: {e}")
        finally:
            self.status_label.config(text="Estado: Desconectado", foreground="red")
            self.connect_button.config(text="Conectar", style="Red.TButton")
            self.remote_tree.delete(*self.remote_tree.get_children())
            self.log("Desconectado del servidor.")

    def populate_local_tree(self, path=None):
        if path is None:
            path = self.current_local_path

        try:
            abs_path, items = self.file_service.list_directory(path)
            self.current_local_path = abs_path
            self.local_path_label.config(text=f"Local: {self.current_local_path}")

            self.local_tree.delete(*self.local_tree.get_children())

            if self.file_service.get_parent_dir(self.current_local_path) != self.current_local_path:
                self.local_tree.insert("", "end", text="..", values=("", "Directorio Padre"), iid="..")

            for item in items:
                display_name = f"📁 {item['name']}" if item['is_dir'] else f"📄 {item['name']}"
                self.local_tree.insert("", "end", text=display_name, values=(item['size'], item['type']), iid=item['name'])
        except Exception as e:
            self.log(f"Error al leer directorio local: {e}")
            messagebox.showerror("Error Local", f"No se pudo acceder a la carpeta: {path}\n{e}")
            if path != self.file_service.get_user_home():
                self.populate_local_tree(self.file_service.get_user_home())

    def populate_remote_tree(self, path=None):
        if not self.ftp_service.is_connected:
            return

        if path is None:
            path = self.current_remote_path

        self.remote_tree.delete(*self.remote_tree.get_children())

        def do_populate():
            try:
                current_path, items = self.ftp_service.list_directory(path)
                self.current_remote_path = current_path

                def update_ui():
                    self.remote_path_label.config(text=f"Remoto: {self.current_remote_path}")
                    if self.current_remote_path != "/":
                        self.remote_tree.insert("", "end", text="..", values=("", "Directorio Padre"), iid="..")

                    for item in items:
                        display_name = f"📁 {item['name']}" if item['is_dir'] else f"📄 {item['name']}"
                        self.remote_tree.insert("", "end", text=display_name, values=(item['size'], item['type']), iid=item['name'])

                self.master.after(0, update_ui)

            except Exception as e:
                self.log(f"Error al leer directorio remoto: {e}")
                self.master.after(0, lambda: messagebox.showerror("Error Remoto", f"No se pudo acceder a la carpeta remota: {path}\n{e}"))

        threading.Thread(target=do_populate, daemon=True).start()

    def refresh_remote_view(self):
        self.populate_remote_tree(self.current_remote_path)

    def change_local_drive(self, event=None):
        selected_drive = self.drive_var.get()
        if selected_drive:
            self.populate_local_tree(selected_drive)

    def on_double_click(self, event, tree):
        item_id = tree.focus()
        if not item_id: return

        item = tree.item(item_id)
        item_type = item["values"][1]

        if "Directorio" in item_type:
            if tree is self.local_tree:
                if item_id == "..":
                    new_path = self.file_service.get_parent_dir(self.current_local_path)
                else:
                    new_path = os.path.join(self.current_local_path, item_id)
                self.populate_local_tree(new_path)
            elif tree is self.remote_tree:
                if item_id == "..":
                    new_path = "/".join(self.current_remote_path.split('/')[:-1]) or "/"
                else:
                    new_path = f"{self.current_remote_path}/{item_id}" if self.current_remote_path != "/" else f"/{item_id}"
                self.populate_remote_tree(new_path)

    def upload_file(self):
        selected_item_id = self.local_tree.focus()
        if not selected_item_id or not self.ftp_service.is_connected:
            self.log("Seleccione un archivo local y conéctese a un servidor para subir.")
            return

        item = self.local_tree.item(selected_item_id)
        item_type = item.get("values")[1] if item.get("values") else ""

        if item_type != "Archivo":
            self.log("Selección no válida. Solo se pueden subir archivos.")
            return

        local_path = os.path.join(self.current_local_path, selected_item_id)

        def do_upload():
            try:
                self.log(f"Subiendo '{selected_item_id}'...")
                self.ftp_service.upload_file(local_path, selected_item_id)
                self.log(f"'{selected_item_id}' subido con éxito.")
                self.master.after(0, self.refresh_remote_view)
            except Exception as e:
                self.log(f"Error al subir '{selected_item_id}': {e}")
                self.master.after(0, lambda: messagebox.showerror("Error de Subida", str(e)))

        threading.Thread(target=do_upload, daemon=True).start()

    def download_file(self):
        selected_item_id = self.remote_tree.focus()
        if not selected_item_id or not self.ftp_service.is_connected:
            self.log("Seleccione un archivo remoto y conéctese a un servidor para descargar.")
            return

        item = self.remote_tree.item(selected_item_id)
        item_type = item.get("values")[1] if item.get("values") else ""

        if item_type != "Archivo":
            self.log("Selección no válida. Solo se pueden descargar archivos.")
            return

        local_path = os.path.join(self.current_local_path, selected_item_id)

        def do_download():
            try:
                self.log(f"Descargando '{selected_item_id}'...")
                self.ftp_service.download_file(selected_item_id, local_path)
                self.log(f"'{selected_item_id}' descargado con éxito.")
                self.master.after(0, lambda: self.populate_local_tree(self.current_local_path))
            except Exception as e:
                self.log(f"Error al descargar '{selected_item_id}': {e}")
                self.master.after(0, lambda: messagebox.showerror("Error de Descarga", str(e)))

        threading.Thread(target=do_download, daemon=True).start()
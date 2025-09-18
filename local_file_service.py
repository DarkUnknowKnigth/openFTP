import os
import platform
import string
from ..interfaces.file_service_interface import FileServiceInterface


class LocalFileService(FileServiceInterface):
    """Handles all local file system interactions."""
    def list_directory(self, path):
        if not os.path.exists(path) or not os.path.isdir(path):
            raise FileNotFoundError(f"La ruta no existe o no es un directorio: {path}")

        abs_path = os.path.abspath(path)
        items = []
        for item_name in sorted(os.listdir(abs_path), key=str.lower):
            full_path = os.path.join(abs_path, item_name)
            try:
                is_dir = os.path.isdir(full_path)
                item_type = "Directorio" if is_dir else "Archivo"
                size = os.path.getsize(full_path) if not is_dir else ""
                items.append({'name': item_name, 'type': item_type, 'size': size, 'is_dir': is_dir})
            except (OSError, PermissionError):
                continue # Ignore files that can't be accessed
        return abs_path, items

    def get_available_drives(self):
        if platform.system() == "Windows":
            return [f"{d}:\\" for d in string.ascii_uppercase if os.path.exists(f"{d}:")]
        return []

    def get_user_home(self):
        return os.path.expanduser("~")

    def get_parent_dir(self, path):
        return os.path.dirname(path)
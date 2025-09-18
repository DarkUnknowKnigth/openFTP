from ftplib import FTP
from ..interfaces.ftp_service_interface import FTPServiceInterface


class FTPService(FTPServiceInterface):
    """Handles all FTP communication logic."""
    def __init__(self):
        self.ftp = None

    def connect(self, host, user, password, timeout=10):
        self.ftp = FTP(host, timeout=timeout)
        welcome_message = self.ftp.login(user, password)
        return welcome_message

    def disconnect(self):
        if self.ftp:
            self.ftp.quit()
            self.ftp = None

    def list_directory(self, path):
        self.ftp.cwd(path)
        current_path = self.ftp.pwd()
        lines = []
        self.ftp.dir(lines.append)

        items = []
        for line in sorted(lines, key=str.lower):
            parts = line.split()
            if len(parts) < 9: continue

            name = " ".join(parts[8:])
            is_dir = line.startswith('d')
            item_type = "Directorio" if is_dir else "Archivo"
            size = parts[4] if not is_dir else ""
            items.append({'name': name, 'type': item_type, 'size': size, 'is_dir': is_dir})
        return current_path, items

    def upload_file(self, local_path, remote_name):
        with open(local_path, 'rb') as f:
            self.ftp.storbinary(f'STOR {remote_name}', f)

    def download_file(self, remote_name, local_path):
        with open(local_path, 'wb') as f:
            self.ftp.retrbinary(f'RETR {remote_name}', f.write)

    @property
    def is_connected(self):
        return self.ftp is not None
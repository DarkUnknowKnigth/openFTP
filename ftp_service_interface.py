from abc import ABC, abstractmethod


class FTPServiceInterface(ABC):
    @abstractmethod
    def connect(self, host, user, password):
        pass

    @abstractmethod
    def disconnect(self):
        pass

    @abstractmethod
    def list_directory(self, path):
        pass

    @abstractmethod
    def upload_file(self, local_path, remote_name):
        pass

    @abstractmethod
    def download_file(self, remote_name, local_path):
        pass

    @property
    @abstractmethod
    def is_connected(self):
        pass
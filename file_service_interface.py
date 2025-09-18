from abc import ABC, abstractmethod


class FileServiceInterface(ABC):
    @abstractmethod
    def list_directory(self, path):
        pass

    @abstractmethod
    def get_available_drives(self):
        pass

    @abstractmethod
    def get_user_home(self):
        pass

    @abstractmethod
    def get_parent_dir(self, path):
        pass
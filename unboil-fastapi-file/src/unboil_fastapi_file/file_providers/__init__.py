from abc import ABC, abstractmethod
from typing import IO


class FileProvider(ABC):
    
    @abstractmethod
    async def list_keys(self, prefix: str) -> list[str]: ...

    @abstractmethod
    async def object_exists(self, key: str) -> bool: ...

    @abstractmethod
    async def copy_object(self, source_key: str, target_key: str) -> None: ...

    @abstractmethod
    async def upload_object(self, key: str, file: IO) -> None: ...

    @abstractmethod
    async def download_object(self, key: str) -> IO: ...

    @abstractmethod
    async def delete_object(self, key: str): ...

    @abstractmethod
    async def delete_objects(self, keys: list[str]): ...

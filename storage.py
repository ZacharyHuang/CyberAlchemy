import json
import os
from abc import ABC, abstractmethod
from typing import Any


class Storage(ABC):
    """
    Abstract base class for storage systems.
    """

    @abstractmethod
    def save(self, key: str, data) -> None:
        """
        Save data to the storage system.
        """
        ...

    @abstractmethod
    def load(self, key: str):
        """
        Load data from the storage system.
        """
        ...

    @abstractmethod
    def delete(self, key: str) -> None:
        """
        Delete data from the storage system.
        """
        ...

    @abstractmethod
    def exists(self, key: str) -> bool:
        """
        Check if data exists in the storage system.
        """
        ...

    @abstractmethod
    def list(self, filter: str | None = None) -> list:
        """
        List all keys in the storage system.
        """
        ...


class InMemoryStorage(Storage):
    """
    In-memory storage implementation.
    """

    def __init__(self):
        self._storage: dict[str, Any] = {}

    def save(self, key: str, data) -> None:
        self._storage[key] = data

    def load(self, key: str):
        return self._storage.get(key)

    def delete(self, key: str) -> None:
        if key in self._storage:
            del self._storage[key]

    def exists(self, key: str) -> bool:
        return key in self._storage

    def list(self, filter: str | None = None) -> list:
        return [
            value
            for key, value in self._storage.items()
            if (filter is None or key.startswith(filter))
        ]


class JsonFileStorage(Storage):
    """
    File-based storage implementation.
    """

    def __init__(self, directory: str):
        self._directory = directory

    def _get_path(self, key: str) -> str:
        return os.path.join(self._directory, f"{key}.json")

    def save(self, key: str, data) -> None:
        filepath = self._get_path(key)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def load(self, key: str):
        filepath = self._get_path(key)
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def delete(self, key: str) -> None:
        filepath = self._get_path(key)
        if os.path.exists(filepath):
            os.remove(filepath)

    def exists(self, key: str) -> bool:
        filepath = self._get_path(key)
        return os.path.exists(filepath)

    def list(self, filter: str | None = None) -> list:
        if not os.path.exists(self._directory):
            return []
        return [
            self.load(f[: -len(".json")])
            for f in os.listdir(self._directory)
            if f.endswith(".json") and (filter is None or f.startswith(filter))
        ]

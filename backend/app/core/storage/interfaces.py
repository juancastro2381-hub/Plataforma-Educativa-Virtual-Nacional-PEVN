"""
PEVN Backend — Secure Storage Driver Interface (Phase B3-H11)

Abstracts the low-level physical storage operations (local filesystem, S3, MinIO)
to decouple the domain model from underlying storage mechanisms.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import BinaryIO


class IStorageDriver(ABC):
    """Abstract interface for raw physical storage drivers."""

    @abstractmethod
    async def save(
        self,
        relative_path: str,
        data: bytes | BinaryIO,
    ) -> str:
        """
        Persist data to the target relative path.
        Returns the confirmed relative path.
        """
        ...

    @abstractmethod
    async def delete(self, relative_path: str) -> bool:
        """
        Delete file at relative path if it exists.
        Returns True if deleted, False if not found.
        """
        ...

    @abstractmethod
    async def exists(self, relative_path: str) -> bool:
        """Check if file exists at relative path."""
        ...

    @abstractmethod
    def get_physical_path(self, relative_path: str) -> str:
        """
        Get the fully resolved absolute physical path for streaming.
        Raises SecurityError / ValueError on path traversal attempt.
        """
        ...

    @abstractmethod
    async def read(self, relative_path: str) -> bytes:
        """Read full binary content from relative path."""
        ...

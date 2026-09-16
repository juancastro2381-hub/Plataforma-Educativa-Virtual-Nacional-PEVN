"""
PEVN Backend — Local Filesystem Storage Driver (Phase B3-H11)

Implements IStorageDriver on the server filesystem with strict path-traversal
prevention and directory isolation.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import BinaryIO

from app.core.storage.interfaces import IStorageDriver
from app.exceptions.errors import PEVNException


class StorageSecurityError(PEVNException):
    """Raised when an illegal path traversal or unauthorized storage access is attempted."""

    default_code = "STORAGE_SECURITY_ERROR"
    default_status = 400

    def __init__(self, message: str = "Violación de seguridad en ruta de almacenamiento."):
        super().__init__(message=message, code=self.default_code, status_code=self.default_status)


class LocalStorageDriver(IStorageDriver):
    """
    Local filesystem storage driver.
    Enforces that all operations remain strictly within base_path.
    """

    def __init__(self, base_path: str | Path) -> None:
        self.base_path = Path(base_path).resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _resolve_safe_path(self, relative_path: str) -> Path:
        """
        Resolves the relative path against base_path and asserts that
        the target is strictly a descendant of base_path (prevents ../ traversal).
        """
        cleaned = relative_path.lstrip("/\\")
        target_path = (self.base_path / cleaned).resolve()
        try:
            target_path.relative_to(self.base_path)
        except ValueError as err:
            raise StorageSecurityError("Ruta de archivo inválida o intento de escape de directorio.") from err

        if os.name == "nt":
            str_path = str(target_path)
            if not str_path.startswith("\\\\?\\") and not str_path.startswith("//?/"):
                return Path(f"\\\\?\\{str_path}")
        return target_path

    async def save(
        self,
        relative_path: str,
        data: bytes | BinaryIO,
    ) -> str:
        target = self._resolve_safe_path(relative_path)

        def _write() -> None:
            os.makedirs(target.parent, exist_ok=True)
            if isinstance(data, bytes):
                target.write_bytes(data)
            else:
                with target.open("wb") as f:
                    data.seek(0)
                    while chunk := data.read(64 * 1024):
                        f.write(chunk)

        await asyncio.to_thread(_write)
        return relative_path

    async def delete(self, relative_path: str) -> bool:
        target = self._resolve_safe_path(relative_path)
        if not target.exists():
            return False

        def _delete() -> None:
            if target.is_file():
                target.unlink(missing_ok=True)

        await asyncio.to_thread(_delete)
        return True

    async def exists(self, relative_path: str) -> bool:
        target = self._resolve_safe_path(relative_path)
        return await asyncio.to_thread(lambda: target.is_file())

    def get_physical_path(self, relative_path: str) -> str:
        target = self._resolve_safe_path(relative_path)
        if not target.is_file():
            raise FileNotFoundError(f"Archivo físico no encontrado: {relative_path}")
        return str(target)

    async def read(self, relative_path: str) -> bytes:
        target = self._resolve_safe_path(relative_path)
        if not target.is_file():
            raise FileNotFoundError(f"Archivo físico no encontrado: {relative_path}")
        return await asyncio.to_thread(target.read_bytes)

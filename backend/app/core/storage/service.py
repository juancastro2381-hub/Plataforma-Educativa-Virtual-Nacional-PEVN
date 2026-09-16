"""
PEVN Backend — High-Level Secure Storage Service (Phase B3-H11)

Orchestrates upload validation, extension checking, magic bytes / MIME verification,
size limits, and secure relative path generation before persisting via IStorageDriver.
"""

from __future__ import annotations

import mimetypes
from pathlib import Path
import uuid
from typing import BinaryIO

from app.core.config import get_settings
from app.core.storage.interfaces import IStorageDriver
from app.core.storage.local import LocalStorageDriver
from app.exceptions.errors import PEVNException


class FileValidationError(PEVNException):
    """Raised when an uploaded file violates security or format policies."""

    default_code = "FILE_VALIDATION_ERROR"
    default_status = 400

    def __init__(self, message: str):
        super().__init__(message=message, code=self.default_code, status_code=self.default_status)


# Dangerous extensions that must ALWAYS be blocked regardless of other checks
FORBIDDEN_EXTENSIONS = {
    ".exe", ".sh", ".bash", ".php", ".phtml", ".php5", ".bat", ".cmd", ".com",
    ".js", ".mjs", ".ts", ".py", ".pyw", ".vbs", ".vbe", ".ps1", ".psm1",
    ".html", ".htm", ".xhtml", ".jar", ".war", ".jsp", ".asp", ".aspx",
    ".cgi", ".pl", ".dll", ".so", ".dylib", ".msi", ".scr", ".pif", ".hta",
}

# Magic bytes signatures for trusted formats
MAGIC_SIGNATURES: dict[str, list[bytes]] = {
    ".pdf": [b"%PDF-"],
    ".png": [b"\x89PNG\r\n\x1a\n"],
    ".jpg": [b"\xff\xd8\xff"],
    ".jpeg": [b"\xff\xd8\xff"],
    ".zip": [b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08"],
    ".docx": [b"PK\x03\x04"],
    ".xlsx": [b"PK\x03\x04"],
    ".pptx": [b"PK\x03\x04"],
    ".doc": [b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"],
    ".xls": [b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"],
    ".ppt": [b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"],
}


class StorageService:
    """
    High-level secure storage service.
    Coordinates security policies and delegates physical operations to driver.
    """

    def __init__(self, driver: IStorageDriver | None = None) -> None:
        settings = get_settings()
        self.driver = driver or LocalStorageDriver(base_path=settings.STORAGE_LOCAL_PATH)
        self.max_size_bytes = settings.MAX_UPLOAD_SIZE_BYTES
        self.allowed_extensions = set(ext.lower() for ext in settings.ALLOWED_FILE_EXTENSIONS)

    def validate_file(
        self,
        filename: str,
        content: bytes,
        declared_mime_type: str | None = None,
    ) -> tuple[str, str]:
        """
        Validates filename, extension, file size, and magic bytes.
        Returns normalized (safe_extension, confirmed_mime_type).
        """
        # 1. Size check
        if len(content) == 0:
            raise FileValidationError("El archivo no puede estar vacío.")

        if len(content) > self.max_size_bytes:
            max_mb = self.max_size_bytes // (1024 * 1024)
            raise FileValidationError(
                f"El archivo excede el tamaño máximo permitido de {max_mb} MB."
            )

        # 2. Extension check
        ext = Path(filename).suffix.lower()
        if not ext:
            raise FileValidationError("El archivo no tiene una extensión válida.")

        if ext in FORBIDDEN_EXTENSIONS:
            raise FileValidationError(
                f"La extensión '{ext}' representa un tipo de archivo ejecutable no permitido por seguridad."
            )

        if ext not in self.allowed_extensions:
            allowed_list = ", ".join(sorted(self.allowed_extensions))
            raise FileValidationError(
                f"Extensión '{ext}' no permitida. Formatos válidos: {allowed_list}"
            )

        # 3. Magic bytes validation (when signature is known)
        expected_magics = MAGIC_SIGNATURES.get(ext)
        if expected_magics:
            matches_magic = any(content.startswith(sig) for sig in expected_magics)
            if not matches_magic:
                raise FileValidationError(
                    f"El contenido binario del archivo no coincide con la extensión declarada '{ext}'."
                )

        # 4. Determine MIME type
        guessed_mime, _ = mimetypes.guess_type(filename)
        mime_type = declared_mime_type or guessed_mime or "application/octet-stream"

        return ext, mime_type

    def build_activity_resource_path(
        self,
        institution_id: uuid.UUID,
        activity_id: uuid.UUID,
        resource_id: uuid.UUID,
        extension: str,
    ) -> str:
        """
        Constructs an opaque physical storage relative path:
        <institution_uuid>/activities/<activity_uuid>/resources/<resource_uuid>.<safe_ext>
        """
        safe_ext = extension.lower() if extension.startswith(".") else f".{extension.lower()}"
        return f"{institution_id}/activities/{activity_id}/resources/{resource_id}{safe_ext}"

    async def save_activity_resource(
        self,
        institution_id: uuid.UUID,
        activity_id: uuid.UUID,
        resource_id: uuid.UUID,
        original_filename: str,
        content: bytes,
        declared_mime_type: str | None = None,
    ) -> tuple[str, str, int]:
        """
        Validates, builds safe path, and persists an activity resource file.
        Returns (relative_file_path, mime_type, file_size_bytes).
        """
        safe_ext, mime_type = self.validate_file(
            filename=original_filename,
            content=content,
            declared_mime_type=declared_mime_type,
        )
        rel_path = self.build_activity_resource_path(
            institution_id=institution_id,
            activity_id=activity_id,
            resource_id=resource_id,
            extension=safe_ext,
        )
        await self.driver.save(rel_path, content)
        return rel_path, mime_type, len(content)

    def build_submission_attachment_path(
        self,
        institution_id: uuid.UUID,
        activity_id: uuid.UUID,
        student_id: uuid.UUID,
        submission_id: uuid.UUID,
        attachment_id: uuid.UUID,
        extension: str,
    ) -> str:
        """
        Constructs an opaque physical storage relative path for student submission attachments:
        <institution_uuid>/submissions/<activity_uuid>/<student_uuid>/<submission_uuid>/<attachment_uuid>.<safe_ext>
        """
        safe_ext = extension.lower() if extension.startswith(".") else f".{extension.lower()}"
        return f"{institution_id}/submissions/{activity_id}/{student_id}/{submission_id}/{attachment_id}{safe_ext}"

    async def save_submission_attachment(
        self,
        institution_id: uuid.UUID,
        activity_id: uuid.UUID,
        student_id: uuid.UUID,
        submission_id: uuid.UUID,
        attachment_id: uuid.UUID,
        original_filename: str,
        content: bytes,
        declared_mime_type: str | None = None,
    ) -> tuple[str, str, int]:
        """
        Validates, builds safe segregated path, and persists a student submission attachment file.
        Returns (relative_file_path, mime_type, file_size_bytes).
        """
        safe_ext, mime_type = self.validate_file(
            filename=original_filename,
            content=content,
            declared_mime_type=declared_mime_type,
        )
        rel_path = self.build_submission_attachment_path(
            institution_id=institution_id,
            activity_id=activity_id,
            student_id=student_id,
            submission_id=submission_id,
            attachment_id=attachment_id,
            extension=safe_ext,
        )
        await self.driver.save(rel_path, content)
        return rel_path, mime_type, len(content)

    async def delete_file(self, relative_path: str) -> bool:
        """Delete file from storage."""
        return await self.driver.delete(relative_path)

    def get_physical_path(self, relative_path: str) -> str:
        """Retrieve physical path for FileResponse streaming."""
        return self.driver.get_physical_path(relative_path)

    async def read_file(self, relative_path: str) -> bytes:
        """Read binary content."""
        return await self.driver.read(relative_path)


_storage_service_singleton: StorageService | None = None


def get_storage_service() -> StorageService:
    """Dependency / Singleton getter for StorageService."""
    global _storage_service_singleton
    if _storage_service_singleton is None:
        _storage_service_singleton = StorageService()
    return _storage_service_singleton

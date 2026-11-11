"""Shared Document Storage contract."""

from .errors import (
    ConflictError,
    FileTooLargeError,
    InvalidOperationError,
    InvalidRequestError,
    NotFoundError,
    PermissionDeniedError,
    ProviderError,
    ProviderUnavailableError,
    StorageError,
)
from .interface import DocumentStorage
from .models import FileInfo
from .streams import BytesDownload, DownloadStream

__all__ = [
    "BytesDownload",
    "ConflictError",
    "DocumentStorage",
    "DownloadStream",
    "FileInfo",
    "FileTooLargeError",
    "InvalidOperationError",
    "InvalidRequestError",
    "NotFoundError",
    "PermissionDeniedError",
    "ProviderError",
    "ProviderUnavailableError",
    "StorageError",
]

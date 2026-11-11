"""Tests for the shared Document Storage contract."""

import pytest

from cloud_storage_api import (
    ConflictError,
    DocumentStorage,
    FileTooLargeError,
    InvalidOperationError,
    InvalidRequestError,
    NotFoundError,
    PermissionDeniedError,
    ProviderError,
    ProviderUnavailableError,
    StorageError,
)


@pytest.mark.parametrize(
    ("error", "status", "code"),
    [
        (InvalidRequestError, 400, "invalid_request"),
        (PermissionDeniedError, 403, "permission_denied"),
        (NotFoundError, 404, "not_found"),
        (ConflictError, 409, "conflict"),
        (FileTooLargeError, 413, "file_too_large"),
        (InvalidOperationError, 422, "invalid_operation"),
        (ProviderError, 502, "provider_error"),
        (ProviderUnavailableError, 503, "provider_unavailable"),
    ],
)
def test_error_status_and_code(error: type[StorageError], status: int, code: str) -> None:
    """Each error carries the status and code from the shared table."""
    exc = error("Error occurred")
    assert exc.status_code == status
    assert exc.code == code
    assert exc.message == "Error occurred"


def test_existing_bytes_operations_remain_abstract() -> None:
    """Keep the original byte-based operations abstract."""
    assert {"create", "replace", "download"} <= DocumentStorage.__abstractmethods__

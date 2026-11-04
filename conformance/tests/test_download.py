"""Tests for GET /files/download."""

from http import HTTPStatus

import httpx2
import pytest

from conformance.tests.conftest import assert_error, create, download

# The download route isn't final yet.
pytestmark = pytest.mark.proposed("download route")


@pytest.mark.parametrize("data", [b"hello", b"", bytes(range(256)) * 4096], ids=["text", "empty", "1mb-binary"])
def test_download(api: httpx2.Client, root: str, data: bytes) -> None:
    """Download returns the same bytes that were uploaded."""
    create(api, root + "/file.bin", data)
    resp = download(api, root + "/file.bin")
    assert resp.status_code == HTTPStatus.OK
    assert resp.content == data


def test_download_missing_file(api: httpx2.Client, root: str) -> None:
    """Missing file is 404."""
    assert_error(download(api, root + "/missing.txt"), HTTPStatus.NOT_FOUND, "not_found")

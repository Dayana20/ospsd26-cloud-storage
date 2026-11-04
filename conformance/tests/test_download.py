"""Download: returns the exact stored bytes (memo, "Download")."""

from http import HTTPStatus

import httpx2
import pytest

from conformance.tests.conftest import ROUTES_QUESTION, assert_error, create, download

# Teams 1 and 3 use this route today. Team 6 uses GET /files/{key}.
pytestmark = pytest.mark.proposed(ROUTES_QUESTION)


@pytest.mark.parametrize(
    "data",
    [b"hello", b"", bytes(range(256)) * 4096],
    ids=["text", "empty", "binary-1MiB"],
)
def test_download_returns_the_exact_bytes(api: httpx2.Client, root: str, data: bytes) -> None:
    """The downloaded bytes equal the uploaded bytes."""
    create(api, root + "/file.bin", data)
    response = download(api, root + "/file.bin")
    assert response.status_code == HTTPStatus.OK
    assert response.content == data


def test_downloading_a_missing_file_is_not_found(api: httpx2.Client, root: str) -> None:
    """A missing file is 404 not_found."""
    assert_error(download(api, root + "/missing.txt"), HTTPStatus.NOT_FOUND, "not_found")

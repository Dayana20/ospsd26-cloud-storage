"""Tests for PUT /files (replace)."""

from http import HTTPStatus

import httpx2

from conformance.tests.conftest import assert_error, create, download, metadata, upload


def test_replace(api: httpx2.Client, root: str) -> None:
    """Replace returns 200 and the new file info."""
    create(api, root + "/file.txt", b"old")
    resp = upload(api, root + "/file.txt", b"new data", method="PUT")
    assert resp.status_code == HTTPStatus.OK
    assert resp.json()["size"] == len(b"new data")
    assert download(api, root + "/file.txt").content == b"new data"


def test_replace_missing_file(api: httpx2.Client, root: str) -> None:
    """Replace doesn't create files. A missing file is 404."""
    create(api, root + "/other.txt")
    assert_error(upload(api, root + "/missing.txt", method="PUT"), HTTPStatus.NOT_FOUND, "not_found")
    assert_error(metadata(api, root + "/missing.txt"), HTTPStatus.NOT_FOUND, "not_found")

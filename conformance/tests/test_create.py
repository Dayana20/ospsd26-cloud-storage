"""Tests for POST /files (create)."""

from http import HTTPStatus

import httpx2

from conformance.tests.conftest import assert_error, create, download, list_folder, upload


def test_create(api: httpx2.Client, root: str) -> None:
    """Create returns 201 and the file info."""
    resp = upload(api, root + "/report.pdf", b"pdf data")
    assert resp.status_code == HTTPStatus.CREATED
    info = resp.json()
    assert info["path"] == root + "/report.pdf"
    assert info["name"] == "report.pdf"
    assert info["size"] == len(b"pdf data")


def test_create_empty_file(api: httpx2.Client, root: str) -> None:
    """0-byte files are allowed."""
    assert create(api, root + "/empty.txt", b"")["size"] == 0


def test_create_in_new_folder(api: httpx2.Client, root: str) -> None:
    """Parent folders are created automatically."""
    create(api, root + "/a/b/c.txt")
    assert list_folder(api, root + "/a/b").status_code == HTTPStatus.OK


def test_create_existing_file(api: httpx2.Client, root: str) -> None:
    """Creating over an existing file gives 409 and doesn't overwrite it."""
    create(api, root + "/file.txt", b"old")
    assert_error(upload(api, root + "/file.txt", b"new"), HTTPStatus.CONFLICT, "conflict")
    assert download(api, root + "/file.txt").content == b"old"


def test_create_missing_file_field(api: httpx2.Client, root: str) -> None:
    """The file field is required."""
    resp = api.post("/files", data={"path": root + "/a.txt"})
    assert_error(resp, HTTPStatus.BAD_REQUEST, "invalid_request")


def test_create_missing_path_field(api: httpx2.Client) -> None:
    """The path field is required."""
    resp = api.post("/files", files={"file": ("f", b"x")})
    assert_error(resp, HTTPStatus.BAD_REQUEST, "invalid_request")

"""Create: POST /files with the form fields file and path (memo, "Create")."""

from http import HTTPStatus

import httpx2
import pytest

from conformance.tests.conftest import ERRORS_ISSUE, assert_error, create, download, upload


def test_create_returns_201_and_the_file_info(api: httpx2.Client, root: str) -> None:
    """A new file is 201 with its file info."""
    data = b"%PDF-1.7 content"
    response = upload(api, root + "/report.pdf", data)
    assert response.status_code == HTTPStatus.CREATED
    info = response.json()
    assert info["path"] == root + "/report.pdf"
    assert info["name"] == "report.pdf"
    assert info["size"] == len(data)


def test_create_accepts_an_empty_file(api: httpx2.Client, root: str) -> None:
    """A 0-byte file is a valid file."""
    assert create(api, root + "/empty.txt", b"")["size"] == 0


def test_create_makes_the_parent_folders(api: httpx2.Client, root: str) -> None:
    """Creating a file makes its folders listable, with no separate folder call."""
    create(api, root + "/a/b/c.txt")
    assert api.get("/files", params={"path": root + "/a/b"}).status_code == HTTPStatus.OK


@pytest.mark.proposed(ERRORS_ISSUE)
def test_creating_an_existing_file_is_a_conflict_and_keeps_the_old_contents(api: httpx2.Client, root: str) -> None:
    """Create never overwrites, even with the same bytes."""
    create(api, root + "/file.txt", b"old")
    assert_error(upload(api, root + "/file.txt", b"new"), HTTPStatus.CONFLICT, "conflict")
    assert download(api, root + "/file.txt").content == b"old"


@pytest.mark.parametrize("missing", ["file", "path"])
def test_a_missing_form_field_is_invalid_request(api: httpx2.Client, root: str, missing: str) -> None:
    """Both form fields are required."""
    data = {} if missing == "path" else {"path": root + "/a.txt"}
    files = None if missing == "file" else {"file": ("f", b"x")}
    response = api.post("/files", data=data, files=files)
    assert_error(response, HTTPStatus.BAD_REQUEST, "invalid_request")

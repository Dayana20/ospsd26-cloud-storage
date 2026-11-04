"""Tests for PATCH /files (move)."""

from http import HTTPStatus

import httpx2
import pytest

from conformance.tests.conftest import assert_error, create, download, metadata, move

pytestmark = pytest.mark.proposed("move, issue #5")


def test_move(api: httpx2.Client, root: str) -> None:
    """Move returns the file info at the new path."""
    create(api, root + "/old.txt", b"12345")
    resp = move(api, root + "/old.txt", root + "/new.txt")
    assert resp.status_code == HTTPStatus.OK
    info = resp.json()
    assert info["path"] == root + "/new.txt"
    assert info["name"] == "new.txt"
    assert info["size"] == len(b"12345")


def test_move_removes_old_path(api: httpx2.Client, root: str) -> None:
    """After a move the old path is gone and the bytes are unchanged."""
    create(api, root + "/old.txt", b"contents")
    move(api, root + "/old.txt", root + "/sub/new.txt")
    assert_error(metadata(api, root + "/old.txt"), HTTPStatus.NOT_FOUND, "not_found")
    assert download(api, root + "/sub/new.txt").content == b"contents"


def test_move_onto_existing_file(api: httpx2.Client, root: str) -> None:
    """Move never overwrites. Both files stay as they were."""
    create(api, root + "/a.txt", b"a")
    create(api, root + "/b.txt", b"b")
    assert_error(move(api, root + "/a.txt", root + "/b.txt"), HTTPStatus.CONFLICT, "conflict")
    assert download(api, root + "/a.txt").content == b"a"
    assert download(api, root + "/b.txt").content == b"b"


@pytest.mark.parametrize("new_name", ["file.txt", "FILE.txt"], ids=["same", "case-only"])
def test_move_same_path(api: httpx2.Client, root: str, new_name: str) -> None:
    """Moving to the same path, or only changing case, is 422."""
    create(api, root + "/file.txt")
    resp = move(api, root + "/file.txt", root + "/" + new_name)
    assert_error(resp, HTTPStatus.UNPROCESSABLE_ENTITY, "invalid_operation")
    assert metadata(api, root + "/file.txt").status_code == HTTPStatus.OK


def test_move_folder(api: httpx2.Client, root: str) -> None:
    """Folders can't be moved."""
    create(api, root + "/folder/inner.txt")
    resp = move(api, root + "/folder", root + "/elsewhere")
    assert_error(resp, HTTPStatus.UNPROCESSABLE_ENTITY, "invalid_operation")


def test_move_missing_file(api: httpx2.Client, root: str) -> None:
    """Missing file is 404."""
    create(api, root + "/other.txt")
    assert_error(move(api, root + "/missing.txt", root + "/new.txt"), HTTPStatus.NOT_FOUND, "not_found")


@pytest.mark.parametrize("body", [{}, {"new_path": ""}, {"new_path": "/a/../b"}])
def test_move_bad_new_path(api: httpx2.Client, root: str, body: dict[str, str]) -> None:
    """new_path is required and must be a valid path."""
    create(api, root + "/file.txt")
    resp = api.patch("/files", params={"path": root + "/file.txt"}, json=body)
    assert_error(resp, HTTPStatus.BAD_REQUEST, "invalid_request")


def test_move_body_not_json(api: httpx2.Client, root: str) -> None:
    """A body that isn't JSON is 400."""
    create(api, root + "/file.txt")
    resp = api.patch(
        "/files",
        params={"path": root + "/file.txt"},
        content=b"not json",
        headers={"Content-Type": "application/json"},
    )
    assert_error(resp, HTTPStatus.BAD_REQUEST, "invalid_request")

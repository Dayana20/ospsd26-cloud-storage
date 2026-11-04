"""Move: PATCH /files?path=<from> with {"new_path": "<to>"} (issue #5)."""

from http import HTTPStatus

import httpx2
import pytest

from conformance.tests.conftest import MOVE_ISSUE, assert_error, create, download, metadata

pytestmark = pytest.mark.proposed(MOVE_ISSUE)


def move(api: httpx2.Client, path: str, new_path: str) -> httpx2.Response:
    """Move a file."""
    return api.patch("/files", params={"path": path}, json={"new_path": new_path})


def test_move_returns_the_file_info_at_the_new_path(api: httpx2.Client, root: str) -> None:
    """A move is 200 with the file info at the new path."""
    data = b"12345"
    create(api, root + "/old.txt", data)
    response = move(api, root + "/old.txt", root + "/new.txt")
    assert response.status_code == HTTPStatus.OK
    info = response.json()
    assert info["path"] == root + "/new.txt"
    assert info["name"] == "new.txt"
    assert info["size"] == len(data)


def test_move_leaves_nothing_at_the_old_path_and_keeps_the_bytes(api: httpx2.Client, root: str) -> None:
    """The old path is empty afterwards, and the bytes did not change."""
    create(api, root + "/old.txt", b"contents")
    move(api, root + "/old.txt", root + "/sub/new.txt")
    assert_error(metadata(api, root + "/old.txt"), HTTPStatus.NOT_FOUND, "not_found")
    assert download(api, root + "/sub/new.txt").content == b"contents"


def test_moving_onto_an_existing_file_is_a_conflict_and_changes_nothing(api: httpx2.Client, root: str) -> None:
    """Move never overwrites."""
    create(api, root + "/a.txt", b"a")
    create(api, root + "/b.txt", b"b")
    assert_error(move(api, root + "/a.txt", root + "/b.txt"), HTTPStatus.CONFLICT, "conflict")
    assert download(api, root + "/a.txt").content == b"a"
    assert download(api, root + "/b.txt").content == b"b"


@pytest.mark.parametrize("new_name", ["file.txt", "FILE.txt"], ids=["same", "case-only"])
def test_moving_to_the_same_path_or_only_changing_case_is_invalid(api: httpx2.Client, root: str, new_name: str) -> None:
    """Dropbox and S3 cannot agree on case-only renames, so both are 422."""
    create(api, root + "/file.txt")
    response = move(api, root + "/file.txt", root + "/" + new_name)
    assert_error(response, HTTPStatus.UNPROCESSABLE_ENTITY, "invalid_operation")
    assert metadata(api, root + "/file.txt").status_code == HTTPStatus.OK


def test_moving_a_folder_is_invalid(api: httpx2.Client, root: str) -> None:
    """Move is files only for now."""
    create(api, root + "/folder/inner.txt")
    response = move(api, root + "/folder", root + "/elsewhere")
    assert_error(response, HTTPStatus.UNPROCESSABLE_ENTITY, "invalid_operation")


def test_moving_a_missing_file_is_not_found(api: httpx2.Client, root: str) -> None:
    """A missing source is 404 not_found."""
    create(api, root + "/other.txt")
    assert_error(move(api, root + "/missing.txt", root + "/new.txt"), HTTPStatus.NOT_FOUND, "not_found")


@pytest.mark.parametrize("body", [{}, {"new_path": ""}, {"new_path": "/a/../b"}])
def test_a_missing_or_malformed_new_path_is_invalid_request(api: httpx2.Client, root: str, body: dict[str, str]) -> None:
    """new_path is required and follows the path rule."""
    create(api, root + "/file.txt")
    response = api.patch("/files", params={"path": root + "/file.txt"}, json=body)
    assert_error(response, HTTPStatus.BAD_REQUEST, "invalid_request")


def test_a_body_that_is_not_json_is_invalid_request(api: httpx2.Client, root: str) -> None:
    """A body that does not parse is a bad request, not a server error."""
    create(api, root + "/file.txt")
    response = api.patch(
        "/files",
        params={"path": root + "/file.txt"},
        content=b"not json",
        headers={"Content-Type": "application/json"},
    )
    assert_error(response, HTTPStatus.BAD_REQUEST, "invalid_request")

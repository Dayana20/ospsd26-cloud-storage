"""Delete: DELETE /files?path=<path>, files and whole folders (memo, "Delete")."""

from http import HTTPStatus

import httpx2

from conformance.tests.conftest import assert_error, create, metadata


def delete(api: httpx2.Client, path: str) -> httpx2.Response:
    """Delete a file or folder."""
    return api.delete("/files", params={"path": path})


def test_delete_returns_204_with_no_body_and_the_file_is_gone(api: httpx2.Client, root: str) -> None:
    """A delete is 204 with an empty body, and the file is gone."""
    create(api, root + "/file.txt")
    response = delete(api, root + "/file.txt")
    assert response.status_code == HTTPStatus.NO_CONTENT
    assert response.content == b""
    assert_error(metadata(api, root + "/file.txt"), HTTPStatus.NOT_FOUND, "not_found")


def test_deleting_a_folder_removes_everything_in_it(api: httpx2.Client, root: str) -> None:
    """A folder goes with everything under it, at every depth, and nothing else."""
    create(api, root + "/keep.txt")
    create(api, root + "/folder/a.txt")
    create(api, root + "/folder/sub/b.txt")
    assert delete(api, root + "/folder").status_code == HTTPStatus.NO_CONTENT
    assert_error(metadata(api, root + "/folder/a.txt"), HTTPStatus.NOT_FOUND, "not_found")
    assert_error(metadata(api, root + "/folder/sub/b.txt"), HTTPStatus.NOT_FOUND, "not_found")
    assert metadata(api, root + "/keep.txt").status_code == HTTPStatus.OK


def test_deleting_a_folder_spares_a_sibling_with_the_same_prefix(api: httpx2.Client, root: str) -> None:
    """A folder delete does not treat its path as a plain text prefix."""
    create(api, root + "/data/a.txt")
    create(api, root + "/data-backup/a.txt")
    delete(api, root + "/data")
    assert metadata(api, root + "/data-backup/a.txt").status_code == HTTPStatus.OK


def test_deleting_a_missing_path_is_not_found(api: httpx2.Client, root: str) -> None:
    """A missing path is 404 not_found."""
    create(api, root + "/other.txt")
    assert_error(delete(api, root + "/missing.txt"), HTTPStatus.NOT_FOUND, "not_found")


def test_deleting_twice_is_not_found_the_second_time(api: httpx2.Client, root: str) -> None:
    """The second delete of the same file is 404 not_found."""
    create(api, root + "/file.txt")
    delete(api, root + "/file.txt")
    assert_error(delete(api, root + "/file.txt"), HTTPStatus.NOT_FOUND, "not_found")

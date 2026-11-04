"""Replace: PUT /files with the same form fields as create (memo, "Replace")."""

from http import HTTPStatus

import httpx2

from conformance.tests.conftest import assert_error, create, download, metadata, upload


def test_replace_returns_200_and_the_new_file_info(api: httpx2.Client, root: str) -> None:
    """Replacing an existing file is 200 with the new file info."""
    data = b"new contents"
    create(api, root + "/file.txt", b"old")
    response = upload(api, root + "/file.txt", data, method="PUT")
    assert response.status_code == HTTPStatus.OK
    info = response.json()
    assert info["path"] == root + "/file.txt"
    assert info["size"] == len(data)


def test_replace_changes_the_downloaded_bytes(api: httpx2.Client, root: str) -> None:
    """A download after a replace returns the new bytes."""
    create(api, root + "/file.txt", b"old")
    upload(api, root + "/file.txt", b"new", method="PUT")
    assert download(api, root + "/file.txt").content == b"new"


def test_replacing_a_missing_file_is_not_found_and_creates_nothing(api: httpx2.Client, root: str) -> None:
    """Replace never creates, so create and replace never overlap."""
    create(api, root + "/other.txt")  # so the folder exists
    assert_error(upload(api, root + "/missing.txt", method="PUT"), HTTPStatus.NOT_FOUND, "not_found")
    assert_error(metadata(api, root + "/missing.txt"), HTTPStatus.NOT_FOUND, "not_found")

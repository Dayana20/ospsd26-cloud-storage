"""Tests for DELETE /files."""

from http import HTTPStatus

import httpx2

from conformance.tests.conftest import assert_error, create, delete, metadata


def test_delete(api: httpx2.Client, root: str) -> None:
    """Delete returns 204 with no body, and the file is gone."""
    create(api, root + "/file.txt")
    resp = delete(api, root + "/file.txt")
    assert resp.status_code == HTTPStatus.NO_CONTENT
    assert resp.content == b""
    assert_error(metadata(api, root + "/file.txt"), HTTPStatus.NOT_FOUND, "not_found")


def test_delete_folder(api: httpx2.Client, root: str) -> None:
    """Deleting a folder deletes everything in it, and nothing else."""
    create(api, root + "/keep.txt")
    create(api, root + "/folder/a.txt")
    create(api, root + "/folder/sub/b.txt")
    assert delete(api, root + "/folder").status_code == HTTPStatus.NO_CONTENT
    assert_error(metadata(api, root + "/folder/a.txt"), HTTPStatus.NOT_FOUND, "not_found")
    assert_error(metadata(api, root + "/folder/sub/b.txt"), HTTPStatus.NOT_FOUND, "not_found")
    assert metadata(api, root + "/keep.txt").status_code == HTTPStatus.OK


def test_delete_folder_keeps_similar_names(api: httpx2.Client, root: str) -> None:
    """Deleting /data doesn't touch /data-backup."""
    create(api, root + "/data/a.txt")
    create(api, root + "/data-backup/a.txt")
    delete(api, root + "/data")
    assert metadata(api, root + "/data-backup/a.txt").status_code == HTTPStatus.OK


def test_delete_missing(api: httpx2.Client, root: str) -> None:
    """Missing path is 404."""
    create(api, root + "/other.txt")
    assert_error(delete(api, root + "/missing.txt"), HTTPStatus.NOT_FOUND, "not_found")


def test_delete_twice(api: httpx2.Client, root: str) -> None:
    """The second delete is 404."""
    create(api, root + "/file.txt")
    delete(api, root + "/file.txt")
    assert_error(delete(api, root + "/file.txt"), HTTPStatus.NOT_FOUND, "not_found")

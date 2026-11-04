"""Tests for path handling."""

from http import HTTPStatus

import httpx2
import pytest

from conformance.tests.conftest import assert_error, create, delete, download, metadata, upload


def test_leading_slash_added(api: httpx2.Client, root: str) -> None:
    """A path without a leading / comes back with one."""
    info = create(api, root.lstrip("/") + "/notes.txt")
    assert info["path"] == root + "/notes.txt"
    assert info["name"] == "notes.txt"


def test_with_and_without_slash_same_file(api: httpx2.Client, root: str) -> None:
    """/a/b.txt and a/b.txt are the same file."""
    create(api, root + "/notes.txt")
    resp = metadata(api, root.lstrip("/") + "/notes.txt")
    assert resp.status_code == HTTPStatus.OK
    assert resp.json()["path"] == root + "/notes.txt"


@pytest.mark.parametrize("bad", ["", "/", "{root}/", "{root}//a.txt", "{root}/./a.txt", "{root}/../a.txt"])
def test_bad_path(api: httpx2.Client, root: str, bad: str) -> None:
    """Bad paths are rejected with 400."""
    assert_error(upload(api, bad.format(root=root)), HTTPStatus.BAD_REQUEST, "invalid_request")


def test_bad_path_other_operations(api: httpx2.Client, root: str) -> None:
    """Metadata, download and delete check the path too."""
    bad = root + "/../a.txt"
    assert_error(metadata(api, bad), HTTPStatus.BAD_REQUEST, "invalid_request")
    assert_error(download(api, bad), HTTPStatus.BAD_REQUEST, "invalid_request")
    assert_error(delete(api, bad), HTTPStatus.BAD_REQUEST, "invalid_request")

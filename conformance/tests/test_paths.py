"""Paths: with or without a leading /, always returned with one (memo, "Paths")."""

from http import HTTPStatus

import httpx2
import pytest

from conformance.tests.conftest import assert_error, create, download, metadata, upload


def test_a_path_without_a_leading_slash_is_returned_with_one(api: httpx2.Client, root: str) -> None:
    """The service adds the leading / and reports the canonical path."""
    info = create(api, root.lstrip("/") + "/notes.txt")
    assert info["path"] == root + "/notes.txt"
    assert info["name"] == "notes.txt"


def test_both_forms_name_the_same_file(api: httpx2.Client, root: str) -> None:
    """A path with and without the leading / reach the same file."""
    create(api, root + "/notes.txt")
    response = metadata(api, root.lstrip("/") + "/notes.txt")
    assert response.status_code == HTTPStatus.OK
    assert response.json()["path"] == root + "/notes.txt"


@pytest.mark.parametrize(
    "bad",
    ["", "/", "{root}/", "{root}//a.txt", "{root}/./a.txt", "{root}/../a.txt", "{root}/.."],
)
def test_a_malformed_path_is_invalid_request(api: httpx2.Client, root: str, bad: str) -> None:
    """Empty paths, empty segments, '.', '..', and a trailing / are 400 invalid_request."""
    assert_error(upload(api, bad.format(root=root)), HTTPStatus.BAD_REQUEST, "invalid_request")


def test_a_malformed_path_is_rejected_by_every_operation(api: httpx2.Client, root: str) -> None:
    """Reads and deletes apply the same path rule as uploads."""
    bad = root + "/../a.txt"
    assert_error(metadata(api, bad), HTTPStatus.BAD_REQUEST, "invalid_request")
    assert_error(download(api, bad), HTTPStatus.BAD_REQUEST, "invalid_request")
    assert_error(api.delete("/files", params={"path": bad}), HTTPStatus.BAD_REQUEST, "invalid_request")

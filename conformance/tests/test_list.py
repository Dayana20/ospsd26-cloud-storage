"""List: GET /files?path=<folder>, the direct children in one response (issue #3)."""

from http import HTTPStatus

import httpx2
import pytest

from conformance.tests.conftest import FOLDERS_QUESTION, LIST_ISSUE, assert_error, create

pytestmark = pytest.mark.proposed(LIST_ISSUE)


def list_folder(api: httpx2.Client, folder: str) -> httpx2.Response:
    """List a folder."""
    return api.get("/files", params={"path": folder})


def test_list_returns_the_direct_children_sorted_by_path(api: httpx2.Client, root: str) -> None:
    """Entries come back sorted by path, whatever the upload order."""
    for name in ["b.txt", "a.txt", "c.txt"]:
        create(api, f"{root}/docs/{name}")
    response = list_folder(api, root + "/docs")
    assert response.status_code == HTTPStatus.OK
    assert [entry["path"] for entry in response.json()] == [
        f"{root}/docs/a.txt",
        f"{root}/docs/b.txt",
        f"{root}/docs/c.txt",
    ]


def test_list_is_one_level_and_includes_folders_once(api: httpx2.Client, root: str) -> None:
    """A subfolder appears once, and nothing under it appears."""
    create(api, root + "/top.txt")
    create(api, root + "/sub/one.txt")
    create(api, root + "/sub/deeper/two.txt")
    paths = [entry["path"] for entry in list_folder(api, root).json()]
    assert paths == [root + "/sub", root + "/top.txt"]


def test_list_entries_are_file_info(api: httpx2.Client, root: str) -> None:
    """A file's entry matches the file info that create returned."""
    created = create(api, root + "/file.txt", b"12345")
    [entry] = list_folder(api, root).json()
    for field in ["id", "name", "path", "size"]:
        assert entry[field] == created[field]


@pytest.mark.proposed(FOLDERS_QUESTION)
def test_list_marks_files_and_folders(api: httpx2.Client, root: str) -> None:
    """Each entry has type "file" or "folder"."""
    create(api, root + "/file.txt")
    create(api, root + "/sub/inner.txt")
    types = {entry["name"]: entry["type"] for entry in list_folder(api, root).json()}
    assert types == {"file.txt": "file", "sub": "folder"}


def test_list_returns_every_entry_in_one_response(api: httpx2.Client, root: str) -> None:
    """The response is a plain array, with no cursor or page fields.

    Crossing a provider page (1000 keys on S3) would take too long against a real
    service, so this only checks the shape.
    """
    count = 30
    for number in range(count):
        create(api, f"{root}/many/{number:03}.txt", b"")
    entries = list_folder(api, root + "/many").json()
    assert isinstance(entries, list)
    assert len(entries) == count


def test_listing_a_missing_folder_is_not_found(api: httpx2.Client, root: str) -> None:
    """A missing folder is 404 not_found."""
    assert_error(list_folder(api, root + "/missing"), HTTPStatus.NOT_FOUND, "not_found")


def test_listing_with_a_malformed_path_is_invalid_request(api: httpx2.Client, root: str) -> None:
    """The path rule applies to list too."""
    assert_error(list_folder(api, root + "/../x"), HTTPStatus.BAD_REQUEST, "invalid_request")

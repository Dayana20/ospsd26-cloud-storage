"""Tests for GET /files (list a folder)."""

from http import HTTPStatus

import httpx2
import pytest

from conformance.tests.conftest import assert_error, create, list_folder

# The list route isn't final yet (#10).
pytestmark = pytest.mark.proposed("list route")


def test_list_sorted(api: httpx2.Client, root: str) -> None:
    """Entries are sorted by path."""
    for name in ["b.txt", "a.txt", "c.txt"]:
        create(api, f"{root}/docs/{name}")
    resp = list_folder(api, root + "/docs")
    assert resp.status_code == HTTPStatus.OK
    assert [e["path"] for e in resp.json()] == [f"{root}/docs/a.txt", f"{root}/docs/b.txt", f"{root}/docs/c.txt"]


def test_list_one_level(api: httpx2.Client, root: str) -> None:
    """Only direct children are listed. Subfolders show up once."""
    create(api, root + "/top.txt")
    create(api, root + "/sub/one.txt")
    create(api, root + "/sub/deeper/two.txt")
    assert [e["path"] for e in list_folder(api, root).json()] == [root + "/sub", root + "/top.txt"]


def test_list_file_info(api: httpx2.Client, root: str) -> None:
    """A file entry has the same info as create returned."""
    created = create(api, root + "/file.txt", b"12345")
    [entry] = list_folder(api, root).json()
    for field in ["id", "name", "path", "size"]:
        assert entry[field] == created[field]


def test_list_types(api: httpx2.Client, root: str) -> None:
    """Each entry has type file or folder. Folders have no size or modified_at."""
    create(api, root + "/file.txt")
    create(api, root + "/sub/inner.txt")
    entries = {e["name"]: e for e in list_folder(api, root).json()}
    assert entries["file.txt"]["type"] == "file"
    assert entries["sub"]["type"] == "folder"
    assert entries["sub"]["size"] is None
    assert entries["sub"]["modified_at"] is None


def test_list_no_paging(api: httpx2.Client, root: str) -> None:
    """The whole folder comes back as one array, no cursor."""
    count = 30
    for i in range(count):
        create(api, f"{root}/many/{i:03}.txt", b"")
    entries = list_folder(api, root + "/many").json()
    assert isinstance(entries, list)
    assert len(entries) == count


def test_list_missing_folder(api: httpx2.Client, root: str) -> None:
    """Missing folder is 404."""
    assert_error(list_folder(api, root + "/missing"), HTTPStatus.NOT_FOUND, "not_found")


def test_list_bad_path(api: httpx2.Client, root: str) -> None:
    """Bad path is 400."""
    assert_error(list_folder(api, root + "/../x"), HTTPStatus.BAD_REQUEST, "invalid_request")

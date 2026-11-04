"""The consumer workflow from the memo, run unchanged against every service."""

from http import HTTPStatus

import httpx2

from conformance.tests.conftest import assert_error, download, metadata


def test_consumer_workflow(api: httpx2.Client, root: str) -> None:
    """Upload, read, download, list, move, read again, delete, and confirm it is gone."""
    data = b"quarterly report\n" * 1000
    path = root + "/reports/q3.txt"
    new_path = root + "/archive/q3-final.txt"

    # Upload a file.
    created = api.post("/files", data={"path": path}, files={"file": ("q3.txt", data)})
    assert created.status_code == HTTPStatus.CREATED, created.text

    # Read its metadata.
    info = metadata(api, path)
    assert info.status_code == HTTPStatus.OK
    assert info.json()["size"] == len(data)

    # Download it and compare the bytes.
    downloaded = download(api, path)
    assert downloaded.status_code == HTTPStatus.OK
    assert downloaded.content == data

    # List its folder.
    listing = api.get("/files", params={"path": root + "/reports"})
    assert listing.status_code == HTTPStatus.OK
    assert [entry["path"] for entry in listing.json()] == [path]

    # Move it.
    moved = api.patch("/files", params={"path": path}, json={"new_path": new_path})
    assert moved.status_code == HTTPStatus.OK, moved.text
    assert moved.json()["path"] == new_path

    # Read its metadata at the new path.
    info = metadata(api, new_path)
    assert info.status_code == HTTPStatus.OK
    assert info.json()["size"] == len(data)
    assert_error(metadata(api, path), HTTPStatus.NOT_FOUND, "not_found")

    # Delete it.
    assert api.delete("/files", params={"path": new_path}).status_code == HTTPStatus.NO_CONTENT

    # Confirm that metadata now returns 404.
    assert_error(metadata(api, new_path), HTTPStatus.NOT_FOUND, "not_found")

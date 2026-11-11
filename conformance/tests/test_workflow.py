"""End-to-end workflow a client would run against any of the services."""

from http import HTTPStatus

import httpx2

from conformance.tests.conftest import assert_error, delete, download, list_folder, metadata, move, upload


def test_workflow(api: httpx2.Client, root: str) -> None:
    """Upload, metadata, download, list, move, metadata, delete, 404."""
    data = b"quarterly report\n" * 1000
    path = root + "/reports/q3.txt"
    new_path = root + "/archive/q3-final.txt"

    resp = upload(api, path, data)
    assert resp.status_code == HTTPStatus.CREATED, resp.text

    resp = metadata(api, path)
    assert resp.status_code == HTTPStatus.OK
    assert resp.json()["size"] == len(data)

    resp = download(api, path)
    assert resp.status_code == HTTPStatus.OK
    assert resp.content == data

    resp = list_folder(api, root + "/reports")
    assert resp.status_code == HTTPStatus.OK
    assert [e["path"] for e in resp.json()] == [path]

    resp = move(api, path, new_path)
    assert resp.status_code == HTTPStatus.OK, resp.text
    assert resp.json()["path"] == new_path

    resp = metadata(api, new_path)
    assert resp.status_code == HTTPStatus.OK
    assert resp.json()["size"] == len(data)
    assert_error(metadata(api, path), HTTPStatus.NOT_FOUND, "not_found")

    assert delete(api, new_path).status_code == HTTPStatus.NO_CONTENT
    assert_error(metadata(api, new_path), HTTPStatus.NOT_FOUND, "not_found")

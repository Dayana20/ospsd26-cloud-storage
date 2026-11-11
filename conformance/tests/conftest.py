"""Fixtures and helpers.

By default the tests run against the in-memory reference app. To test a real
service, set CONFORMANCE_BASE_URL, e.g. CONFORMANCE_BASE_URL=http://127.0.0.1:8000
"""

import os
import uuid
from collections.abc import Iterator
from typing import Any

import httpx2
import pytest
from fastapi.testclient import TestClient

from conformance.reference.app import build_app


@pytest.fixture(scope="session")
def api() -> Iterator[httpx2.Client]:
    """HTTP client for the service being tested."""
    base_url = os.environ.get("CONFORMANCE_BASE_URL")
    if base_url:
        with httpx2.Client(base_url=base_url, timeout=60) as client:
            yield client
    else:
        with TestClient(build_app()) as client:
            yield client


@pytest.fixture
def root(api: httpx2.Client) -> Iterator[str]:
    """Random folder for a test. Deleted after the test."""
    folder = f"/conformance-{uuid.uuid4().hex}"
    yield folder
    api.delete("/files", params={"path": folder})


def upload(api: httpx2.Client, path: str, data: bytes = b"hello", method: str = "POST") -> httpx2.Response:
    """POST (create) or PUT (replace) a file."""
    return api.request(method, "/files", data={"path": path}, files={"file": ("f", data)})


def create(api: httpx2.Client, path: str, data: bytes = b"hello") -> dict[str, Any]:
    """Create a file and return its info. Fails the test if it doesn't work."""
    resp = upload(api, path, data)
    assert resp.status_code == httpx2.codes.CREATED, resp.text
    info: dict[str, Any] = resp.json()
    return info


def metadata(api: httpx2.Client, path: str) -> httpx2.Response:
    """GET /files/metadata."""
    return api.get("/files/metadata", params={"path": path})


def download(api: httpx2.Client, path: str) -> httpx2.Response:
    """GET /files/download."""
    return api.get("/files/download", params={"path": path})


def list_folder(api: httpx2.Client, path: str) -> httpx2.Response:
    """GET /files."""
    return api.get("/files", params={"path": path})


def move(api: httpx2.Client, path: str, new_path: str) -> httpx2.Response:
    """PATCH /files."""
    return api.patch("/files", params={"path": path}, json={"new_path": new_path})


def delete(api: httpx2.Client, path: str) -> httpx2.Response:
    """DELETE /files."""
    return api.delete("/files", params={"path": path})


def assert_error(resp: httpx2.Response, status: int, code: str) -> None:
    """Check the status and the error body."""
    assert resp.status_code == status, resp.text
    body = resp.json()
    assert list(body) == ["error"]
    assert set(body["error"]) == {"code", "message"}
    assert body["error"]["code"] == code

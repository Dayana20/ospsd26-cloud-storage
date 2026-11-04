"""Fixtures and helpers for the conformance suite.

Without settings, the tests run against the reference service in this process: no
network, no credentials. Set ``CONFORMANCE_BASE_URL`` to run the same tests against a
running service:

    CONFORMANCE_BASE_URL=http://127.0.0.1:8000 uv run pytest conformance/tests
"""

import os
import uuid
from collections.abc import Iterator
from typing import Any

import httpx2
import pytest
from fastapi.testclient import TestClient

from conformance.reference.app import build_app

# Sources that tests marked @pytest.mark.proposed(...) follow.
ISSUES = "https://github.com/Dayana20/ospsd26-cloud-storage/issues/"
ERRORS_ISSUE = ISSUES + "4"
MOVE_ISSUE = ISSUES + "5"
LIST_ISSUE = ISSUES + "3"
ROUTES_QUESTION = "memo open question 2: routes for download and metadata"
FOLDERS_QUESTION = "memo open question 4: how list marks folders"
TIMESTAMP_QUESTION = "memo, The data model: modified_at in UTC ending in Z"


@pytest.fixture(scope="session")
def api() -> Iterator[httpx2.Client]:
    """Return a client for the service under test."""
    base_url = os.environ.get("CONFORMANCE_BASE_URL")
    if base_url:
        with httpx2.Client(base_url=base_url, timeout=60) as client:
            yield client
    else:
        with TestClient(build_app()) as client:
            yield client


@pytest.fixture
def root(api: httpx2.Client) -> Iterator[str]:
    """Return a unique folder for one test, and delete it with everything in it afterwards."""
    folder = f"/conformance-{uuid.uuid4().hex}"
    yield folder
    api.delete("/files", params={"path": folder})  # 404 if the test left nothing


def upload(api: httpx2.Client, path: str, data: bytes = b"hello", method: str = "POST") -> httpx2.Response:
    """Create (POST) or replace (PUT) a file."""
    return api.request(method, "/files", data={"path": path}, files={"file": ("f", data)})


def create(api: httpx2.Client, path: str, data: bytes = b"hello") -> dict[str, Any]:
    """Create a file that a test needs, and return its file info."""
    response = upload(api, path, data)
    assert response.status_code == httpx2.codes.CREATED, response.text
    info: dict[str, Any] = response.json()
    return info


def metadata(api: httpx2.Client, path: str) -> httpx2.Response:
    """Read a file's metadata."""
    return api.get("/files/metadata", params={"path": path})


def download(api: httpx2.Client, path: str) -> httpx2.Response:
    """Download a file."""
    return api.get("/files/download", params={"path": path})


def assert_error(response: httpx2.Response, status: int, code: str) -> None:
    """Check that the response is the shared error body with this status and code."""
    assert response.status_code == status, response.text
    body = response.json()
    assert set(body) == {"error"}
    assert set(body["error"]) == {"code", "message"}
    assert body["error"]["code"] == code
    assert isinstance(body["error"]["message"], str)

"""Tests for GET /files/metadata."""

from datetime import UTC, datetime, timedelta
from http import HTTPStatus

import httpx2
import pytest

from conformance.tests.conftest import assert_error, create, metadata

# The metadata route isn't final yet.
pytestmark = pytest.mark.proposed("metadata route")

FIELDS = {"id", "name", "path", "size", "modified_at"}


def test_metadata(api: httpx2.Client, root: str) -> None:
    """Metadata has id, name, path, size and modified_at."""
    create(api, root + "/docs/report.pdf", b"12345")
    resp = metadata(api, root + "/docs/report.pdf")
    assert resp.status_code == HTTPStatus.OK
    info = resp.json()
    assert set(info) >= FIELDS  # extra fields are fine
    assert info["id"] is None or isinstance(info["id"], str)  # S3 has no id
    assert info["name"] == "report.pdf"
    assert info["path"] == root + "/docs/report.pdf"
    assert info["size"] == len(b"12345")


def test_metadata_same_as_create(api: httpx2.Client, root: str) -> None:
    """Metadata matches what create returned."""
    created = create(api, root + "/file.txt")
    info = metadata(api, root + "/file.txt").json()
    for field in ["id", "name", "path", "size"]:
        assert info[field] == created[field]


def test_modified_at_has_timezone(api: httpx2.Client, root: str) -> None:
    """modified_at is an ISO 8601 time with a timezone, close to now."""
    create(api, root + "/file.txt")
    modified = datetime.fromisoformat(metadata(api, root + "/file.txt").json()["modified_at"])
    assert modified.tzinfo is not None
    assert abs(datetime.now(UTC) - modified) < timedelta(hours=1)


@pytest.mark.proposed("UTC timestamps")
def test_modified_at_is_utc(api: httpx2.Client, root: str) -> None:
    """modified_at ends in Z."""
    create(api, root + "/file.txt")
    assert metadata(api, root + "/file.txt").json()["modified_at"].endswith("Z")


def test_metadata_missing_file(api: httpx2.Client, root: str) -> None:
    """Missing file is 404."""
    assert_error(metadata(api, root + "/missing.txt"), HTTPStatus.NOT_FOUND, "not_found")

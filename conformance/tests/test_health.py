"""Tests for the health checks."""

from http import HTTPStatus

import httpx2


def test_health(api: httpx2.Client) -> None:
    """GET /health is ok."""
    resp = api.get("/health")
    assert resp.status_code == HTTPStatus.OK
    assert resp.json() == {"status": "ok"}


def test_provider_health(api: httpx2.Client) -> None:
    """GET /health/provider is ok."""
    resp = api.get("/health/provider")
    assert resp.status_code == HTTPStatus.OK
    assert resp.json() == {"status": "ok"}

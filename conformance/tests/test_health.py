"""Health: one check for the service, one for its storage provider (memo, "Health")."""

from http import HTTPStatus

import httpx2


def test_service_health_is_ok(api: httpx2.Client) -> None:
    """GET /health answers 200 {"status": "ok"} while the service runs."""
    response = api.get("/health")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"status": "ok"}


def test_provider_health_is_ok(api: httpx2.Client) -> None:
    """GET /health/provider answers 200 {"status": "ok"} when the provider is reachable."""
    response = api.get("/health/provider")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"status": "ok"}

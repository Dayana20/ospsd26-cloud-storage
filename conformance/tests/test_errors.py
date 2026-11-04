"""Tests for errors that aren't tied to one operation."""

from http import HTTPStatus

import httpx2
import pytest

from conformance.tests.conftest import assert_error

pytestmark = pytest.mark.proposed("error codes, issue #4")


def test_unknown_route(api: httpx2.Client) -> None:
    """Unknown route is 404 route_not_found, not not_found."""
    assert_error(api.get("/no-such-route"), HTTPStatus.NOT_FOUND, "route_not_found")


def test_wrong_method(api: httpx2.Client) -> None:
    """Wrong method is 405 with an Allow header."""
    resp = api.post("/health")
    assert_error(resp, HTTPStatus.METHOD_NOT_ALLOWED, "method_not_allowed")
    assert "GET" in resp.headers["Allow"]

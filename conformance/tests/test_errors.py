"""The shared error body: {"error": {"code", "message"}} (memo, "Errors", and issue #4).

Every other file checks the body through ``assert_error``. These tests cover the errors
that happen outside any operation.
"""

from http import HTTPStatus

import httpx2
import pytest

from conformance.tests.conftest import ERRORS_ISSUE, assert_error

pytestmark = pytest.mark.proposed(ERRORS_ISSUE)


def test_an_unknown_route_is_route_not_found(api: httpx2.Client) -> None:
    """A wrong URL is told apart from a missing file."""
    assert_error(api.get("/no-such-route"), HTTPStatus.NOT_FOUND, "route_not_found")


def test_a_wrong_method_is_method_not_allowed_with_an_allow_header(api: httpx2.Client) -> None:
    """A method the path does not accept is 405, and Allow lists the ones it does."""
    response = api.post("/health")
    assert_error(response, HTTPStatus.METHOD_NOT_ALLOWED, "method_not_allowed")
    assert "GET" in response.headers["Allow"]

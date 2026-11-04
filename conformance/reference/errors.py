"""Error responses: {"error": {"code": ..., "message": ...}}."""

from http import HTTPStatus


class ApiError(Exception):
    """An error with an HTTP status and an error code."""

    def __init__(self, status: int, code: str, message: str) -> None:
        """Create the error."""
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message

    def body(self) -> dict[str, dict[str, str]]:
        """Return the JSON error body."""
        return {"error": {"code": self.code, "message": self.message}}


def invalid_request(message: str) -> ApiError:
    """Return a 400 error."""
    return ApiError(HTTPStatus.BAD_REQUEST, "invalid_request", message)


def not_found(path: str) -> ApiError:
    """Return a 404 error."""
    return ApiError(HTTPStatus.NOT_FOUND, "not_found", f"{path} not found")


def conflict(path: str) -> ApiError:
    """Return a 409 error."""
    return ApiError(HTTPStatus.CONFLICT, "conflict", f"{path} already exists")


def invalid_operation(message: str) -> ApiError:
    """Return a 422 error."""
    return ApiError(HTTPStatus.UNPROCESSABLE_ENTITY, "invalid_operation", message)

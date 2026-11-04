"""The shared error body (memo, "Errors", and issue #4).

Every error is ``{"error": {"code": "...", "message": "..."}}``. Callers branch on the
status and the code, never on the message.
"""

from http import HTTPStatus


class ContractError(Exception):
    """An error response the contract defines: a status, a stable code, and a message."""

    def __init__(self, status: int, code: str, message: str) -> None:
        """Keep the parts of the response."""
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message

    def body(self) -> dict[str, dict[str, str]]:
        """Return the JSON body of the response."""
        return {"error": {"code": self.code, "message": self.message}}


def invalid_request(message: str) -> ContractError:
    """Return a 400 for input the contract rejects."""
    return ContractError(HTTPStatus.BAD_REQUEST, "invalid_request", message)


def not_found(path: str) -> ContractError:
    """Return a 404 for a path where nothing exists."""
    return ContractError(HTTPStatus.NOT_FOUND, "not_found", f"nothing exists at {path}")


def conflict(path: str) -> ContractError:
    """Return a 409 for a destination that is already taken."""
    return ContractError(HTTPStatus.CONFLICT, "conflict", f"something already exists at {path}")


def invalid_operation(message: str) -> ContractError:
    """Return a 422 for valid input asking for something the contract forbids."""
    return ContractError(HTTPStatus.UNPROCESSABLE_ENTITY, "invalid_operation", message)

"""The reference service: the shared HTTP contract over an in-memory store.

Run it as a server with ``uv run uvicorn conformance.reference.app:app``. Each route
follows the Oct 28 memo for the Document Storage vertical and issues #3 (list),
#4 (errors), and #5 (move). README.md lists the rules that are still proposals.
"""

from http import HTTPStatus
from typing import Annotated, Any

from fastapi import FastAPI, File, Form, Query, Request, Response, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException

from conformance.reference.errors import ContractError, invalid_request
from conformance.reference.paths import canonical_folder, canonical_path
from conformance.reference.store import Folder, Store, StoredFile


class MoveRequest(BaseModel):
    """The body of a move request."""

    new_path: str


def file_info(stored: StoredFile) -> dict[str, Any]:
    """Return the shared file info object (memo, "The data model")."""
    return {
        "id": stored.id,
        "name": stored.path.rsplit("/", 1)[1],
        "path": stored.path,
        "size": len(stored.data),
        "modified_at": stored.modified_at.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
    }


def list_entry(entry: StoredFile | Folder) -> dict[str, Any]:
    """Return a file info object with ``type``. Folders have no id, size, or modification time."""
    if isinstance(entry, Folder):
        return {
            "type": "folder",
            "id": None,
            "name": entry.path.rsplit("/", 1)[1],
            "path": entry.path,
            "size": None,
            "modified_at": None,
        }
    return {"type": "file", **file_info(entry)}


def build_app() -> FastAPI:
    """Return a reference service with an empty store."""
    app = FastAPI(title="Document Storage reference service")
    _add_routes(app, Store())
    _add_error_handlers(app)
    return app


def _add_routes(app: FastAPI, store: Store) -> None:
    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/health/provider")
    def provider_health() -> dict[str, str]:
        return {"status": "ok"}  # Memory is always reachable.

    @app.post("/files", status_code=HTTPStatus.CREATED)
    def create_file(file: Annotated[UploadFile, File()], path: Annotated[str, Form()]) -> dict[str, Any]:
        return file_info(store.create(canonical_path(path), file.file.read()))

    @app.put("/files")
    def replace_file(file: Annotated[UploadFile, File()], path: Annotated[str, Form()]) -> dict[str, Any]:
        return file_info(store.replace(canonical_path(path), file.file.read()))

    @app.get("/files/download")
    def download_file(path: Annotated[str, Query()]) -> Response:
        stored = store.get(canonical_path(path))
        name = stored.path.rsplit("/", 1)[1]
        return Response(
            stored.data,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{name}"'},
        )

    @app.get("/files/metadata")
    def file_metadata(path: Annotated[str, Query()]) -> dict[str, Any]:
        return file_info(store.get(canonical_path(path)))

    @app.get("/files")
    def list_files(path: Annotated[str, Query()]) -> list[dict[str, Any]]:
        return [list_entry(entry) for entry in store.list_folder(canonical_folder(path))]

    @app.patch("/files")
    def move_file(path: Annotated[str, Query()], body: MoveRequest) -> dict[str, Any]:
        return file_info(store.move(canonical_path(path), canonical_path(body.new_path)))

    @app.delete("/files", status_code=HTTPStatus.NO_CONTENT)
    def delete_file(path: Annotated[str, Query()]) -> Response:
        store.delete(canonical_path(path))
        return Response(status_code=HTTPStatus.NO_CONTENT)


def _add_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ContractError)
    def contract_error(_request: Request, exc: Exception) -> JSONResponse:
        if not isinstance(exc, ContractError):
            raise TypeError
        return JSONResponse(exc.body(), status_code=exc.status)

    @app.exception_handler(RequestValidationError)
    def validation_error(request: Request, exc: Exception) -> JSONResponse:
        if not isinstance(exc, RequestValidationError):
            raise TypeError
        problem = exc.errors()[0]
        return contract_error(request, invalid_request(f"{problem['loc'][-1]}: {problem['msg']}"))

    @app.exception_handler(HTTPException)
    def http_error(request: Request, exc: Exception) -> JSONResponse:
        if not isinstance(exc, HTTPException):
            raise TypeError
        if exc.status_code == HTTPStatus.NOT_FOUND:
            error = ContractError(exc.status_code, "route_not_found", "no route matches this path")
        elif exc.status_code == HTTPStatus.METHOD_NOT_ALLOWED:
            error = ContractError(exc.status_code, "method_not_allowed", f"this path does not accept {request.method}")
        else:
            error = invalid_request(str(exc.detail))
        response = contract_error(request, error)
        response.headers.update(exc.headers or {})
        return response

    @app.exception_handler(Exception)
    def internal_error(request: Request, _exc: Exception) -> JSONResponse:
        error = ContractError(HTTPStatus.INTERNAL_SERVER_ERROR, "internal_error", "the service failed unexpectedly")
        return contract_error(request, error)


app = build_app()

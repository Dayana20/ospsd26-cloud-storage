"""FastAPI app that serves any DocumentStorage over the shared HTTP API.

By default it uses the in-memory MemoryStorage. Run it with:
uv run --with uvicorn uvicorn conformance.reference.app:app
"""

from dataclasses import asdict
from http import HTTPStatus
from typing import Annotated, Any

from cloud_storage_api.errors import InvalidRequestError, StorageError
from fastapi import FastAPI, File, Form, Request, Response, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException

from cloud_storage_api import DocumentStorage
from conformance.reference.paths import clean_folder, clean_path
from conformance.reference.store import MemoryStorage


class MoveBody(BaseModel):
    """Request body for PATCH /files."""

    new_path: str


def build_app(storage: DocumentStorage | None = None) -> FastAPI:
    """Create the app. Uses a new MemoryStorage if no storage is given."""
    app = FastAPI(title="Storage reference implementation")
    add_routes(app, storage or MemoryStorage())
    add_error_handlers(app)
    return app


def add_routes(app: FastAPI, storage: DocumentStorage) -> None:
    """Register the API routes."""

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/health/provider")
    def provider_health() -> dict[str, str]:
        storage.check_health()
        return {"status": "ok"}

    @app.post("/files", status_code=HTTPStatus.CREATED)
    def create(file: Annotated[UploadFile, File()], path: Annotated[str, Form()]) -> dict[str, Any]:
        return asdict(storage.create(clean_path(path), file.file.read()))

    @app.put("/files")
    def replace(file: Annotated[UploadFile, File()], path: Annotated[str, Form()]) -> dict[str, Any]:
        return asdict(storage.replace(clean_path(path), file.file.read()))

    @app.get("/files/download")
    def download(path: str) -> Response:
        path = clean_path(path)
        name = path.rsplit("/", 1)[1]
        headers = {"Content-Disposition": f'attachment; filename="{name}"'}
        return Response(storage.download(path), media_type="application/octet-stream", headers=headers)

    @app.get("/files/metadata")
    def metadata(path: str) -> dict[str, Any]:
        return asdict(storage.get_metadata(clean_path(path)))

    @app.get("/files")
    def list_files(path: str) -> list[dict[str, Any]]:
        return [asdict(info) for info in storage.list_files(clean_folder(path))]

    @app.patch("/files")
    def move(path: str, body: MoveBody) -> dict[str, Any]:
        return asdict(storage.move(clean_path(path), clean_path(body.new_path)))

    @app.delete("/files", status_code=HTTPStatus.NO_CONTENT)
    def delete(path: str) -> Response:
        storage.delete(clean_path(path))
        return Response(status_code=HTTPStatus.NO_CONTENT)


def error_response(status: int, code: str, message: str) -> JSONResponse:
    """Return the {"error": {"code", "message"}} body."""
    return JSONResponse({"error": {"code": code, "message": message}}, status_code=status)


def add_error_handlers(app: FastAPI) -> None:
    """Make every error use the shared error body."""

    @app.exception_handler(StorageError)
    def storage_error(_: Request, exc: StorageError) -> JSONResponse:
        return error_response(exc.status_code, exc.code, exc.message)

    @app.exception_handler(RequestValidationError)
    def validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        problem = exc.errors()[0]
        err = InvalidRequestError(f"{problem['loc'][-1]}: {problem['msg']}")
        return error_response(err.status_code, err.code, err.message)

    @app.exception_handler(HTTPException)
    def http_error(request: Request, exc: HTTPException) -> JSONResponse:
        if exc.status_code == HTTPStatus.NOT_FOUND:
            response = error_response(exc.status_code, "route_not_found", "no such route")
        elif exc.status_code == HTTPStatus.METHOD_NOT_ALLOWED:
            response = error_response(exc.status_code, "method_not_allowed", f"{request.method} not allowed here")
        else:
            response = error_response(HTTPStatus.BAD_REQUEST, "invalid_request", str(exc.detail))
        response.headers.update(exc.headers or {})
        return response

    @app.exception_handler(Exception)
    def unexpected_error(_: Request, __: Exception) -> JSONResponse:
        return error_response(HTTPStatus.INTERNAL_SERVER_ERROR, "internal_error", "unexpected error")


app = build_app()

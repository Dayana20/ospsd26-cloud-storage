"""FastAPI app for the reference implementation.

Run it with: uv run --with uvicorn uvicorn conformance.reference.app:app
"""

from http import HTTPStatus
from typing import Annotated, Any

from fastapi import FastAPI, File, Form, Request, Response, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException

from conformance.reference.errors import ApiError, invalid_request
from conformance.reference.paths import clean_folder, clean_path
from conformance.reference.store import Folder, Store, StoredFile


class MoveBody(BaseModel):
    """Request body for PATCH /files."""

    new_path: str


def file_info(f: StoredFile) -> dict[str, Any]:
    """Return the file info JSON."""
    return {
        "id": f.id,
        "name": f.path.rsplit("/", 1)[1],
        "path": f.path,
        "size": len(f.data),
        "modified_at": f.modified_at.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
    }


def list_item(item: StoredFile | Folder) -> dict[str, Any]:
    """Return a listing entry. Folders only have a name and path."""
    if isinstance(item, Folder):
        name = item.path.rsplit("/", 1)[1]
        return {"type": "folder", "id": None, "name": name, "path": item.path, "size": None, "modified_at": None}
    return {"type": "file", **file_info(item)}


def build_app() -> FastAPI:
    """Create the app with an empty store."""
    app = FastAPI(title="Storage reference implementation")
    add_routes(app, Store())
    add_error_handlers(app)
    return app


def add_routes(app: FastAPI, store: Store) -> None:
    """Register the API routes."""

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/health/provider")
    def provider_health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/files", status_code=HTTPStatus.CREATED)
    def create(file: Annotated[UploadFile, File()], path: Annotated[str, Form()]) -> dict[str, Any]:
        return file_info(store.create(clean_path(path), file.file.read()))

    @app.put("/files")
    def replace(file: Annotated[UploadFile, File()], path: Annotated[str, Form()]) -> dict[str, Any]:
        return file_info(store.replace(clean_path(path), file.file.read()))

    @app.get("/files/download")
    def download(path: str) -> Response:
        f = store.get(clean_path(path))
        name = f.path.rsplit("/", 1)[1]
        headers = {"Content-Disposition": f'attachment; filename="{name}"'}
        return Response(f.data, media_type="application/octet-stream", headers=headers)

    @app.get("/files/metadata")
    def metadata(path: str) -> dict[str, Any]:
        return file_info(store.get(clean_path(path)))

    @app.get("/files")
    def list_files(path: str) -> list[dict[str, Any]]:
        return [list_item(item) for item in store.list_folder(clean_folder(path))]

    @app.patch("/files")
    def move(path: str, body: MoveBody) -> dict[str, Any]:
        return file_info(store.move(clean_path(path), clean_path(body.new_path)))

    @app.delete("/files", status_code=HTTPStatus.NO_CONTENT)
    def delete(path: str) -> Response:
        store.delete(clean_path(path))
        return Response(status_code=HTTPStatus.NO_CONTENT)


def error_response(err: ApiError) -> JSONResponse:
    """Turn an ApiError into a JSON response."""
    return JSONResponse(err.body(), status_code=err.status)


def add_error_handlers(app: FastAPI) -> None:
    """Make every error use the {"error": {"code", "message"}} body."""

    @app.exception_handler(ApiError)
    def api_error(_: Request, exc: ApiError) -> JSONResponse:
        return error_response(exc)

    @app.exception_handler(RequestValidationError)
    def validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        problem = exc.errors()[0]
        return error_response(invalid_request(f"{problem['loc'][-1]}: {problem['msg']}"))

    @app.exception_handler(HTTPException)
    def http_error(request: Request, exc: HTTPException) -> JSONResponse:
        if exc.status_code == HTTPStatus.NOT_FOUND:
            err = ApiError(exc.status_code, "route_not_found", "no such route")
        elif exc.status_code == HTTPStatus.METHOD_NOT_ALLOWED:
            err = ApiError(exc.status_code, "method_not_allowed", f"{request.method} not allowed here")
        else:
            err = invalid_request(str(exc.detail))
        response = error_response(err)
        response.headers.update(exc.headers or {})
        return response

    @app.exception_handler(Exception)
    def unexpected_error(_: Request, __: Exception) -> JSONResponse:
        return error_response(ApiError(HTTPStatus.INTERNAL_SERVER_ERROR, "internal_error", "unexpected error"))


app = build_app()

"""Path validation. Paths are returned with a leading slash."""

from cloud_storage_api.errors import InvalidRequestError

MAX_PATH_BYTES = 1024


def clean_path(raw: str) -> str:
    """Add a leading slash and reject empty, '.', '..' or trailing-slash paths."""
    path = raw if raw.startswith("/") else "/" + raw
    if path == "/" or path.endswith("/"):
        msg = "path must not be empty or end with /"
        raise InvalidRequestError(msg)
    if any(part in {"", ".", ".."} for part in path[1:].split("/")):
        msg = "path must not contain empty, '.' or '..' parts"
        raise InvalidRequestError(msg)
    if len(path.encode()) > MAX_PATH_BYTES:
        msg = f"path is longer than {MAX_PATH_BYTES} bytes"
        raise InvalidRequestError(msg)
    return path


def clean_folder(raw: str) -> str:
    """Like clean_path, but allow the root folder."""
    if raw in {"", "/"}:
        return "/"
    return clean_path(raw)

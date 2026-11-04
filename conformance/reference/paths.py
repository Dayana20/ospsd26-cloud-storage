"""The shared path rule (memo, "Paths").

Callers may send a path with or without a leading ``/``. The service turns it into one
canonical form that starts with ``/``, and every response uses that form. Empty paths,
empty segments, ``.``, ``..``, and a trailing ``/`` are rejected.
"""

from conformance.reference.errors import invalid_request

# Team 6's limit, the only one confirmed so far. The shared limit is the smallest one
# all three services support.
MAX_PATH_BYTES = 1024


def canonical_path(raw: str) -> str:
    """Return the canonical form of a file or folder path, or raise ``invalid_request``."""
    path = raw if raw.startswith("/") else "/" + raw
    problem = None
    if path == "/":
        problem = "path must not be empty"
    elif path.endswith("/"):
        problem = "path must not end with /"
    elif any(segment in {"", ".", ".."} for segment in path[1:].split("/")):
        problem = "path must not contain empty, '.' or '..' segments"
    elif len(path.encode()) > MAX_PATH_BYTES:
        problem = f"path must be at most {MAX_PATH_BYTES} UTF-8 bytes"
    if problem is not None:
        raise invalid_request(problem)
    return path


def canonical_folder(raw: str) -> str:
    """Return the canonical form of a folder path, where ``/`` or ``""`` is the root."""
    if raw in {"", "/"}:
        return "/"
    return canonical_path(raw)

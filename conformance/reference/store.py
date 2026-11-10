"""In-memory DocumentStorage.

Folders aren't stored. A folder exists as long as there is a file under it (like S3).
"""

import hashlib
import uuid
from dataclasses import dataclass, replace
from datetime import UTC, datetime

from cloud_storage_api.errors import ConflictError, InvalidOperationError, NotFoundError

from cloud_storage_api import DocumentStorage, FileInfo


@dataclass(frozen=True)
class _File:
    id: str
    data: bytes
    modified_at: datetime


class MemoryStorage(DocumentStorage):
    """Files kept in a dict by path."""

    def __init__(self) -> None:
        """Start with no files."""
        self.files: dict[str, _File] = {}

    def create(self, path: str, content: bytes) -> FileInfo:
        """Add a new file. Fails if something is already at path."""
        if self._exists(path):
            raise _conflict(path)
        self._check_parents(path)
        return self._save(path, content, uuid.uuid4().hex)

    def replace(self, path: str, content: bytes) -> FileInfo:
        """Overwrite an existing file."""
        return self._save(path, content, self._get(path).id)

    def download(self, path: str) -> bytes:
        """Return the file's bytes."""
        return self._get(path).data

    def get_metadata(self, path: str) -> FileInfo:
        """Return the file's info."""
        return _info(path, self._get(path))

    def list_files(self, path: str) -> list[FileInfo]:
        """Return the files and folders directly inside path, sorted by path."""
        if path in self.files:
            msg = f"{path} is a file"
            raise InvalidOperationError(msg)
        if path != "/" and not self._is_folder(path):
            raise _not_found(path)
        prefix = "/" if path == "/" else path + "/"
        children: dict[str, FileInfo] = {}
        for file_path, f in self.files.items():
            if file_path.startswith(prefix):
                name, _, rest = file_path[len(prefix) :].partition("/")
                child = prefix + name
                children[child] = _folder(child) if rest else replace(_info(child, f), type="file")
        return [children[p] for p in sorted(children)]

    def move(self, from_path: str, to_path: str) -> FileInfo:
        """Move a file. Folders can't be moved."""
        if from_path not in self.files and self._is_folder(from_path):
            msg = "can't move a folder"
            raise InvalidOperationError(msg)
        f = self._get(from_path)
        if to_path.lower() == from_path.lower():
            msg = "new path is the same as path (ignoring case)"
            raise InvalidOperationError(msg)
        if self._exists(to_path):
            raise _conflict(to_path)
        self._check_parents(to_path)
        del self.files[from_path]
        self.files[to_path] = f
        return _info(to_path, f)

    def delete(self, path: str) -> None:
        """Delete a file, or a folder and everything in it."""
        if path in self.files:
            del self.files[path]
            return
        inside = [p for p in self.files if p.startswith(path + "/")]
        if not inside:
            raise _not_found(path)
        for p in inside:
            del self.files[p]

    def check_health(self) -> None:
        """Memory is always available."""

    def _get(self, path: str) -> _File:
        if path in self.files:
            return self.files[path]
        if self._is_folder(path):
            msg = f"{path} is a folder"
            raise InvalidOperationError(msg)
        raise _not_found(path)

    def _save(self, path: str, data: bytes, file_id: str) -> FileInfo:
        self.files[path] = _File(file_id, data, datetime.now(UTC))
        return _info(path, self.files[path])

    def _exists(self, path: str) -> bool:
        return path in self.files or self._is_folder(path)

    def _is_folder(self, path: str) -> bool:
        return any(p.startswith(path + "/") for p in self.files)

    def _check_parents(self, path: str) -> None:
        # e.g. can't create /a/b.txt when /a is a file
        parts = path.split("/")
        for i in range(2, len(parts)):
            parent = "/".join(parts[:i])
            if parent in self.files:
                msg = f"{parent} is a file"
                raise InvalidOperationError(msg)


def _info(path: str, f: _File) -> FileInfo:
    return FileInfo(
        id=f.id,
        name=path.rsplit("/", 1)[1],
        path=path,
        size=len(f.data),
        modified_at=f.modified_at.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        etag=hashlib.md5(f.data, usedforsecurity=False).hexdigest(),
        type=None,
    )


def _folder(path: str) -> FileInfo:
    name = path.rsplit("/", 1)[1]
    return FileInfo(id=None, name=name, path=path, size=None, modified_at=None, etag=None, type="folder")


def _not_found(path: str) -> NotFoundError:
    return NotFoundError(f"{path} not found")


def _conflict(path: str) -> ConflictError:
    return ConflictError(f"{path} already exists")

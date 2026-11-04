"""Files kept in a dict, keyed by canonical path.

Folders are implicit, as on S3: a folder exists while some file's path is under it.
Paths are compared exactly, so ``/A.txt`` and ``/a.txt`` are two files (S3's behavior).
"""

import uuid
from dataclasses import dataclass, replace
from datetime import UTC, datetime

from conformance.reference.errors import conflict, invalid_operation, not_found


@dataclass(frozen=True)
class StoredFile:
    """A file's contents and the facts the file info object reports."""

    path: str
    id: str
    data: bytes
    modified_at: datetime


@dataclass(frozen=True)
class Folder:
    """A folder in a listing. It has no data of its own."""

    path: str


class Store:
    """The reference service's storage. Each method enforces one operation's rules."""

    def __init__(self) -> None:
        """Start empty."""
        self._files: dict[str, StoredFile] = {}

    def create(self, path: str, data: bytes) -> StoredFile:
        """Store a new file. Never overwrites."""
        if self._exists(path):
            raise conflict(path)
        self._check_parents_are_folders(path)
        return self._write(path, data, uuid.uuid4().hex)

    def replace(self, path: str, data: bytes) -> StoredFile:
        """Replace an existing file's contents. Never creates one."""
        return self._write(path, data, self._file(path).id)

    def get(self, path: str) -> StoredFile:
        """Return the file at ``path``."""
        return self._file(path)

    def list_folder(self, folder: str) -> list[StoredFile | Folder]:
        """Return the direct children of ``folder``, sorted by path."""
        if folder in self._files:
            message = f"{folder} is a file"
            raise invalid_operation(message)
        if folder != "/" and not self._is_folder(folder):
            raise not_found(folder)
        base = "" if folder == "/" else folder
        children: dict[str, StoredFile | Folder] = {}
        for path, stored in self._files.items():
            if not path.startswith(base + "/"):
                continue
            name, _, rest = path[len(base) + 1 :].partition("/")
            child = f"{base}/{name}"
            children[child] = Folder(child) if rest else stored
        return [children[path] for path in sorted(children)]

    def move(self, path: str, new_path: str) -> StoredFile:
        """Move a file. Files only, and never onto something that exists."""
        if path not in self._files and self._is_folder(path):
            message = "only files can be moved"
            raise invalid_operation(message)
        stored = self._file(path)
        if new_path.casefold() == path.casefold():
            message = "new_path must differ from path by more than letter case"
            raise invalid_operation(message)
        if self._exists(new_path):
            raise conflict(new_path)
        self._check_parents_are_folders(new_path)
        del self._files[path]
        moved = replace(stored, path=new_path)
        self._files[new_path] = moved
        return moved

    def delete(self, path: str) -> None:
        """Delete a file, or a folder and everything under it."""
        if self._files.pop(path, None) is not None:
            return
        under = [key for key in self._files if key.startswith(path + "/")]
        if not under:
            raise not_found(path)
        for key in under:
            del self._files[key]

    def _file(self, path: str) -> StoredFile:
        stored = self._files.get(path)
        if stored is not None:
            return stored
        if self._is_folder(path):
            message = f"{path} is a folder"
            raise invalid_operation(message)
        raise not_found(path)

    def _write(self, path: str, data: bytes, file_id: str) -> StoredFile:
        stored = StoredFile(path=path, id=file_id, data=data, modified_at=datetime.now(UTC))
        self._files[path] = stored
        return stored

    def _exists(self, path: str) -> bool:
        return path in self._files or self._is_folder(path)

    def _is_folder(self, path: str) -> bool:
        return any(key.startswith(path + "/") for key in self._files)

    def _check_parents_are_folders(self, path: str) -> None:
        segments = path.split("/")
        for end in range(2, len(segments)):
            parent = "/".join(segments[:end])
            if parent in self._files:
                message = f"{parent} is a file, not a folder"
                raise invalid_operation(message)

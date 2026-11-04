"""In-memory file store.

Folders aren't stored. A folder exists as long as there is a file under it (like S3).
"""

import uuid
from dataclasses import dataclass, replace
from datetime import UTC, datetime

from conformance.reference.errors import conflict, invalid_operation, not_found


@dataclass(frozen=True)
class StoredFile:
    """A stored file."""

    path: str
    id: str
    data: bytes
    modified_at: datetime


@dataclass(frozen=True)
class Folder:
    """A folder in a listing."""

    path: str


class Store:
    """Files by path."""

    def __init__(self) -> None:
        """Start with no files."""
        self.files: dict[str, StoredFile] = {}

    def create(self, path: str, data: bytes) -> StoredFile:
        """Add a new file. Fails if something is already at path."""
        if self._exists(path):
            raise conflict(path)
        self._check_parents(path)
        return self._save(path, data, uuid.uuid4().hex)

    def replace(self, path: str, data: bytes) -> StoredFile:
        """Overwrite an existing file."""
        return self._save(path, data, self.get(path).id)

    def get(self, path: str) -> StoredFile:
        """Return the file at path."""
        if path in self.files:
            return self.files[path]
        if self._is_folder(path):
            msg = f"{path} is a folder"
            raise invalid_operation(msg)
        raise not_found(path)

    def list_folder(self, folder: str) -> list[StoredFile | Folder]:
        """Return the files and folders directly inside folder, sorted by path."""
        if folder in self.files:
            msg = f"{folder} is a file"
            raise invalid_operation(msg)
        if folder != "/" and not self._is_folder(folder):
            raise not_found(folder)
        prefix = "/" if folder == "/" else folder + "/"
        children: dict[str, StoredFile | Folder] = {}
        for path, f in self.files.items():
            if path.startswith(prefix):
                name, _, rest = path[len(prefix) :].partition("/")
                child = prefix + name
                children[child] = Folder(child) if rest else f
        return [children[p] for p in sorted(children)]

    def move(self, path: str, new_path: str) -> StoredFile:
        """Move a file to new_path. Folders can't be moved."""
        if path not in self.files and self._is_folder(path):
            msg = "can't move a folder"
            raise invalid_operation(msg)
        f = self.get(path)
        if new_path.lower() == path.lower():
            msg = "new_path is the same as path (ignoring case)"
            raise invalid_operation(msg)
        if self._exists(new_path):
            raise conflict(new_path)
        self._check_parents(new_path)
        del self.files[path]
        self.files[new_path] = replace(f, path=new_path)
        return self.files[new_path]

    def delete(self, path: str) -> None:
        """Delete a file, or a folder and everything in it."""
        if path in self.files:
            del self.files[path]
            return
        inside = [p for p in self.files if p.startswith(path + "/")]
        if not inside:
            raise not_found(path)
        for p in inside:
            del self.files[p]

    def _save(self, path: str, data: bytes, file_id: str) -> StoredFile:
        self.files[path] = StoredFile(path, file_id, data, datetime.now(UTC))
        return self.files[path]

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
                raise invalid_operation(msg)

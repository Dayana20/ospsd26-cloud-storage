"""Tests for streaming download helpers."""

from io import BytesIO

import pytest

from cloud_storage_api import DocumentStorage, FileInfo, NotFoundError

CONTENT = b"abcdef"


class MemoryStorage(DocumentStorage):
    """Minimal bytes-only storage that relies on the default stream methods."""

    def __init__(self) -> None:
        """Start empty."""
        self.files: dict[str, bytes] = {}

    def _info(self, path: str) -> FileInfo:
        """Build file info for a stored path."""
        return FileInfo(
            id=None,
            name=path.rsplit("/", 1)[-1],
            path=path,
            size=len(self.files[path]),
            modified_at=None,
            etag=None,
            type=None,
        )

    def create(self, path: str, content: bytes) -> FileInfo:
        """Store bytes."""
        self.files[path] = content
        return self._info(path)

    def replace(self, path: str, content: bytes) -> FileInfo:
        """Store bytes."""
        self.files[path] = content
        return self._info(path)

    def download(self, path: str) -> bytes:
        """Return stored bytes or raise NotFoundError."""
        if path not in self.files:
            msg = "No file exists at that path."
            raise NotFoundError(msg)
        return self.files[path]

    def get_metadata(self, path: str) -> FileInfo:
        """Return file info."""
        if path not in self.files:
            msg = "No file exists at that path."
            raise NotFoundError(msg)
        return self._info(path)

    def list_files(self, path: str) -> list[FileInfo]:
        """Return every stored file."""
        return [self._info(p) for p in sorted(self.files)]

    def move(self, from_path: str, to_path: str) -> FileInfo:
        """Move bytes between paths."""
        self.files[to_path] = self.files.pop(from_path)
        return self._info(to_path)

    def delete(self, path: str) -> None:
        """Remove a path."""
        del self.files[path]

    def check_health(self) -> None:
        """Report storage as healthy."""


def test_open_download_default_yields_chunks() -> None:
    """The default open_download splits the bytes into chunks."""
    storage = MemoryStorage()
    storage.files["/a.txt"] = CONTENT
    with storage.open_download("/a.txt") as download:
        assert list(download.chunks(4)) == [b"abcd", b"ef"]


def test_open_download_info_is_available_before_reading() -> None:
    """The size is known before any chunk is read."""
    storage = MemoryStorage()
    storage.files["/a.txt"] = CONTENT
    with storage.open_download("/a.txt") as download:
        assert download.info.size == len(CONTENT)
        assert download.info.path == "/a.txt"


def test_open_download_raises_before_the_first_chunk() -> None:
    """Errors surface when open_download is called, not on iteration."""
    storage = MemoryStorage()
    with pytest.raises(NotFoundError):
        storage.open_download("/missing.txt")


def test_close_is_idempotent_and_safe_before_reading() -> None:
    """Close works with no chunk read and can be called repeatedly."""
    storage = MemoryStorage()
    storage.files["/a.txt"] = b"abc"
    download = storage.open_download("/a.txt")
    download.close()
    download.close()


def test_reading_a_closed_download_raises() -> None:
    """Reading after close is an error, not a silent empty read."""
    storage = MemoryStorage()
    storage.files["/a.txt"] = b"abc"
    with storage.open_download("/a.txt") as download:
        pass
    with pytest.raises(ValueError, match="closed"):
        list(download.chunks())


@pytest.mark.parametrize("size", [0, -1])
def test_chunks_reject_non_positive_sizes(size: int) -> None:
    """Reject chunk sizes that cannot make progress."""
    storage = MemoryStorage()
    storage.files["/a.txt"] = CONTENT

    with (
        storage.open_download("/a.txt") as download,
        pytest.raises(ValueError, match="Chunk size must be positive"),
    ):
        list(download.chunks(size))


def test_create_stream_default_reads_from_current_position_without_closing() -> None:
    """Read from the current stream position and leave the stream open."""
    storage = MemoryStorage()
    stream = BytesIO(CONTENT)
    stream.seek(2)

    storage.create_stream("/a.txt", stream)

    assert storage.files["/a.txt"] == CONTENT[2:]
    assert not stream.closed

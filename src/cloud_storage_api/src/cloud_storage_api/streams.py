"""Streaming helpers for the shared Document Storage interface."""

from abc import ABC, abstractmethod
from collections.abc import Iterator
from types import TracebackType
from typing import Self

from .models import FileInfo

# 64 KiB (kilobytes in binary measurement)
# Small enough to process files incrementally without requiring large buffers
DEFAULT_CHUNK_SIZE = 65536


class DownloadStream(ABC):
    """An open, lazy download. Always close it, preferably with a ``with`` block.

    ``info`` is known as soon as the stream is returned, so an HTTP layer can set
    Content-Length before sending the body. Errors that can be detected when opening
    are raised by ``open_download`` itself. Read failures can still be raised while
    iterating ``chunks``; once response headers are sent, the caller must log the
    failure and cut the body off rather than send a JSON error.
    """

    @property
    @abstractmethod
    def info(self) -> FileInfo:
        """Return the file's info, available before the first chunk is read."""

    @abstractmethod
    def chunks(self, size: int = DEFAULT_CHUNK_SIZE) -> Iterator[bytes]:
        """Yield the file's bytes in chunks of at most ``size`` bytes."""

    @abstractmethod
    def close(self) -> None:
        """Release provider resources. Idempotent, and safe before any chunk is read."""

    def __enter__(self) -> Self:
        """Return the stream for use in a ``with`` block."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Close the stream when the ``with`` block ends."""
        self.close()


class BytesDownload(DownloadStream):
    """A DownloadStream over bytes that are already in memory."""

    def __init__(self, info: FileInfo, data: bytes) -> None:
        """Wrap file info and bytes that were already downloaded."""
        self._info = info
        self._data = data
        self._closed = False

    @property
    def info(self) -> FileInfo:
        """Return the file's info."""
        return self._info

    def chunks(self, size: int = DEFAULT_CHUNK_SIZE) -> Iterator[bytes]:
        """Yield the bytes in chunks. Raise ValueError if the stream is closed."""
        for start in range(0, len(self._data), size):
            if self._closed:
                msg = "The download is closed."
                raise ValueError(msg)
            yield self._data[start : start + size]
        if self._closed:
            msg = "The download is closed."
            raise ValueError(msg)

    def close(self) -> None:
        """Drop the in-memory bytes. Safe to call more than once."""
        self._closed = True
        self._data = b""

"""Provider interface that every storage adapter implements."""

from abc import ABC, abstractmethod
from typing import BinaryIO

from .models import FileInfo
from .streams import BytesDownload, DownloadStream


class DocumentStorage(ABC):
    """Operations of the shared Document Storage contract."""

    @abstractmethod
    def create(self, path: str, content: bytes) -> FileInfo:
        """Create a file. Raise ConflictError if one already exists."""

    @abstractmethod
    def replace(self, path: str, content: bytes) -> FileInfo:
        """Replace a file. Raise NotFoundError if missing; never create."""

    @abstractmethod
    def download(self, path: str) -> bytes:
        """Return the exact bytes of a file."""

    def open_download(self, path: str) -> DownloadStream:
        """Open a lazy download.

        The lookup is eager: errors such as NotFoundError are raised here, before the
        first chunk, and ``info`` is available on the result. The caller must close the
        result, preferably with a ``with`` block. The default makes two provider calls
        (metadata, then download); adapters that can stream should override it.
        """
        info = self.get_metadata(path)
        return BytesDownload(info, self.download(path))

    def create_stream(self, path: str, stream: BinaryIO) -> FileInfo:
        """Create a file from a readable binary stream.

        The caller owns ``stream`` and the adapter never closes it. The default
        reads the whole stream; adapters that can stream should override it.
        """
        return self.create(path, stream.read())

    def replace_stream(self, path: str, stream: BinaryIO) -> FileInfo:
        """Replace a file from a readable binary stream. Same ownership rules as create_stream."""
        return self.replace(path, stream.read())

    @abstractmethod
    def get_metadata(self, path: str) -> FileInfo:
        """Return file info. Raise NotFoundError if missing."""

    @abstractmethod
    def list_files(self, path: str) -> list[FileInfo]:
        """Return the direct children of a folder, sorted by path, every page fetched."""

    @abstractmethod
    def move(self, from_path: str, to_path: str) -> FileInfo:
        """Move a file. Raise ConflictError if the destination exists."""

    @abstractmethod
    def delete(self, path: str) -> None:
        """Delete a file, or a folder with everything in it."""

    @abstractmethod
    def check_health(self) -> None:
        """Make one lightweight provider call. Raise ProviderUnavailableError on failure."""

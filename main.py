"""Demonstrate the document storage API."""

from cloud_storage_api import DocumentStorage


def main(storage: DocumentStorage) -> None:
    """List documents, inspect and download one, and optionally delete it."""
    storage.check_health()
    files = [item for item in storage.list_files("/") if item.type == "file"]

    if not files:
        return

    file_info = storage.get_metadata(files[0].path)
    content = storage.download(file_info.path)
    print(f"{file_info.name}: {file_info.size} bytes")  # noqa: T201
    print(f"Downloaded {len(content)} bytes.")  # noqa: T201

    try:
        confirmation = input(f"Type 'DELETE' to delete {file_info.path}: ")
    except EOFError:
        return

    if confirmation == "DELETE":
        storage.delete(file_info.path)
        print(f"Deleted {file_info.path}.")  # noqa: T201

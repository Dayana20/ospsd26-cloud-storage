# Cloud Storage Contract Component

`cloud_storage_api` is the provider-independent contract for document-storage
adapters. It defines the expected operations and shared data/error types;
provider-specific behavior belongs in a separate implementation package.

## Package layout

```text
src/cloud_storage_api/
├── pyproject.toml
├── README.md
├── src/cloud_storage_api/
│   ├── __init__.py
│   ├── errors.py
│   ├── interface.py
│   ├── models.py
│   └── py.typed
└── tests/
```

## Public API

- `DocumentStorage`: abstract operations for creating, replacing, downloading,
  inspecting, listing, moving, and deleting files, plus a health check.
- `FileInfo`: provider-neutral file or folder metadata.
- `StorageError` and its subclasses: shared error types with status and code
  attributes.

The package exports its public types from `cloud_storage_api`. It does not
provide a factory or concrete provider implementation; applications receive a
provider adapter through dependency injection.

## Provider adapters

An adapter should implement all abstract methods, follow the behavioral
contracts documented on `DocumentStorage`, return `FileInfo` values, and map
provider failures to the shared storage errors. Provider credentials and
provider-specific configuration belong to the adapter, not this contract.

## Testing

Contract tests live in `src/cloud_storage_api/tests/` and run without
credentials. Provider packages should test their adapter separately, including
integration tests with provider credentials kept in a CI secret context.

# Cloud Storage API

This project defines a provider-independent contract for document storage.
The API includes the `DocumentStorage` interface, the `FileInfo` metadata
model, and a shared set of storage errors. Provider implementations can use
this contract to offer consistent file operations across storage services.

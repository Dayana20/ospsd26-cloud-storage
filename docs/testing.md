# Testing

# Testing

The `cloud_storage_api` tests verify the shared contract and its error types.
They do not connect to a cloud provider and require no credentials.

Run the contract tests and quality checks from the repository root:

```bash
uv run pytest src/cloud_storage_api/tests -q
uv run ruff check .
uv run mypy .
```

## Provider integration tests

Provider adapters should test their implementations separately from the shared
contract. Mark tests requiring a real provider with `integration`; the
CircleCI integration job uses the `cloud-storage` context. Keep provider
credentials out of source control and configure the required environment
variables in that context.

The shared contract package does not currently include provider integration
tests. CircleCI skips the integration-test step until such tests are added.

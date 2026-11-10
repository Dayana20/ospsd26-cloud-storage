# Conformance tests

Tests that every storage service (Team 1, Team 3, Team 6) should pass. They only use
the HTTP API, so the same tests work against any of the services.

`reference/` serves any `cloud_storage_api.DocumentStorage` over HTTP. By default it
uses `MemoryStorage`, an in-memory implementation, so CI doesn't need any credentials.
If a test fails against the reference app, the test is wrong.

The reference app can also serve your own adapter, e.g. `build_app(MyStorage())`.

## Running

```bash
uv sync --all-packages --extra dev

# against the reference app
uv run pytest conformance/tests --no-cov

# against your own service
CONFORMANCE_BASE_URL=http://127.0.0.1:8000 uv run pytest conformance/tests --no-cov

# skip rules that aren't agreed yet
uv run pytest conformance/tests --no-cov -m "not proposed"
```

Each test uses its own `/conformance-<random>` folder and deletes it at the end. Still,
point it at a test bucket or app folder, not one with real data.

## Not agreed yet

Tests marked `@pytest.mark.proposed` check rules that are still being discussed:

- `/files/download?path=` and `/files/metadata?path=` routes (#8)
- `GET /files?path=` list route (#10)
- move (#5)
- `route_not_found` and `method_not_allowed` (#4)

Error codes, `FileInfo` fields (including `etag` and `type`) and UTC timestamps follow
`cloud_storage_api` 0.2.0, so those tests aren't marked.

When a rule is agreed, remove the marker. If it changes, update the test and the
reference app.

## Not tested

- Upload size limit (not decided, and big uploads are slow)
- Provider errors (403, 502, 503), since we can't make a real provider fail on demand
- Empty folders (S3 doesn't have them)
- Lists longer than one provider page (too slow against a real service)
- Upper/lower case paths (Dropbox and S3 behave differently)

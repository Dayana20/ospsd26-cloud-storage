# Conformance tests

Tests that every storage service (Team 1, Team 3, Team 6) should pass. They only use
the HTTP API, so the same tests work against any of the services.

`reference/` is a small in-memory version of the API. By default the tests run against
it, so CI doesn't need any credentials. If a test fails against the reference app, the
test is wrong.

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

- 409 when creating a file that exists (#4)
- `/files/download?path=` and `/files/metadata?path=` routes
- `modified_at` in UTC ending in `Z`
- list response and the `type` field for folders (#3)
- move (#5)
- `route_not_found` and `method_not_allowed` (#4)

When a rule is agreed, remove the marker. If it changes, update the test and the
reference app.

## Not tested

- Upload size limit (not decided, and big uploads are slow)
- Provider errors (403, 502, 503), since we can't make a real provider fail on demand
- Empty folders (S3 doesn't have them)
- Lists longer than one provider page (too slow against a real service)
- Upper/lower case paths (Dropbox and S3 behave differently)

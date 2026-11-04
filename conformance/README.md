# Conformance suite

One set of tests that every Document Storage service must pass: Team 1 and Team 3
(Dropbox) and Team 6 (S3-compatible). Passing the same tests is how the three teams show
that a consumer can switch services by changing only the base URL and the credentials.
The Oct 28 memo for the Document Storage vertical assigns this suite and its reference
service to Team 6.

It lives outside the `src/` packages because the shared Python package does not have a
layout yet. It imports nothing from any team's service.

## What is here

| Path | What it is |
|---|---|
| `reference/` | A small service that follows the contract and keeps files in memory. It is the answer key: a test that fails against it is a wrong test. |
| `tests/` | The tests, one file per operation, and `test_workflow.py`, the consumer workflow from the memo. |

## Running it

```bash
uv sync --all-packages --extra dev

# Against the reference service, in this process (no network, no credentials).
# CI runs this on every pull request. --no-cov skips the coverage gate, which
# measures src/ only.
uv run pytest conformance/tests --no-cov

# Against a running service, before a release
CONFORMANCE_BASE_URL=http://127.0.0.1:8000 uv run pytest conformance/tests --no-cov

# Only the rules that are already agreed
CONFORMANCE_BASE_URL=http://127.0.0.1:8000 uv run pytest conformance/tests --no-cov -m "not proposed"

# The reference service as a real server
uv run --with uvicorn uvicorn conformance.reference.app:app --port 8100
```

Each test works in its own folder, `/conformance-<random>/`, and deletes it afterwards, so a
run against a real service leaves nothing behind. Run against a test bucket or app folder,
not one with real data.

## The contract as tested

| Operation | Request | Success | Errors tested | Source |
|---|---|---|---|---|
| Health | `GET /health`, `GET /health/provider` | 200 `{"status": "ok"}` | | memo, Health |
| Create | `POST /files`, form fields `file` and `path` | 201, file info | 400, 409 | memo, Create |
| Replace | `PUT /files`, same fields | 200, file info | 404 (nothing created) | memo, Replace |
| Download | `GET /files/download?path=` | 200, exact bytes | 404 | memo, Download; route: open question 2 |
| Metadata | `GET /files/metadata?path=` | 200, file info | 404 | memo, Metadata; route: open question 2 |
| List | `GET /files?path=<folder>` | 200, array of direct children sorted by path, with `type` | 400, 404 | #3 |
| Move | `PATCH /files?path=` with `{"new_path"}` | 200, file info at the new path | 400, 404, 409, 422 | #5 |
| Delete | `DELETE /files?path=` | 204, no body; a folder goes with everything in it | 404 | memo, Delete |

* **File info:** `id` (string, or null on S3), `name`, `path`, `size`, `modified_at` (ISO 8601
  with a timezone). Extra fields, such as `etag`, are allowed.
* **Paths:** accepted with or without a leading `/`, always returned with one. Empty paths,
  empty segments, `.`, `..`, and a trailing `/` are 400 `invalid_request`.
* **Errors:** every error is `{"error": {"code": "...", "message": "..."}}`. The tests check
  the status and the code, never the message.

## Rules that are not agreed yet

Tests for these rules follow the current proposal and are marked
`@pytest.mark.proposed(<source>)`. Deselect them with `-m "not proposed"`. When a rule is
agreed, remove its marker. When it changes, change the test and the reference service.

| Rule | Proposal tested | Source |
|---|---|---|
| Existing destination on Create | 409 `conflict` | #4, memo open question 3 |
| Download and metadata routes | `/files/download?path=`, `/files/metadata?path=` (Teams 1 and 3 today) | memo open question 2 |
| Timestamps | `modified_at` in UTC, ending in `Z` | memo, The data model |
| List | Shape, one level, sorting, `type` field for files and folders | #3, memo open question 4 |
| Move | Every Move rule, including 422 for the same path, a case-only rename, and a folder source | #5 |
| Unknown route, wrong method | 404 `route_not_found`, 405 `method_not_allowed` with `Allow` | #4 |

## Not tested yet

* **Upload size limit:** not agreed (memo open question 9), and a 150 MiB upload is slow
  against a real service.
* **Provider failures** (403, 502, 503): a shared test cannot make a real provider fail on
  demand. Each team tests these in its own repository.
* **An empty folder:** S3 has no empty folders, so the suite cannot create one on every
  service.
* **Metadata, Replace, or Download on a folder path, and List on a file path:** the contract
  does not say what happens. The reference service returns 422 `invalid_operation`.
* **Lists longer than one provider page** (1000 keys on S3): too slow against a real service.
* **Letter case:** Dropbox treats `/A.txt` and `/a.txt` as one file and S3 as two. The
  contract tells consumers not to rely on either, so the suite does not test it.

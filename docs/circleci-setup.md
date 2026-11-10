# CircleCI Setup

The CircleCI pipeline builds the project, runs Ruff, type-checks the source,
and runs the cloud storage contract tests. These contract checks do not need
provider credentials. The provider integration job uses a CircleCI context
named `cloud-storage`; it skips until integration tests are added.

## Connect the Repository

1. Log in to [CircleCI](https://circleci.com/).
2. Add this repository under **Projects**.
3. CircleCI detects the pipeline configuration in `.circleci/config.yml`.

## Provider Credentials

Create a CircleCI **Context** named `cloud-storage` and add the credentials
required by the selected storage provider. The environment variable names
depend on the provider implementation and should be documented alongside
that adapter. Do not add credentials to this shared contract package.

The `integration_test` job runs on `main` and `develop`. Until tests marked
`integration` exist, the job reports that there are no provider integration
tests and exits successfully.

## Workflows

The pipeline runs build, lint, unit-test, credential-free test, and report
jobs on regular branches. On `main`/`develop`, it additionally runs provider
integration tests using the `cloud-storage` context.

## Run Checks Locally

From the repository root:

```bash
uv sync --all-packages --extra dev
uv run ruff check .
uv run mypy .
uv run pytest src/ --cov=src --cov-fail-under=85
```

No secrets or environment variables are needed for the contract tests.

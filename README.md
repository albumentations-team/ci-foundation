# Albumentations CI Foundation

Shared, security-hardened GitHub Actions for AlbumentationsX, Albucore, and albumentations.ai.

The repository owns three mechanisms: Python and uv bootstrap, CPU-only PyTorch automation, and trusted-base
Antigravity review orchestration. Consumer repositories keep their dependency graphs, job permissions, test commands,
release policy, legal checks, and deployment logic. [The architecture](docs/architecture.md) defines that boundary.

## Use a pinned action

Consumers must reference a full commit SHA. Release tags name the SHA for humans; they are not execution references.

```yaml
- uses: albumentations-team/ci-foundation/actions/setup-python-uv@<full-commit-sha>
  with:
    python-version: "3.13"
    cache-dependency-glob: |
      pyproject.toml
      uv.lock
    cache-suffix: ci-test-torch-cpu
```

`setup-python-uv` installs Python and uv only. The caller selects and installs its own dependency graph.
Set `cache-enabled: "false"` only for a job whose cache policy intentionally prohibits restore and save.

```yaml
- uses: albumentations-team/ci-foundation/actions/torch-cpu@<full-commit-sha>
  with:
    mode: verify
    python: python
```

`torch-cpu` never chooses a user runtime. `verify` checks a Torch installation that the caller already selected. `install` installs an explicit Torch requirement from the PyTorch CPU index, then runs the same verification.

## Use the trusted Antigravity workflow

The caller owns the trigger and repository policy. It must call this workflow from `pull_request_target`, allow only
same-repository, non-draft pull requests, and grant no permissions beyond the workflow's needs. The reusable workflow
checks out the trusted base SHA, reads untrusted PR metadata and diffs as data, then publishes its review from a
separate job.

```yaml
jobs:
  antigravity:
    uses: albumentations-team/ci-foundation/.github/workflows/antigravity-review.yml@<full-commit-sha>
    with:
      policy-path: .github/ci-foundation/antigravity.toml
      gcp-location: ${{ vars.ANTIGRAVITY_GCP_LOCATION }}
      gcp-project-id: ${{ vars.ANTIGRAVITY_GCP_PROJECT_ID }}
      gcp-service-account: ${{ vars.ANTIGRAVITY_GCP_SERVICE_ACCOUNT }}
      gcp-workload-identity-provider: ${{ vars.ANTIGRAVITY_GCP_WIF_PROVIDER }}
```

The policy is a trusted-base TOML file. It contains `paths.include`, optional `paths.exclude`, and the relative path
of model instructions. The action rejects absolute and parent-directory paths. See
[the workflow contract](docs/antigravity.md) before adding a caller.

## Development

```bash
uv sync --group dev
uv run pytest
uv run ruff check .
uv run ruff format --check .
uvx zizmor .github
```

## License

The repository is public so all consumers can call its reusable workflows. Its source license will be added as a
separate, explicit maintainer decision before the first release tag.

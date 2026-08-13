# Albumentations CI Foundation

Shared, security-hardened GitHub Actions for AlbumentationsX, Albucore, and albumentations.ai.

The repository owns three mechanisms: Python and uv bootstrap, CPU-only PyTorch automation, and trusted-base Antigravity review orchestration. Consumer repositories keep their dependency graphs, job permissions, test commands, release policy, legal checks, and deployment logic.

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

```yaml
- uses: albumentations-team/ci-foundation/actions/torch-cpu@<full-commit-sha>
  with:
    mode: verify
    python: python
```

`torch-cpu` never chooses a user runtime. `verify` checks a Torch installation that the caller already selected. `install` installs an explicit Torch requirement from the PyTorch CPU index, then runs the same verification.

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

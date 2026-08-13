# CI Foundation architecture

`ci-foundation` is a small public repository of reusable GitHub Actions. Public visibility is required because
AlbumentationsX and Albucore are public callers. Consumers execute pinned commit SHAs, never floating tags.

## Ownership boundary

| Foundation owns | Consumer owns |
| --- | --- |
| Python and uv bootstrap | Python versions and dependency graphs |
| Explicit CPU-only Torch install and verification | Whether Torch is needed and its version constraint |
| Trusted Antigravity policy parsing, review artifact validation, and review orchestration | PR trigger, project path policy, model instructions, and cloud variables |
| Foundation unit tests, actionlint, and Zizmor | Tests, build, release, license, legal, deployment, and product checks |

Actions must not install a consumer dependency graph or choose an accelerator runtime. A caller declares its own
dependencies and asks `torch-cpu` to verify the selected environment, or explicitly requests a CPU-only Torch install.

## Versioning and upgrades

1. Change the foundation on its own branch and prove its tests, Ruff, actionlint, and Zizmor checks.
2. Merge to `main`, run the foundation CI, then tag the validated commit as `v1.x.y`.
3. Upgrade one consumer at a time by replacing its full action SHA and running that consumer's complete CI.
4. Publish an immutable release note with the tag, commit SHA, changed contracts, and upgrade instructions.

Tags are human-readable release labels. Callers pin complete commit SHAs so they do not execute new code until they
deliberately change their workflow.

## Security model

The Antigravity reusable workflow accepts only `pull_request_target` context from a same-repository, non-draft pull
request. It checks out `github.event.pull_request.base.sha`; it never checks out or executes the PR head. PR metadata,
changed paths, and diffs are untrusted data. Gemini receives only read-only file tools and cannot invoke shell or GitHub
commands. The publication job has `pull-requests: write`; the analysis job only has read permissions plus an OIDC token
for Vertex AI.

The caller still owns its workflow trigger and permissions. The reusable workflow is defence in depth, not a reason to
weaken a caller's trigger or grant broad permissions.

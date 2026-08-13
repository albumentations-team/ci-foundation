# Antigravity workflow contract

The reusable workflow is an analysis and publication mechanism. A consumer configures project-specific scope with a
data-only policy in the trusted base revision:

```toml
[paths]
include = ["src/**", "tests/**"]
exclude = ["src/generated/**"]

[review]
instructions = ".github/ci-foundation/antigravity-review.md"
```

`include` is a non-empty list of path patterns. `exclude` is optional. `instructions` must name an existing file under
the trusted base checkout; absolute paths and paths containing `..` fail validation.

The caller must use `pull_request_target`, restrict the job to non-draft PRs whose head repository equals the current
repository, and configure its Vertex AI variables. Do not call the workflow on fork PRs. The foundation enforces the
same conditions as a second boundary.

Model instructions are trusted-base content. They must tell the reviewer which checks and contracts matter for the
consumer project; they must not contain credentials or request file modification. Pull-request title, body, paths, and
diff remain untrusted review data even when they appear in `.antigravity`.

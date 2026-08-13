"""Validate a trusted Antigravity policy and select matching changed files."""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Iterable
from pathlib import Path, PurePosixPath
from typing import Any

import tomllib


def _relative_workspace_path(workspace: Path, value: str, *, label: str) -> Path:
    candidate = PurePosixPath(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        msg = f"{label} must be a relative path within the checked-out trusted base."
        raise ValueError(msg)
    resolved = (workspace / Path(candidate)).resolve()
    if not resolved.is_relative_to(workspace):
        msg = f"{label} escapes the checked-out trusted base."
        raise ValueError(msg)
    return resolved


def _string_list(value: object, *, label: str) -> list[str]:
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
        msg = f"{label} must be a non-empty list of non-empty strings."
        raise ValueError(msg)
    return value


def load_policy(policy_path: Path, *, workspace: Path) -> tuple[list[str], list[str], Path]:
    """Load a data-only path policy from the trusted base checkout."""
    try:
        policy = tomllib.loads(policy_path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        raise ValueError(f"policy is not valid TOML: {error}") from error

    paths = policy.get("paths")
    review = policy.get("review")
    if not isinstance(paths, dict) or not isinstance(review, dict):
        raise ValueError("policy must define [paths] and [review] tables.")
    include = _string_list(paths.get("include"), label="paths.include")
    exclude_value = paths.get("exclude", [])
    if not isinstance(exclude_value, list) or not all(isinstance(item, str) and item for item in exclude_value):
        raise ValueError("paths.exclude must be a list of non-empty strings.")
    instructions = review.get("instructions")
    if not isinstance(instructions, str) or not instructions:
        raise ValueError("review.instructions must be a non-empty path string.")
    instructions_path = _relative_workspace_path(workspace, instructions, label="review.instructions")
    if not instructions_path.is_file():
        raise ValueError(f"review.instructions does not exist: {instructions}")
    return include, exclude_value, instructions_path


def _iter_changed_paths(payload: object) -> Iterable[str]:
    pages = payload if isinstance(payload, list) else [payload]
    for page in pages:
        if not isinstance(page, list):
            raise ValueError("GitHub changed-file payload must contain lists of file records.")
        for record in page:
            if not isinstance(record, dict) or not isinstance(filename := record.get("filename"), str):
                raise ValueError("GitHub changed-file payload contains a record without a filename.")
            yield filename


def _matches(path: str, patterns: Iterable[str]) -> bool:
    pure_path = PurePosixPath(path)
    return any(pure_path.match(pattern) for pattern in patterns)


def selected_paths(changed_paths: Iterable[str], *, include: list[str], exclude: list[str]) -> list[str]:
    """Return changed paths selected by include patterns and rejected by exclude patterns."""
    return sorted(path for path in changed_paths if _matches(path, include) and not _matches(path, exclude))


def write_github_output(path: Path, values: dict[str, str]) -> None:
    """Append simple scalar outputs to GitHub's output file."""
    with path.open("a", encoding="utf-8") as output:
        for key, value in values.items():
            output.write(f"{key}={value}\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--changed-files", type=Path, required=True)
    parser.add_argument("--github-output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    workspace = Path.cwd().resolve()
    policy_path = _relative_workspace_path(workspace, args.policy.as_posix(), label="policy")
    include, exclude, instructions_path = load_policy(policy_path, workspace=workspace)
    changed_payload: Any = json.loads(args.changed_files.read_text(encoding="utf-8"))
    selected = selected_paths(_iter_changed_paths(changed_payload), include=include, exclude=exclude)
    instructions_relative = instructions_path.relative_to(workspace).as_posix()
    write_github_output(
        args.github_output,
        {
            "instructions-path": instructions_relative,
            "selected": str(bool(selected)).lower(),
            "selected-paths-json": json.dumps(selected),
        },
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=os.sys.stderr)
        raise SystemExit(1) from error

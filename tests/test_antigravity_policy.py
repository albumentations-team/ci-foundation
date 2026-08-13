from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ACTION_DIRECTORY = Path(__file__).parents[1] / "actions" / "antigravity-policy"
sys.path.insert(0, str(ACTION_DIRECTORY))

import prepare_policy  # noqa: E402


def _write_policy(workspace: Path, content: str) -> Path:
    policy_path = workspace / ".github" / "ci-foundation" / "antigravity.toml"
    policy_path.parent.mkdir(parents=True)
    policy_path.write_text(content, encoding="utf-8")
    return policy_path


def test_load_policy_uses_only_trusted_workspace_paths(tmp_path: Path) -> None:
    instructions = tmp_path / ".github" / "antigravity-review.md"
    instructions.parent.mkdir(parents=True)
    instructions.write_text("review rules", encoding="utf-8")
    policy_path = _write_policy(
        tmp_path,
        """[paths]
include = ["src/**"]
exclude = ["src/generated/**"]

[review]
instructions = ".github/antigravity-review.md"
""",
    )

    include, exclude, loaded_instructions = prepare_policy.load_policy(policy_path, workspace=tmp_path)

    assert include == ["src/**"]
    assert exclude == ["src/generated/**"]
    assert loaded_instructions == instructions


@pytest.mark.parametrize("instructions", ["../outside.md", "/etc/passwd"])
def test_load_policy_rejects_instruction_paths_outside_workspace(tmp_path: Path, instructions: str) -> None:
    policy_path = _write_policy(
        tmp_path,
        f"""[paths]
include = ["**"]

[review]
instructions = "{instructions}"
""",
    )

    with pytest.raises(ValueError, match="relative path within the checked-out trusted base"):
        prepare_policy.load_policy(policy_path, workspace=tmp_path)


def test_selected_paths_respects_include_and_exclude_patterns() -> None:
    paths = prepare_policy.selected_paths(
        ["src/core.py", "src/generated/catalog.py", "README.md"],
        include=["src/**"],
        exclude=["src/generated/**"],
    )

    assert paths == ["src/core.py"]


def test_iter_changed_paths_accepts_paginated_gh_api_payload() -> None:
    payload = [[{"filename": "src/a.py"}], [{"filename": "src/b.py"}]]

    assert list(prepare_policy._iter_changed_paths(payload)) == ["src/a.py", "src/b.py"]


def test_write_github_output_emits_scalar_outputs(tmp_path: Path) -> None:
    output_path = tmp_path / "github-output"

    prepare_policy.write_github_output(
        output_path,
        {"selected": "true", "selected-paths-json": json.dumps(["src/a.py"])},
    )

    assert output_path.read_text(encoding="utf-8") == 'selected=true\nselected-paths-json=["src/a.py"]\n'

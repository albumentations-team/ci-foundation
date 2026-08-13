from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

REPOSITORY_ROOT = Path(__file__).parents[1]
SETUP_ACTION = REPOSITORY_ROOT / "actions" / "setup-python-uv" / "action.yml"
TORCH_ACTION = REPOSITORY_ROOT / "actions" / "torch-cpu" / "action.yml"
ANTIGRAVITY_ACTION = REPOSITORY_ROOT / "actions" / "antigravity-policy" / "action.yml"
FULL_SHA = re.compile(r"@[0-9a-f]{40}(?:\s|$)")


def _load_yaml(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def test_setup_action_has_no_dependency_install_step() -> None:
    action = _load_yaml(SETUP_ACTION)
    action_text = SETUP_ACTION.read_text(encoding="utf-8")

    assert action["inputs"]["uv-version"]["required"] is True
    assert action["inputs"]["cache-dependency-glob"]["required"] is True
    assert action["inputs"]["cache-suffix"]["required"] is True
    assert action["inputs"]["cache-enabled"]["default"] == "true"
    assert "uv sync" not in action_text
    assert "uv pip install" not in action_text
    assert "pip install" not in action_text
    assert "version: ${{ inputs.uv-version }}" in action_text


def test_torch_action_exposes_install_and_verify_without_accelerator_fallback() -> None:
    action = _load_yaml(TORCH_ACTION)
    action_text = TORCH_ACTION.read_text(encoding="utf-8")

    assert set(action["inputs"]) == {"mode", "python", "requirement", "output-json"}
    assert "Unknown Torch CPU action mode" in action_text
    assert "--index-url" not in action_text
    assert "--torch-backend" not in action_text
    assert "--extra-index-url" not in action_text


def test_antigravity_action_has_explicit_select_and_prepare_operations() -> None:
    action = _load_yaml(ANTIGRAVITY_ACTION)
    action_text = ANTIGRAVITY_ACTION.read_text(encoding="utf-8")

    assert action["inputs"]["operation"]["default"] == "select"
    assert "prepare-review" in action_text
    assert "Unknown Antigravity action operation" in action_text


def test_all_third_party_action_references_are_full_sha_pins() -> None:
    for action_path in (SETUP_ACTION, TORCH_ACTION, ANTIGRAVITY_ACTION):
        for line in action_path.read_text(encoding="utf-8").splitlines():
            if "uses:" in line and "./" not in line:
                reference = line.split("uses:", maxsplit=1)[1].strip().split(" #", maxsplit=1)[0]
                assert FULL_SHA.search(reference), f"{action_path}: {reference} is not a full SHA pin"

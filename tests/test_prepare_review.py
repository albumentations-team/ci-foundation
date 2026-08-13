from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ACTION_DIRECTORY = Path(__file__).parents[1] / "actions" / "antigravity-policy"
sys.path.insert(0, str(ACTION_DIRECTORY))

import prepare_review  # noqa: E402


def test_prepare_review_writes_only_a_valid_markdown_response(tmp_path: Path) -> None:
    source = tmp_path / "stdout.log"
    source.write_text(json.dumps({"response": "## Antigravity Review\n\nNo findings."}), encoding="utf-8")
    output = tmp_path / "review.md"

    prepare_review.prepare_review(source, output)

    assert output.read_text(encoding="utf-8") == "## Antigravity Review\n\nNo findings.\n"


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({"error": {"type": "AUTH"}}, "error instead of a complete review"),
        ({"response": ""}, "EMPTY_RESPONSE"),
        ({"response": "No heading"}, "required Antigravity Review heading"),
    ],
)
def test_prepare_review_rejects_non_publishable_responses(
    tmp_path: Path,
    payload: dict[str, object],
    message: str,
) -> None:
    source = tmp_path / "stdout.log"
    source.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(prepare_review.ReviewError, match=message):
        prepare_review.prepare_review(source, tmp_path / "review.md")

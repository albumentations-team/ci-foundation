"""Install a validated Torch requirement from the canonical PyTorch CPU index."""

from __future__ import annotations

import argparse
import re
import shlex
import subprocess
from pathlib import Path

PYTORCH_CPU_INDEX = "https://download.pytorch.org/whl/cpu"
TORCH_REQUIREMENT_PATTERN = re.compile(
    r"^torch(?:(?:===|==|!=|<=|>=|<|>|~=)[A-Za-z0-9.*+!_-]+(?:,(?:===|==|!=|<=|>=|<|>|~=)[A-Za-z0-9.*+!_-]+)*)?$",
    flags=re.IGNORECASE,
)


def validate_requirement(requirement: str) -> str:
    """Accept only a direct Torch requirement with optional version constraints."""
    normalized = requirement.strip()
    if not TORCH_REQUIREMENT_PATTERN.fullmatch(normalized):
        msg = "requirement must be a direct Torch requirement, for example 'torch>=2.13.0'."
        raise ValueError(msg)
    return normalized


def install_cpu_torch(*, python: Path, requirement: str) -> None:
    """Install CPU-only Torch for one interpreter without resolving from the default index."""
    command = [
        "uv",
        "pip",
        "install",
        "--python",
        str(python),
        requirement,
        "--index-url",
        PYTORCH_CPU_INDEX,
    ]
    print("+", shlex.join(command))
    subprocess.run(command, check=True)  # noqa: S603 - command arguments are fixed or validated.


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--requirement", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    install_cpu_torch(python=args.python, requirement=validate_requirement(args.requirement))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

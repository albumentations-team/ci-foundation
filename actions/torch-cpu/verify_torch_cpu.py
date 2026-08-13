"""Verify that an interpreter contains a CPU-only Torch runtime without probing devices."""

from __future__ import annotations

import argparse
import importlib.metadata
import importlib.util
import json
import sys
from collections.abc import Callable, Iterable
from pathlib import Path
from types import ModuleType
from typing import Any

ACCELERATOR_DISTRIBUTION_PREFIXES = ("cuda", "nvidia-")


def _normalize_distribution_name(name: str) -> str:
    return name.casefold().replace("_", "-")


def accelerator_distributions(distribution_names: Iterable[str]) -> list[str]:
    """Return normalized CUDA and NVIDIA distribution names in deterministic order."""
    return sorted(
        {
            _normalize_distribution_name(name)
            for name in distribution_names
            if _normalize_distribution_name(name).startswith(ACCELERATOR_DISTRIBUTION_PREFIXES)
        },
    )


def installed_distribution_names() -> list[str]:
    """Return installed distribution names without importing their modules."""
    return [
        name
        for distribution in importlib.metadata.distributions()
        if (name := distribution.metadata.get("Name")) is not None
    ]


def _load_torch() -> ModuleType:
    import torch

    return torch


def cpu_runtime_evidence(
    *,
    torch_present: bool,
    load_torch: Callable[[], ModuleType],
    distribution_names: Iterable[str],
) -> dict[str, Any]:
    """Collect CPU-runtime evidence without calling Torch accelerator APIs."""
    accelerator_packages = accelerator_distributions(distribution_names)
    evidence: dict[str, Any] = {
        "accelerator_distributions": accelerator_packages,
        "cuda_version": None,
        "errors": [],
        "torch_present": torch_present,
        "torch_version": None,
    }
    errors: list[str] = evidence["errors"]

    if not torch_present:
        errors.append("Torch is not installed but a CPU-only Torch runtime is required.")
    else:
        try:
            torch = load_torch()
        except Exception as error:  # noqa: BLE001 - loader failures are runtime evidence.
            errors.append(f"Torch could not be imported: {error}")
        else:
            evidence["torch_version"] = getattr(torch, "__version__", None)
            cuda_version = getattr(getattr(torch, "version", None), "cuda", None)
            evidence["cuda_version"] = cuda_version
            if cuda_version is not None:
                errors.append(f"Torch reports CUDA {cuda_version!r}; a CPU-only runtime is required.")

    if accelerator_packages:
        errors.append("CPU-only runtime contains accelerator distributions: " + ", ".join(accelerator_packages))

    return evidence


def current_cpu_runtime_evidence() -> dict[str, Any]:
    """Collect evidence for the current interpreter."""
    return cpu_runtime_evidence(
        torch_present=importlib.util.find_spec("torch") is not None,
        load_torch=_load_torch,
        distribution_names=installed_distribution_names(),
    )


def write_evidence(path: Path, evidence: dict[str, Any]) -> None:
    """Write stable JSON evidence for a CI artifact or summary step."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    evidence = current_cpu_runtime_evidence()
    if args.output_json is not None:
        write_evidence(args.output_json, evidence)
    if errors := evidence["errors"]:
        print("ERROR: " + "\nERROR: ".join(errors), file=sys.stderr)
        return 1
    print(json.dumps(evidence, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

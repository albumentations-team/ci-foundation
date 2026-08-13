from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ACTION_DIRECTORY = Path(__file__).parents[1] / "actions" / "torch-cpu"
sys.path.insert(0, str(ACTION_DIRECTORY))

import install_torch_cpu  # noqa: E402
import verify_torch_cpu  # noqa: E402


def _torch(*, cuda: str | None, version: str = "2.13.0") -> SimpleNamespace:
    return SimpleNamespace(__version__=version, version=SimpleNamespace(cuda=cuda))


def test_cpu_runtime_evidence_accepts_cpu_torch() -> None:
    evidence = verify_torch_cpu.cpu_runtime_evidence(
        torch_present=True,
        load_torch=lambda: _torch(cuda=None),
        distribution_names=["torch", "numpy"],
    )

    assert evidence["errors"] == []
    assert evidence["cuda_version"] is None
    assert evidence["torch_version"] == "2.13.0"


@pytest.mark.parametrize(
    ("torch_present", "cuda", "distribution_names", "expected_error"),
    [
        (False, None, [], "Torch is not installed"),
        (True, "12.8", [], "Torch reports CUDA"),
        (True, None, ["nvidia-cuda-runtime-cu12"], "contains accelerator distributions"),
        (True, None, ["cuda-python"], "contains accelerator distributions"),
    ],
)
def test_cpu_runtime_evidence_rejects_non_cpu_states(
    torch_present: bool,
    cuda: str | None,
    distribution_names: list[str],
    expected_error: str,
) -> None:
    evidence = verify_torch_cpu.cpu_runtime_evidence(
        torch_present=torch_present,
        load_torch=lambda: _torch(cuda=cuda),
        distribution_names=distribution_names,
    )

    assert any(expected_error in error for error in evidence["errors"])


def test_cpu_runtime_evidence_reports_torch_loader_failure() -> None:
    def load_broken_torch() -> SimpleNamespace:
        raise ImportError("missing shared library")

    evidence = verify_torch_cpu.cpu_runtime_evidence(
        torch_present=True,
        load_torch=load_broken_torch,
        distribution_names=[],
    )

    assert evidence["errors"] == ["Torch could not be imported: missing shared library"]


def test_evidence_json_is_stable(tmp_path: Path) -> None:
    evidence = {"errors": [], "torch_version": "2.13.0"}
    output_path = tmp_path / "evidence" / "torch.json"

    verify_torch_cpu.write_evidence(output_path, evidence)

    assert output_path.read_text(encoding="utf-8") == '{\n  "errors": [],\n  "torch_version": "2.13.0"\n}\n'


@pytest.mark.parametrize("requirement", ["torch", "torch>=2.13.0", "torch>=2.13.0,<2.14.0", "Torch==2.13.0"])
def test_validate_requirement_accepts_direct_torch_constraints(requirement: str) -> None:
    assert install_torch_cpu.validate_requirement(requirement) == requirement


@pytest.mark.parametrize(
    "requirement",
    [
        "torch @ https://example.invalid/torch.whl",
        "torch; python_version >= '3.10'",
        "torchvision",
        "torch>=2.13.0;echo",
    ],
)
def test_validate_requirement_rejects_indirect_or_unsafe_requirements(requirement: str) -> None:
    with pytest.raises(ValueError, match="direct Torch requirement"):
        install_torch_cpu.validate_requirement(requirement)


def test_verifier_does_not_reference_accelerator_api_calls() -> None:
    source = Path(verify_torch_cpu.__file__).read_text(encoding="utf-8")

    assert "torch.cuda." not in source
    assert "torch.mps." not in source
    assert importlib.util.find_spec("torch") is not None or "find_spec" in source

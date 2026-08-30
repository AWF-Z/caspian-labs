#!/usr/bin/env python3
"""Fail closed if the Caspian Labs public surface drifts outside its allowlist."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ALLOWED = {
    ".github/workflows/validate.yml",
    ".gitignore",
    "LICENSE",
    "README.md",
    "SECURITY.md",
    "TRADEMARK.md",
    "assets/casp-system.svg",
    "assets/caspian-hero.svg",
    "assets/wandr-result.svg",
    "docs/EVIDENCE.md",
    "docs/PRODUCT.md",
    "evidence/clinical-opportunity/result.json",
    "evidence/wandr-s45/result.json",
    "scripts/check_public_repo.py",
}

BLOCKED = {
    "/" + "Users/": "local absolute path",
    "quarry-core-" + "private": "private repository name",
    "CASP_5_0_FAILURE_" + "LEDGER": "private failure ledger",
    "CASP_5_0_WINNING_" + "MECHANISMS": "private mechanism registry",
    "judge_" + "replay.jsonl": "private evaluator receipt",
    "triage_" + "replay.jsonl": "private evaluator receipt",
    "canon_" + "replay.jsonl": "private evaluator receipt",
    "CASP_RUN_" + "CONTRACT": "private run contract",
}

SECRET_ASSIGNMENT = re.compile(
    r"(?i)(?:api[_-]?key|access[_-]?token|client[_-]?secret|password)"
    r"\s*[:=]\s*['\"][^'\"]{8,}['\"]"
)
PRIVATE_KEY = re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----")


def public_files() -> set[str]:
    found: set[str] = set()
    for path in ROOT.rglob("*"):
        if ".git" in path.parts or path.is_dir():
            continue
        found.add(path.relative_to(ROOT).as_posix())
    return found


def main() -> None:
    actual = public_files()
    failures: list[str] = []

    unknown = sorted(actual - ALLOWED)
    missing = sorted(ALLOWED - actual)
    if unknown:
        failures.append("unknown files: " + ", ".join(unknown))
    if missing:
        failures.append("missing allowlisted files: " + ", ".join(missing))

    for rel in sorted(actual):
        path = ROOT / rel
        if path.is_symlink():
            failures.append(f"symlink forbidden: {rel}")
            continue
        if path.stat().st_size > 1_000_000:
            failures.append(f"file exceeds public size ceiling: {rel}")
            continue
        try:
            body = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            failures.append(f"binary file forbidden: {rel}")
            continue
        for text, reason in BLOCKED.items():
            if text in body:
                failures.append(f"{reason} in {rel}")
        if SECRET_ASSIGNMENT.search(body) or PRIVATE_KEY.search(body):
            failures.append(f"secret-shaped content in {rel}")

    wandr = json.loads((ROOT / "evidence/wandr-s45/result.json").read_text())
    if wandr.get("task_count") != 45:
        failures.append("WANDR task count drift")
    if wandr.get("genuine_metric_bearing_receipts") != 45:
        failures.append("WANDR receipt count drift")
    if wandr.get("infrastructure_zero_fills") != 0:
        failures.append("WANDR infrastructure boundary drift")
    if wandr.get("metrics", {}).get("mean_soft_f1") != 0.583303196742441:
        failures.append("WANDR soft F1 drift")
    if wandr.get("metrics", {}).get("mean_hard_f1") != 0.4926476110146942:
        failures.append("WANDR hard F1 drift")

    clinical = json.loads(
        (ROOT / "evidence/clinical-opportunity/result.json").read_text()
    )
    if clinical.get("later_positive_opportunities") != 8031:
        failures.append("clinical denominator drift")
    if clinical.get("casp_lineage", {}).get("hits") != 3821:
        failures.append("clinical CASP-lineage hit drift")
    if clinical.get("comparison", {}).get("hits") != 3155:
        failures.append("clinical comparator hit drift")
    if clinical.get("precommitted_activation_gate_passed") is not False:
        failures.append("clinical gate boundary drift")

    if failures:
        raise SystemExit("PUBLIC RELEASE AUDIT FAILED\n- " + "\n- ".join(failures))
    print(f"Public release audit passed: {len(actual)} allowlisted files")


if __name__ == "__main__":
    main()

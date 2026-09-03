#!/usr/bin/env python3
"""Fail closed if the Caspian Labs public surface drifts outside its allowlist."""

from __future__ import annotations

import hashlib
import json
import math
import re
import subprocess
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ALLOWED = {
    ".github/workflows/validate.yml",
    ".gitignore",
    "LICENSE",
    "README.md",
    "SECURITY.md",
    "TRADEMARK.md",
    "assets/casp-system-v3.svg",
    "assets/caspian-hero.svg",
    "assets/wandr-field-v5.svg",
    "docs/EVIDENCE.md",
    "docs/PRODUCT.md",
    "evidence/clinical-opportunity/result.json",
    "evidence/wandr-s45/receipt-examples/ai-funding-announcements.json",
    "evidence/wandr-s45/receipt-examples/solid-state-battery-patents.json",
    "evidence/wandr-s45/receipt-examples/us-cardiac-surgery-signals.json",
    "evidence/wandr-s45/result.json",
    "evidence/wandr-s45/task-results.json",
    "scripts/check_public_repo.py",
    "scripts/LICENSE",
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
    "CASP_5_0_" + "ARCHITECTURE.md": "private architecture specification",
    "CASP_5_0_" + "PROVENANCE.json": "private provenance record",
    "CASP_5_0_ENGINE_" + "REGISTRY.json": "private engine registry",
    "PRESERVED_" + "TASKS.json": "private preservation record",
    "SEALED_DO_" + "NOT_RERUN": "private sealed-run marker",
}

SECRET_ASSIGNMENT = re.compile(
    r"(?i)(?:api[_-]?key|access[_-]?token|client[_-]?secret|password)"
    r"\s*[:=]\s*['\"][^'\"]{8,}['\"]"
)
PRIVATE_KEY = re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----")
SHA256 = re.compile(r"^[0-9a-f]{64}$")

METRICS = {
    "soft_f1_full": "mean_soft_f1",
    "hard_f1_full": "mean_hard_f1",
    "soft_precision_full": "mean_soft_precision",
    "soft_recall_full": "mean_soft_recall",
    "hard_precision_full": "mean_hard_precision",
    "hard_recall_full": "mean_hard_recall",
}

RECEIPT_EXAMPLES = (
    "ai-funding-announcements",
    "solid-state-battery-patents",
    "us-cardiac-surgery-signals",
)


def public_files() -> set[str]:
    found: set[str] = set()
    for path in ROOT.rglob("*"):
        if ".git" in path.parts or path.is_dir():
            continue
        found.add(path.relative_to(ROOT).as_posix())
    return found


def scan_body(body: str, location: str, failures: list[str]) -> None:
    for text, reason in BLOCKED.items():
        if text in body:
            failures.append(f"{reason} in {location}")
    if SECRET_ASSIGNMENT.search(body) or PRIVATE_KEY.search(body):
        failures.append(f"secret-shaped content in {location}")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def same_number(left: object, right: object) -> bool:
    if not isinstance(left, (int, float)) or isinstance(left, bool):
        return False
    if not isinstance(right, (int, float)) or isinstance(right, bool):
        return False
    return math.isclose(float(left), float(right), rel_tol=0.0, abs_tol=1e-12)


def same_published_comparison(left: object, right: object) -> bool:
    if not isinstance(left, (int, float)) or isinstance(left, bool):
        return False
    if not isinstance(right, (int, float)) or isinstance(right, bool):
        return False
    # Table 6 displays comparator scores to three decimal places.
    return math.isclose(float(left), float(right), rel_tol=0.0, abs_tol=1e-8)


def valid_timestamp(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return False
    return parsed.tzinfo is not None


def validate_wandr_evidence(failures: list[str]) -> None:
    result_path = ROOT / "evidence/wandr-s45/result.json"
    task_results_path = ROOT / "evidence/wandr-s45/task-results.json"
    wandr = json.loads(result_path.read_text())
    task_results = json.loads(task_results_path.read_text())

    if wandr.get("task_count") != 45:
        failures.append("WANDR task count drift")
    if wandr.get("genuine_metric_bearing_receipts") != 45:
        failures.append("WANDR receipt count drift")
    if wandr.get("infrastructure_zero_fills") != 0:
        failures.append("WANDR infrastructure boundary drift")

    task_reference = wandr.get("public_task_results", {})
    if task_reference.get("path") != "task-results.json":
        failures.append("WANDR task-results path drift")
    if task_reference.get("sha256") != sha256_file(task_results_path):
        failures.append("WANDR task-results file hash mismatch")

    if task_results.get("schema") != "caspian-labs.public-wandr-task-results.v1":
        failures.append("WANDR task-results schema drift")
    if task_results.get("result_id") != wandr.get("result_id"):
        failures.append("WANDR result identifier mismatch")
    if task_results.get("evaluator") != {
        "name": "WANDR official evaluator",
        "benchmark_source": "https://github.com/perplexityai/wandr",
        "benchmark_source_commit": "ca82dc224d5c03a8cde5409c6ba49c1c4f67fff3",
        "official_configuration_sha256": "1f3934601907427e2cc141f9fd561bacdcbc97f7e22d4fc66f1453222fdf74a4",
        "verifier_python_sha256": "36984af9f922aec72ba5b03e811ee92512268785007192e20f826cbd07cf8d04",
    }:
        failures.append("WANDR evaluator binding drift")

    tasks = task_results.get("tasks")
    if not isinstance(tasks, list) or len(tasks) != 45:
        failures.append("WANDR task-results row count drift")
        return
    task_ids = [row.get("task_id") for row in tasks if isinstance(row, dict)]
    if len(task_ids) != 45 or len(set(task_ids)) != 45:
        failures.append("WANDR task identifiers are missing or duplicated")
    if task_ids != sorted(task_ids):
        failures.append("WANDR task identifiers are not in stable order")

    sums = {metric: 0.0 for metric in METRICS}
    rows_by_id: dict[str, dict[str, object]] = {}
    for index, row in enumerate(tasks):
        location = f"WANDR task-results row {index + 1}"
        if not isinstance(row, dict):
            failures.append(f"{location} is not an object")
            continue
        task_id = row.get("task_id")
        if not isinstance(task_id, str) or not task_id:
            failures.append(f"{location} has an invalid task identifier")
            continue
        rows_by_id[task_id] = row
        if row.get("status") != "GENUINE_METRIC_BEARING_OFFICIAL_SCORE":
            failures.append(f"{location} is not a genuine official score")
        if row.get("metric_bearing") is not True:
            failures.append(f"{location} is not metric-bearing")
        if row.get("infrastructure_zero_fill") is not False:
            failures.append(f"{location} has an infrastructure zero-fill")
        if not valid_timestamp(row.get("sealed_at")):
            failures.append(f"{location} has an invalid sealed timestamp")
        if not isinstance(row.get("semantic_records"), int) or row["semantic_records"] < 0:
            failures.append(f"{location} has an invalid semantic-record count")
        for key in ("official_receipt_artifact_sha256", "official_receipt_file_sha256"):
            value = row.get(key)
            if not isinstance(value, str) or not SHA256.fullmatch(value):
                failures.append(f"{location} has an invalid {key}")

        row_metrics = row.get("metrics")
        if not isinstance(row_metrics, dict) or set(row_metrics) != set(METRICS):
            failures.append(f"{location} has an invalid metric set")
            continue
        for metric in METRICS:
            value = row_metrics.get(metric)
            if (
                not isinstance(value, (int, float))
                or isinstance(value, bool)
                or not math.isfinite(float(value))
                or not 0.0 <= float(value) <= 1.0
            ):
                failures.append(f"{location} has an invalid {metric}")
                continue
            sums[metric] += float(value)

    published_aggregate = task_results.get("published_aggregate", {})
    if published_aggregate.get("task_count") != 45:
        failures.append("WANDR task-results aggregate count drift")
    for task_metric, public_metric in METRICS.items():
        recomputed = sums[task_metric] / 45
        if not same_number(recomputed, published_aggregate.get(public_metric)):
            failures.append(f"WANDR task-results {public_metric} does not recompute")
        if not same_number(recomputed, wandr.get("metrics", {}).get(public_metric)):
            failures.append(f"WANDR public {public_metric} does not match task rows")

    leader = wandr.get("published_matched_leader", {})
    comparison = wandr.get("comparison", {})
    soft_f1 = wandr.get("metrics", {}).get("mean_soft_f1")
    hard_f1 = wandr.get("metrics", {}).get("mean_hard_f1")
    leader_soft_f1 = leader.get("soft_f1")
    leader_hard_f1 = leader.get("hard_f1")
    if all(
        isinstance(value, (int, float)) and not isinstance(value, bool)
        for value in (soft_f1, hard_f1, leader_soft_f1, leader_hard_f1)
    ):
        if not same_published_comparison(
            float(soft_f1) / float(leader_soft_f1) - 1.0,
            comparison.get("relative_soft_f1_improvement"),
        ):
            failures.append("WANDR relative soft F1 comparison drift")
        if not same_published_comparison(
            float(hard_f1) / float(leader_hard_f1),
            comparison.get("hard_f1_multiple"),
        ):
            failures.append("WANDR hard F1 multiple drift")
    else:
        failures.append("WANDR comparison inputs are not numeric")

    for task_id in RECEIPT_EXAMPLES:
        receipt_path = (
            ROOT / "evidence/wandr-s45/receipt-examples" / f"{task_id}.json"
        )
        receipt = json.loads(receipt_path.read_text())
        row = rows_by_id.get(task_id)
        if row is None:
            failures.append(f"WANDR receipt example has no task row: {task_id}")
            continue
        if receipt.get("schema") != "caspian-labs.public-wandr-receipt-extract.v1":
            failures.append(f"WANDR receipt example schema drift: {task_id}")
        if receipt.get("artifact_type") != "OfficialScoreReceiptExtract":
            failures.append(f"WANDR receipt example artifact-type drift: {task_id}")
        if receipt.get("public_copy") is not True:
            failures.append(f"WANDR receipt example is not marked public: {task_id}")
        bindings = {
            "task_id": "task_id",
            "status": "status",
            "metric_bearing": "metric_bearing",
            "infrastructure_zero_fill": "infrastructure_zero_fill",
            "metrics": "metrics",
            "semantic_records": "semantic_records",
            "sealed_at": "sealed_at",
            "source_receipt_artifact_sha256": "official_receipt_artifact_sha256",
            "source_receipt_file_sha256": "official_receipt_file_sha256",
        }
        for receipt_key, row_key in bindings.items():
            if receipt.get(receipt_key) != row.get(row_key):
                failures.append(
                    f"WANDR receipt example binding mismatch: {task_id} {receipt_key}"
                )
        for key in (
            "evaluator_attempt_receipt_sha256",
            "official_terminal_sha256",
            "participant_terminal_sha256",
        ):
            value = receipt.get(key)
            if not isinstance(value, str) or not SHA256.fullmatch(value):
                failures.append(f"WANDR receipt example has an invalid {key}: {task_id}")


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
        scan_body(body, rel, failures)

    try:
        history = subprocess.run(
            ["git", "log", "--all", "--format=", "--patch"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    except subprocess.CalledProcessError as exc:
        failures.append(f"unable to scan git history: {exc}")
    else:
        scan_body(history, "git history", failures)

    validate_wandr_evidence(failures)

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

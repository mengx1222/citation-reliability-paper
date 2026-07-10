from __future__ import annotations

"""
Data integrity validation for the citation-reliability paper.

Checks:
  1. All source rows parse correctly (task_id, workflow, model).
  2. Every task_id in verification CSVs exists in task_seed.csv.
  3. No duplicate (source, citation_number) pairs.
  4. Per-session citation counts are within reasonable bounds.
  5. Total reference counts match manuscript claims.
  6. Cross-file consistency between extraction and verification tables.

Usage:
  python analysis/validate_integrity.py
"""

import csv
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TASKS_CSV = ROOT / "data" / "task_seed.csv"
DS_VERIFIED = ROOT / "results" / "verified_refs_merged.csv"
QW_VERIFIED = ROOT / "results" / "verified_refs_qwen.csv"
DS_EXTRACTED = ROOT / "results" / "extracted_refs_deepseek.csv"
QW_EXTRACTED = ROOT / "results" / "extracted_refs_qwen.csv"
E3_SAMPLE = ROOT / "data" / "e3_annotation_sample.csv"

KNOWN_WORKFLOWS = {"W0_DIRECT", "W1_CAUTIOUS", "W2_RETRIEVAL_FIRST", "W3_VERIFY_REPAIR"}
KNOWN_LANGUAGES = {"en", "zh"}
MAX_REFS_PER_SESSION = 20
MIN_REFS_PER_SESSION = 3

SOURCE_RE = re.compile(
    r"^(?P<task_id>T\d+)_(?P<workflow>W\d+_[A-Z_]+)__"
    r"(?P<model>[^.]+)\.txt$",
    re.IGNORECASE,
)

exit_code = 0


def fail(msg: str) -> None:
    global exit_code
    exit_code = 1
    print(f"  FAIL: {msg}")


def check(condition: bool, msg: str) -> None:
    if not condition:
        fail(msg)
    else:
        print(f"  OK: {msg}")


def load_task_seed() -> dict[str, str]:
    tasks: dict[str, str] = {}
    with TASKS_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            tasks[row["task_id"]] = row["language"]
    return tasks


def parse_source(source: str) -> tuple[str, str, str]:
    m = SOURCE_RE.match(source.strip())
    if not m:
        raise ValueError(f"Cannot parse source: {source}")
    return m.group("task_id"), m.group("workflow").upper(), m.group("model").lower()


def verify_csv(filepath: Path, label: str, tasks: dict[str, str]) -> dict:
    print(f"\n--- {label}")
    sources: list[str] = []
    seen: set[tuple[str, str]] = set()
    session_counts: Counter = Counter()
    task_ids: set[str] = set()
    workflows: set[str] = set()
    models: set[str] = set()
    status_counts: Counter = Counter()

    with filepath.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            fail(f"No CSV header found in {filepath.name}")
            return {}
        print(f"  Columns: {reader.fieldnames}")

        for row in reader:
            source = row.get("source", row.get("source_file", "")).strip()
            if not source:
                continue

            try:
                task_id, wf, model = parse_source(source)
            except ValueError as e:
                fail(f"  Parse error: {e}")
                continue

            sources.append(source)
            task_ids.add(task_id)
            workflows.add(wf)
            models.add(model)
            session_counts[f"{task_id}_{wf}"] += 1

            if "source" in reader.fieldnames:
                status_counts[row.get("status", "unknown")] += 1

            # citation_number check
            cit_num = row.get("citation_number", "")
            dup_key = (source, cit_num)
            if cit_num and dup_key in seen:
                fail(f"Duplicate (source, citation_number): {dup_key}")
            seen.add(dup_key)

    print(f"  Rows parsed: {len(sources)}")
    print(f"  Distinct tasks: {len(task_ids)}")
    print(f"  Workflows: {sorted(workflows)}")
    print(f"  Models: {sorted(models)}")
    print(f"  Sessions: {len(session_counts)}")
    if status_counts:
        print(f"  Status distribution: {dict(status_counts)}")

    # --- Checks ---
    check(len(sources) > 0, f"{filepath.name} has data rows")

    unknown_tasks = task_ids - set(tasks.keys())
    check(len(unknown_tasks) == 0, f"All task_ids known ({len(unknown_tasks)} unknown: {unknown_tasks})")

    unknown_wf = workflows - KNOWN_WORKFLOWS
    check(len(unknown_wf) == 0, f"All workflows known ({len(unknown_wf)} unknown: {unknown_wf})")

    for (session_key, count) in session_counts.items():
        if count > MAX_REFS_PER_SESSION:
            fail(f"Session {session_key} has {count} refs (max {MAX_REFS_PER_SESSION})")
        if count < MIN_REFS_PER_SESSION:
            fail(f"Session {session_key} has {count} refs (min {MIN_REFS_PER_SESSION})")

    expected_sessions = len(task_ids) * len(KNOWN_WORKFLOWS)
    actual_sessions = len(session_counts)
    check(actual_sessions == expected_sessions,
          f"Sessions {actual_sessions} == expected {expected_sessions}")

    return {
        "total_refs": len(sources),
        "sessions": actual_sessions,
        "tasks": len(task_ids),
        "models": sorted(models),
        "statuses": dict(status_counts),
    }


def main() -> None:
    tasks = load_task_seed()
    print(f"Task seeds loaded: {len(tasks)} tasks across {len(set(tasks.values()))} languages")

    ds = verify_csv(DS_VERIFIED, "DeepSeek verified refs", tasks)
    qw = verify_csv(QW_VERIFIED, "Qwen verified refs", tasks)
    dse = verify_csv(DS_EXTRACTED, "DeepSeek extracted refs", tasks)
    qwe = verify_csv(QW_EXTRACTED, "Qwen extracted refs", tasks)
    _e3 = verify_csv(E3_SAMPLE, "E3 annotation sample", tasks)

    # Cross-file consistency
    print(f"\n--- Cross-file checks")
    if ds and dse:
        check(ds["total_refs"] == dse["total_refs"],
              f"DeepSeek: verified ({ds['total_refs']}) matches extracted ({dse['total_refs']})")
    if qw and qwe:
        check(qw["total_refs"] == qwe["total_refs"],
              f"Qwen: verified ({qw['total_refs']}) matches extracted ({qwe['total_refs']})")

    # Total reference count check
    total_refs_in_manuscript = 1974
    total_found = (ds.get("total_refs", 0) if ds else 0) + (qw.get("total_refs", 0) if qw else 0)
    check(total_found == total_refs_in_manuscript,
          f"Total refs {total_found} == manuscript claim {total_refs_in_manuscript}")

    print(f"\n{'='*50}")
    if exit_code == 0:
        print("All integrity checks passed.")
    else:
        print(f"Some checks failed (exit code {exit_code}). Review messages above.")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

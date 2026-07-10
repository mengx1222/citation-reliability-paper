from __future__ import annotations

"""
Orchestration script for the citation-reliability experiment pipeline.

Usage:
  python code/run_experiment.py --status        show what's available
  python code/run_experiment.py --all            run all automated steps
  python code/run_experiment.py --step prompts   regenerate prompts only
  python code/run_experiment.py --step tables    regenerate analysis tables

Steps that require external API credentials or model outputs are marked
and skip gracefully when inputs are missing.
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# --- Artifact registry ------------------------------------------------

ARTIFACTS = {
    "prompts": {
        "script": ROOT / "code" / "build_prompts.py",
        "inputs": [ROOT / "data" / "task_seed.csv"],
        "outputs": [ROOT / "data" / "prompts.csv"],
        "label": "Generate prompt set from task seeds",
        "requires_api": False,
        "requires_outputs": False,
    },
    "extract_deepseek": {
        "script": ROOT / "analysis" / "rebuild_extracted.py",
        "inputs": [ROOT / "results" / "verified_refs_merged.csv"],
        "outputs": [ROOT / "results" / "extracted_refs_deepseek.csv"],
        "label": "Rebuild DeepSeek extraction table from verification CSV",
        "requires_api": False,
        "requires_outputs": False,
    },
    "summarize": {
        "script": ROOT / "analysis" / "summarize_results.py",
        "inputs": [
            ROOT / "results" / "verified_refs_merged.csv",
            ROOT / "results" / "verified_refs_qwen.csv",
        ],
        "outputs": [
            ROOT / "analysis" / "summary_metrics.md",
            ROOT / "analysis" / "summary_metrics.json",
            ROOT / "docs" / "figures" / "resolved-rate-by-workflow.svg",
        ],
        "label": "Generate summary metrics and figure",
        "requires_api": False,
        "requires_outputs": False,
    },
    "tables": {
        "script": ROOT / "analysis" / "statistical_analysis.py",
        "inputs": [
            ROOT / "results" / "verified_refs_merged.csv",
            ROOT / "results" / "verified_refs_qwen.csv",
            ROOT / "data" / "task_seed.csv",
        ],
        "outputs": [
            ROOT / "analysis" / "generated" / "paper_tables.md",
            ROOT / "analysis" / "generated" / "paper_tables.json",
        ],
        "label": "Generate paper tables with Wilson CIs and per-session stats",
        "requires_api": False,
        "requires_outputs": False,
    },
    "extract_qwen_raw": {
        "script": ROOT / "code" / "verify_citations.py",
        "args": ["extract", "--outputs-dir", "outputs/qwen",
                 "--out", "results/extracted_refs_qwen.csv"],
        "label": "Extract references from raw Qwen model outputs",
        "requires_api": False,
        "requires_outputs": True,
    },
    "extract_deepseek_raw": {
        "script": ROOT / "code" / "verify_citations.py",
        "args": ["extract", "--outputs-dir", "outputs/deepseek",
                 "--out", "results/extracted_refs_deepseek.csv"],
        "label": "Extract references from raw DeepSeek model outputs",
        "requires_api": False,
        "requires_outputs": True,
    },
    "verify_qwen": {
        "script": ROOT / "code" / "verify_citations.py",
        "args": ["verify", "--input", "results/extracted_refs_qwen.csv",
                 "--out", "results/verified_refs_qwen.csv", "--online"],
        "label": "Verify Qwen references against Crossref, OpenAlex, arXiv APIs",
        "requires_api": True,
        "requires_outputs": False,
    },
    "verify_deepseek": {
        "script": ROOT / "code" / "verify_citations.py",
        "args": ["verify", "--input", "results/extracted_refs_deepseek.csv",
                 "--out", "results/verified_refs_merged.csv", "--online"],
        "label": "Verify DeepSeek references against Crossref, OpenAlex, arXiv APIs",
        "requires_api": True,
        "requires_outputs": False,
    },
}

# --- Step ordering ----------------------------------------------------

STEP_ORDER = [
    "prompts",
    "extract_deepseek_raw",
    "extract_qwen_raw",
    "verify_deepseek",
    "verify_qwen",
    "extract_deepseek",
    "summarize",
    "tables",
]

AUTO_ORDER = [
    "prompts",
    "extract_deepseek",
    "summarize",
    "tables",
]


# --- Helpers ----------------------------------------------------------

def check_input(entry: dict) -> bool:
    for inp in entry.get("inputs", []):
        if isinstance(inp, Path) and not inp.exists():
            return False
    return True


def check_output(entry: dict) -> tuple[bool, str]:
    for out in entry.get("outputs", []):
        if out.exists():
            return True, "exists"
    return False, "not generated"


def run_step(step_name: str) -> bool:
    entry = ARTIFACTS[step_name]
    print(f"\n{'='*50}")
    print(f"Step: {step_name}  --  {entry['label']}")
    print(f"{'='*50}")

    if entry.get("requires_outputs"):
        for inp in entry.get("inputs", []):
            if isinstance(inp, Path) and not inp.exists():
                print(f"  [SKIP] missing input: {inp}")
                return False

    if entry.get("requires_api"):
        print(f"  [SKIP] requires API access (not available without credentials)")
        return False

    script = entry["script"]
    args = entry.get("args", [])
    cmd = [sys.executable, str(script)] + args

    print(f"  Running: python {script.relative_to(ROOT)} {' '.join(args)}")
    t0 = time.time()
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    elapsed = time.time() - t0

    if result.returncode == 0:
        print(f"  [OK] completed in {elapsed:.1f}s")
        if result.stdout.strip():
            for line in result.stdout.strip().splitlines()[-3:]:
                print(f"       {line}")
        return True
    else:
        print(f"  [FAIL] return code {result.returncode}")
        if result.stderr.strip():
            for line in result.stderr.strip().splitlines()[-5:]:
                print(f"       {line}")
        return False


# --- Commands ---------------------------------------------------------

def cmd_status() -> None:
    print(f"Experiment Pipeline - Artifact Status")
    print("=" * 50)
    print(f"{'Step':<25} {'Inputs':<10} {'Outputs':<10} {'Note'}")
    print("-" * 55)

    for step_name in STEP_ORDER:
        entry = ARTIFACTS[step_name]
        inputs_ok = check_input(entry)
        outputs_ok, _ = check_output(entry)
        note = ""
        if entry.get("requires_outputs") and not inputs_ok:
            note = "needs raw outputs"
        elif entry.get("requires_api"):
            note = "needs API access"

        in_sym = "Y" if inputs_ok or not entry.get("inputs") else "."
        out_sym = "Y" if outputs_ok else "."

        print(f"{step_name:<25} {in_sym:<10} {out_sym:<10} {note}")

    print()
    print("Auto steps (no API, no raw outputs needed):")
    print("  python code/run_experiment.py --all")
    print()
    print("Full pipeline (needs API keys + raw model outputs):")
    print("  python code/run_experiment.py --all --allow-api --allow-raw")


def cmd_auto() -> None:
    for step_name in AUTO_ORDER:
        run_step(step_name)


def cmd_full() -> None:
    for step_name in STEP_ORDER:
        if not run_step(step_name):
            print(f"  Stopping at {step_name}")
            break


def cmd_single(step_name: str) -> None:
    if step_name not in ARTIFACTS:
        print(f"Unknown step '{step_name}'. Available: {', '.join(ARTIFACTS)}")
        sys.exit(1)
    run_step(step_name)


# --- CLI --------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Citation-reliability experiment pipeline orchestrator"
    )
    p.add_argument("--status", action="store_true", help="show artifact status")
    p.add_argument("--all", action="store_true", help="run all automated steps")
    p.add_argument("--allow-api", action="store_true", help="include API-dependent steps")
    p.add_argument("--allow-raw", action="store_true", help="include raw-output steps")
    p.add_argument("--step", type=str, help="run a single step by name")
    return p


def main() -> None:
    args = build_parser().parse_args()

    if args.status:
        cmd_status()
    elif args.step:
        cmd_single(args.step)
    elif args.all:
        if args.allow_api or args.allow_raw:
            cmd_full()
        else:
            cmd_auto()
    else:
        cmd_status()


if __name__ == "__main__":
    main()

from __future__ import annotations

import csv
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERIFIED_CSV = ROOT / "results" / "verified_refs_merged.csv"
OUTPUT_CSV = ROOT / "results" / "extracted_refs_deepseek.csv"

SOURCE_RE = re.compile(
    r"^(?P<task_id>T\d+)_(?P<workflow>W\d+_[A-Z_]+)__"
    r"(?P<model>[^.]+)\.txt$",
    re.IGNORECASE,
)


def run() -> None:
    src_to_refs: dict[str, list[dict[str, str]]] = defaultdict(list)

    with VERIFIED_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            source = row.get("source", "").strip()
            if not source:
                continue
            match = SOURCE_RE.match(source)
            if not match:
                print(f"Warn: could not parse source '{source}'")
                continue
            src_to_refs[source].append(
                {
                    "source_file": source,
                    "reference_text": row.get("ref_text", "").strip(),
                    "doi_in_text": row.get("doi", "").strip(),
                }
            )

    out_rows: list[dict[str, str]] = []
    for source in sorted(src_to_refs):
        for idx, ref in enumerate(src_to_refs[source], start=1):
            out_rows.append(
                {
                    "source_file": ref["source_file"],
                    "citation_number": str(idx),
                    "reference_text": ref["reference_text"],
                    "doi_in_text": ref["doi_in_text"],
                }
            )

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "source_file",
                "citation_number",
                "reference_text",
                "doi_in_text",
            ],
        )
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"Wrote {len(out_rows)} extracted references to {OUTPUT_CSV}")


if __name__ == "__main__":
    run()

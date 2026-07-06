from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASKS_CSV = ROOT / "data" / "task_seed.csv"
PROMPTS_CSV = ROOT / "data" / "prompts.csv"


WORKFLOWS = ("W0_DIRECT", "W1_CAUTIOUS", "W2_RETRIEVAL_FIRST", "W3_VERIFY_REPAIR")


def response_format(language: str) -> str:
    if language == "zh":
        return (
            "请严格使用以下结构输出：\n"
            "[正文]\n"
            "一段 300-500 字的相关工作综述，使用 [1]、[2] 这类编号引用。\n\n"
            "[References]\n"
            "按编号列出 5-8 条参考文献。每条尽量包含作者、年份、题名、来源和 DOI。"
        )
    return (
        "Use this exact output structure:\n"
        "[Body]\n"
        "One related-work paragraph of 150-250 words using numbered citations such as [1] and [2].\n\n"
        "[References]\n"
        "List 5-8 references by number. Include authors, year, title, venue/source, and DOI when available."
    )


def build_prompt(task: dict[str, str], workflow: str) -> str:
    lang = task["language"]
    question = task["research_question"]
    base_format = response_format(lang)

    if lang == "zh":
        if workflow == "W0_DIRECT":
            return (
                f"研究问题：{question}\n\n"
                "请写一段学术论文相关工作综述，并加入参考文献。\n\n"
                f"{base_format}"
            )
        if workflow == "W1_CAUTIOUS":
            return (
                f"研究问题：{question}\n\n"
                "请写一段学术论文相关工作综述。只引用你确信真实存在的论文；如果不确定，不要编造。"
                "尽量给出 DOI，但不要猜 DOI。引用必须能被作者、年份、题名或 DOI 核验。\n\n"
                f"{base_format}"
            )
        if workflow == "W2_RETRIEVAL_FIRST":
            return (
                f"研究问题：{question}\n\n"
                "下面会提供候选文献列表。请只基于候选文献写相关工作综述，不要引用候选列表之外的论文。"
                "如果候选文献不足，请明确说明，而不是编造引用。\n\n"
                "[Retrieved Sources]\n"
                "{{retrieved_sources}}\n\n"
                f"{base_format}"
            )
        if workflow == "W3_VERIFY_REPAIR":
            return (
                f"研究问题：{question}\n\n"
                "请先写一段学术论文相关工作综述。随后这些引用会被自动核验；因此请只使用真实、可核验的引用，"
                "不要虚构作者、题名、年份、期刊或 DOI。\n\n"
                f"{base_format}"
            )
    else:
        if workflow == "W0_DIRECT":
            return (
                f"Research question: {question}\n\n"
                "Write a related-work paragraph for an academic paper and include references.\n\n"
                f"{base_format}"
            )
        if workflow == "W1_CAUTIOUS":
            return (
                f"Research question: {question}\n\n"
                "Write a related-work paragraph for an academic paper. Cite only papers that you are confident really exist. "
                "If you are unsure, do not fabricate a reference. Include DOI when available, but do not guess DOI values. "
                "Each reference must be verifiable by author, year, title, or DOI.\n\n"
                f"{base_format}"
            )
        if workflow == "W2_RETRIEVAL_FIRST":
            return (
                f"Research question: {question}\n\n"
                "You will be given a list of retrieved candidate papers. Write the related-work paragraph using only those papers. "
                "Do not cite papers outside the retrieved list. If the list is insufficient, say so rather than fabricating citations.\n\n"
                "[Retrieved Sources]\n"
                "{{retrieved_sources}}\n\n"
                f"{base_format}"
            )
        if workflow == "W3_VERIFY_REPAIR":
            return (
                f"Research question: {question}\n\n"
                "Write a related-work paragraph for an academic paper. The references will later be automatically verified, "
                "so use only real and verifiable references. Do not invent authors, titles, years, venues, or DOI values.\n\n"
                f"{base_format}"
            )

    raise ValueError(f"Unknown workflow: {workflow}")


def main() -> None:
    with TASKS_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        tasks = list(csv.DictReader(f))

    rows: list[dict[str, str]] = []
    for task in tasks:
        for workflow in WORKFLOWS:
            prompt_id = f"{task['task_id']}_{workflow}"
            rows.append(
                {
                    "prompt_id": prompt_id,
                    "task_id": task["task_id"],
                    "domain": task["domain"],
                    "language": task["language"],
                    "workflow": workflow,
                    "research_question": task["research_question"],
                    "prompt": build_prompt(task, workflow),
                }
            )

    with PROMPTS_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "prompt_id",
                "task_id",
                "domain",
                "language",
                "workflow",
                "research_question",
                "prompt",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} prompts to {PROMPTS_CSV}")


if __name__ == "__main__":
    main()


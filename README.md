# Citation Reliability in LLM-Assisted Academic Writing

[English](#english) | [中文](#中文)

---

<a name="english"></a>

## English

### Experiment Summary

This workspace contains a complete empirical study evaluating citation reliability in LLM-assisted academic writing.

- **Model**: DeepSeek-chat
- **Task**: 30 research questions × 4 workflows × 2 languages = 120 paragraphs
- **Extracted references**: 950
- **Verified against**: Crossref, OpenAlex, arXiv APIs

### Key Results

| Metric | Value |
|--------|-------|
| Verified genuine | 561/950 (59.1%) |
| Estimated hallucinated (E1) | ~363/950 (38.2%) |
| Best workflow | W1 Cautious Prompt (E1 ~13%) |
| Worst workflow | W2 Retrieval-first (E1 ~31%) |
| Language gap | English 62.4% vs Chinese 55.5% resolved |

### Repository Structure

```
├── paper_submission.tex           # LaTeX source (arXiv/journal-ready)
├── paper_submission.md            # Full English Markdown version
├── cover_letter.md                # Submission cover letter
├── seed_sources.md                # Core literature seeds
├── data/
│   ├── prompts.csv                # 120 experiment prompts (4 workflows × 30 tasks)
│   └── task_seed.csv              # 30 research questions
├── code/
│   ├── verify_citations.py        # Citation extraction and API verification pipeline
│   ├── build_prompts.py           # Prompt generation script
│   └── scoring_rubric.md          # Human annotation rubric for claim support
└── results/
    └── verified_refs_merged.csv   # 950 verified references (326 KB)
```

### How to Reproduce

1. Run `code/build_prompts.py` to generate prompts
2. Send prompts to DeepSeek (or other LLM) API
3. Run `code/verify_citations.py` to extract and verify references
4. Statistical analysis from merged results

### Publication

Manuscript prepared for submission. Target venues: *Applied Intelligence* / arXiv preprint.

---

<a name="中文"></a>

## 中文

### 实验概述

本研究对大语言模型辅助学术写作中的引用可靠性进行了受控实证评估。

- **模型**: DeepSeek-chat
- **任务**: 30个研究问题 × 4种工作流 × 2种语言 = 120段输出
- **提取引用**: 950条
- **核验来源**: Crossref、OpenAlex、arXiv API

### 核心结果

| 指标 | 数值 |
|------|------|
| 验证为真实 | 561/950 (59.1%) |
| 估算幻觉引用 (E1) | ~363/950 (38.2%) |
| 最佳工作流 | W1 谨慎提示 (E1 ~13%) |
| 最差工作流 | W2 检索优先 (E1 ~31%) |
| 语言差异 | 英文 62.4% vs 中文 55.5% resolved |

### 仓库结构

```
├── paper_submission.tex           # LaTeX 源文件（arXiv/期刊可直接编译）
├── paper_submission.md            # 英文 Markdown 完整版
├── cover_letter.md                # 投稿推荐信
├── seed_sources.md                # 核心文献种子
├── data/
│   ├── prompts.csv                # 120 条实验 prompts
│   └── task_seed.csv              # 30 个研究问题
├── code/
│   ├── verify_citations.py        # 引用核验管线
│   ├── build_prompts.py           # prompt 生成脚本
│   └── scoring_rubric.md          # 人工评分规则
└── results/
    └── verified_refs_merged.csv   # 950 条核验结果 (326 KB)
```

### 如何复现

1. 运行 `code/build_prompts.py` 生成 prompts
2. 将 prompts 发送至 DeepSeek（或其他 LLM）API
3. 运行 `code/verify_citations.py` 提取并核验引用
4. 对合并结果进行统计分析

### 发表状态

稿件准备中。目标期刊: *Applied Intelligence* / arXiv 预印本。

---

## License

This project is available for academic use.

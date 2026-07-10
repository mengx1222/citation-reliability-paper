"""Tests for the citation verification pipeline and analysis utilities.

Run with:  python -m pytest tests/ -v
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Add directories to path so imports work
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "analysis"))
os.chdir(str(PROJECT_ROOT))  # Ensure CWD is project root

# Direct import of the verification module functions
import importlib.util as iu

_ver = (PROJECT_ROOT / "code" / "verify_citations.py").read_text(encoding="utf-8")
exec(_ver, globals())

import common


# ── verify_citations tests ─────────────────────────────────────────────
class TestTextUtilities:
    def test_normalize_space(self):
        assert normalize_space("  hello   world  ") == "hello world"  # noqa: F821
        assert normalize_space("") == ""  # noqa: F821
        assert normalize_space("  ") == ""  # noqa: F821

    def test_normalize_title(self):
        result = normalize_title("Hello World https://example.com 10.1234/test")  # noqa: F821
        assert "hello" in result
        assert "world" in result
        assert "https" not in result
        assert "10.1234" not in result

    def test_similarity_perfect(self):
        assert similarity("Hello World", "Hello World") == 1.0  # noqa: F821

    def test_similarity_partial(self):
        s = similarity("Machine Learning for NLP", "Deep Learning for NLP")  # noqa: F821
        assert 0.5 < s < 1.0

    def test_similarity_unrelated(self):
        s = similarity("Quantum Physics", "Cooking Recipes")  # noqa: F821
        assert s < 0.3


class TestGuessTitle:
    def test_guess_from_quotes(self):
        ref = 'Author (2024). "A Very Specific Paper Title." Journal.'
        title = guess_title(ref)  # noqa: F821
        assert "Very Specific Paper Title" in title

    def test_guess_after_year(self):
        ref = "Smith, J. (2020). The title of the paper. Journal of Examples, 10(2), 100-110."
        title = guess_title(ref)  # noqa: F821
        assert "title of the paper" in title.lower()

    def test_guess_fallback(self):
        ref = "Some. Random. Text. Without. Clear. Title."
        title = guess_title(ref)  # noqa: F821
        assert title


class TestExtractReferences:
    def test_basic_extraction(self):
        text = """[References]
[1] Author, A. (2024). Title. Journal. doi:10.1234/test
[2] Another, B. (2023). Another Title. Conference."""
        refs = extract_references(text, "test.txt")  # noqa: F821
        assert len(refs) == 2
        assert refs[0].citation_number == "1"
        assert refs[0].doi_in_text == "10.1234/test"
        assert refs[1].citation_number == "2"
        assert refs[1].doi_in_text == ""

    def test_chinese_marker(self):
        text = """[参考文献]
[1] 王, (2024). 标题. 期刊."""
        refs = extract_references(text, "zh.txt")  # noqa: F821
        assert len(refs) == 1
        assert refs[0].citation_number == "1"

    def test_dot_numbered_references(self):
        text = """[References]
1. Smith, J. (2024). Title. Journal.
2. Lee, K. (2023). Another Paper. Venue."""
        refs = extract_references(text, "test.txt")  # noqa: F821
        assert len(refs) == 2

    def test_multi_line_reference(self):
        text = """[References]
[1] Author, A. (2024). A very long title that
spans across two lines. Journal."""
        refs = extract_references(text, "test.txt")  # noqa: F821
        assert len(refs) == 1
        assert "spans across" in refs[0].reference_text

    def test_no_references_section(self):
        text = "Just some text without references."
        refs = extract_references(text, "test.txt")  # noqa: F821
        assert len(refs) == 0


class TestDOIRegEx:
    def test_standard_doi(self):
        m = DOI_RE.search("doi:10.1000/abc123")  # noqa: F821
        assert m is not None
        assert m.group(0) == "10.1000/abc123"

    def test_arxiv_doi(self):
        m = DOI_RE.search("10.48550/arXiv.2301.00001")  # noqa: F821
        assert m is not None

    def test_nested_doi(self):
        m = DOI_RE.search("10.1016/j.neuron.2023.01.001")  # noqa: F821
        assert m is not None


# ── analysis/common.py tests ──────────────────────────────────────────
class TestCommon:
    def test_normalize_status_mapped(self):
        assert common.normalize_status("exists_metadata_plausible") == "resolved"
        assert common.normalize_status("unresolved") == "unresolved"
        assert common.normalize_status("no_doi") == "no_doi"
        assert common.normalize_status("RESOLVED") == "resolved"
        assert common.normalize_status("") == "no_doi"

    def test_normalize_status_unknown(self):
        assert common.normalize_status("garbage_status") == "unresolved"

    def test_workflow_order(self):
        assert len(common.WORKFLOW_ORDER) == 4
        assert common.WORKFLOW_ORDER[0] == "W0_DIRECT"

    def test_parse_source_name(self):
        t, w, m = common.parse_source_name("T001_W0_DIRECT__deepseek-chat.txt")
        assert t == "T001"
        assert w == "W0_DIRECT"
        assert m == "deepseek-chat"

    def test_parse_source_name_raises(self):
        import pytest
        with pytest.raises(ValueError):
            common.parse_source_name("invalid.txt")

    def test_source_re_variations(self):
        t, w, m = common.parse_source_name("T010_W2_RETRIEVAL_FIRST__qwen3-14b.txt")
        assert t == "T010"
        assert w == "W2_RETRIEVAL_FIRST"
        assert m == "qwen3-14b"

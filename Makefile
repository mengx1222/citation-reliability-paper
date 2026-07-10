# ──────────────────────────────────────────────────────────────────────────
#  Citation Reliability Paper — Automation Makefile
# ──────────────────────────────────────────────────────────────────────────
#  Run `make` or `make all` to regenerate all reproducible artifacts.
#  Run `make help` to list available targets.
# ──────────────────────────────────────────────────────────────────────────

.PHONY: all help prompts summary tables stats sensitivity viz integrity test clean

help:
	@echo "Available targets:"
	@echo "  all         - Run all automated steps (default)"
	@echo "  prompts     - Rebuild prompt set from task seeds"
	@echo "  summary     - Generate summary metrics and bar chart"
	@echo "  tables      - Generate paper tables with significance tests"
	@echo "  stats       - Alias for tables"
	@echo "  sensitivity - Run sensitivity analysis on thresholds"
	@echo "  viz         - Generate all visualizations (forest plot, heatmap, etc.)"
	@echo "  integrity   - Validate data integrity"
	@echo "  test        - Run unit tests"
	@echo "  clean       - Remove generated outputs"

all: prompts summary tables sensitivity viz integrity

prompts:
	python code/build_prompts.py

summary:
	python analysis/summarize_results.py

tables stats:
	python analysis/statistical_analysis.py

sensitivity:
	python analysis/sensitivity_analysis.py

viz:
	python analysis/visualizations.py

integrity:
	python analysis/validate_integrity.py

test:
	python -m pytest tests/ -v

clean:
	rm -rf analysis/generated/*
	rm -rf cache/
	rm -f analysis/summary_metrics.md
	rm -f analysis/summary_metrics.json
	rm -f docs/figures/*.svg

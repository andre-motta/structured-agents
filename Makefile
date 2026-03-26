.PHONY: venv install dev lint clean mcp-config help

VENV_DIR := .venv
VENV_PIP := $(VENV_DIR)/bin/pip
VENV_PYTHON := $(VENV_DIR)/bin/python
WORKSPACE ?=
CLAUDE_CODE ?=

PYTHON ?= $(shell command -v python3.12 2>/dev/null || command -v python3.11 2>/dev/null || echo python3)

$(VENV_PIP):
	rm -rf $(VENV_DIR)
	$(PYTHON) -m venv --upgrade-deps $(VENV_DIR)

venv: $(VENV_PIP) ## Create venv and install project with dev dependencies
	$(VENV_PIP) install --quiet --editable ".[dev,mcp]"

install: ## Install project (assumes venv is active)
	pip install -e ".[dev,mcp]"

dev: venv mcp-config ## Full dev setup (venv + MCP config)

lint: ## Run linters
	$(VENV_DIR)/bin/ruff check src/
	$(VENV_DIR)/bin/mypy src/

clean: ## Remove venv and caches
	rm -rf $(VENV_DIR)
	rm -rf .mypy_cache .ruff_cache .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

mcp-config: ## Generate MCP config from .env (WORKSPACE=path, CLAUDE_CODE=1 for Claude Code)
ifdef WORKSPACE
	python3 scripts/generate-mcp-config.py --workspace $(WORKSPACE) $(if $(CLAUDE_CODE),--claude-code)
else
	python3 scripts/generate-mcp-config.py $(if $(CLAUDE_CODE),--claude-code)
endif

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

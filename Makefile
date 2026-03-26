.PHONY: mcp-config install dev lint help

WORKSPACE ?=
CLAUDE_CODE ?=

mcp-config: ## Generate MCP config from .env (WORKSPACE=path, CLAUDE_CODE=1 for Claude Code)
ifdef WORKSPACE
	python3 scripts/generate-mcp-config.py --workspace $(WORKSPACE) $(if $(CLAUDE_CODE),--claude-code)
else
	python3 scripts/generate-mcp-config.py $(if $(CLAUDE_CODE),--claude-code)
endif

install: ## Install in development mode
	pip install -e ".[dev,mcp]"

dev: install mcp-config ## Full dev setup

lint: ## Run linters
	ruff check src/
	mypy src/

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

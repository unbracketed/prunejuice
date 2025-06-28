# Makefile for prunejuice project

.PHONY: help test test-python shellcheck check-todos all test-env test-env-clean install uninstall dev-link dev-unlink

# Default target - show help
help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

test: test-python ## Run Python implementation tests
	@echo "All tests completed successfully!"

test-python: ## Run Python implementation tests
	@echo "Running Python implementation tests..."
	@if [ -d "python-implementation/prunejuice" ]; then \
		cd python-implementation/prunejuice && \
		if command -v uv >/dev/null 2>&1; then \
			uv run pytest tests/test_database.py tests/test_executor.py -v; \
		else \
			echo "Warning: uv not installed. Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"; \
			exit 1; \
		fi; \
	else \
		echo "Python implementation not found at python-implementation/prunejuice"; \
		exit 1; \
	fi

shellcheck: ## Run shellcheck linting on shell tools (plum/pots)
	@echo "Running shellcheck on shell tools..."
	@if command -v shellcheck >/dev/null 2>&1; then \
		find scripts -name "*.sh" -type f -exec shellcheck {} +; \
		shellcheck scripts/plum/plum scripts/pots/pots; \
		echo "Shellcheck completed successfully!"; \
	else \
		echo "Warning: shellcheck not installed. Install with: brew install shellcheck"; \
		exit 1; \
	fi

check-todos: ## Check for TODO items in code
	@echo "Checking for TODO items..."
	@if grep -r "TODO\|FIXME\|XXX\|HACK" scripts/ python-implementation/ --include="*.sh" --include="*.py" --include="*.yaml" 2>/dev/null; then \
		echo "Found TODO items above that need attention"; \
		exit 1; \
	else \
		echo "No TODO items found"; \
	fi

all: shellcheck test check-todos ## Run full validation suite (shellcheck + Python tests + todo check)
	@echo ""
	@echo "✅ All validation checks passed!"
	@echo "  - Shellcheck: PASSED"
	@echo "  - Python Tests: PASSED" 
	@echo "  - TODO check: PASSED"

test-env: ## Create a temporary git repo for testing
	@echo "Creating test environment..."
	@mkdir -p .testdirs
	@TESTDIR=".testdirs/test-$$(date +%Y%m%d-%H%M%S)"; \
	mkdir -p "$$TESTDIR" && \
	cd "$$TESTDIR" && \
	git init -q && \
	echo "test README" > README.md && \
	git add README.md && \
	git commit -q -m "Initial commit" && \
	echo "" && \
	echo "Test environment created at: $$TESTDIR" && \
	echo "Entering test environment shell (type 'exit' to return)..." && \
	echo "" && \
	exec $${SHELL:-bash} -i

test-env-clean: ## Clean up all test environments
	@echo "Cleaning test environments..."
	@if [ -d .testdirs ]; then \
		rm -rf .testdirs && \
		echo "All test environments removed"; \
	else \
		echo "No test environments found"; \
	fi

PREFIX ?= /usr/local
BINDIR = $(PREFIX)/bin
PROJECT_ROOT = $(shell pwd)

dev-link: ## Install Python implementation in development mode
	@echo "Installing Python implementation in development mode..."
	@if [ -d "python-implementation/prunejuice" ]; then \
		cd python-implementation/prunejuice && \
		if command -v uv >/dev/null 2>&1; then \
			uv pip install -e . && \
			echo "Python implementation installed in development mode"; \
			echo "Commands available: prj, prunejuice"; \
			echo "Shell tools available: plum ($(PROJECT_ROOT)/scripts/plum/plum), pots ($(PROJECT_ROOT)/scripts/pots/pots)"; \
		else \
			echo "Warning: uv not installed. Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"; \
			exit 1; \
		fi; \
	else \
		echo "Python implementation not found at python-implementation/prunejuice"; \
		exit 1; \
	fi

dev-unlink: ## Remove development installation
	@echo "Removing development installation..."
	@if command -v uvx >/dev/null 2>&1; then \
		uvx uninstall prunejuice 2>/dev/null || echo "prunejuice not installed with uvx"; \
	fi
	@echo "Development installation removed"

install: ## Install Python implementation globally with uvx
	@echo "Installing PruneJuice globally..."
	@if [ -d "python-implementation/prunejuice" ]; then \
		if command -v uvx >/dev/null 2>&1; then \
			cd python-implementation/prunejuice && uvx install . && \
			mkdir -p $(BINDIR) && \
			install -m 755 ../../scripts/plum/plum $(BINDIR)/plum && \
			install -m 755 ../../scripts/pots/pots $(BINDIR)/pots && \
			echo "✅ PruneJuice installed successfully!"; \
			echo ""; \
			echo "Commands available:"; \
			echo "  prj                 - Main PruneJuice command"; \
			echo "  prunejuice          - Alias for prj"; \
			echo "  plum                - Worktree manager"; \
			echo "  pots                - Tmux session manager"; \
			echo ""; \
			echo "Get started:"; \
			echo "  prj init            - Initialize a project"; \
			echo "  prj list-commands   - List available commands"; \
			echo "  prj --help          - Show help"; \
		else \
			echo "Warning: uvx not installed. Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"; \
			exit 1; \
		fi; \
	else \
		echo "Python implementation not found at python-implementation/prunejuice"; \
		exit 1; \
	fi

uninstall: ## Remove PruneJuice installation
	@echo "Removing PruneJuice installation..."
	@if command -v uvx >/dev/null 2>&1; then \
		uvx uninstall prunejuice 2>/dev/null || echo "prunejuice not installed with uvx"; \
	fi
	@rm -f $(BINDIR)/plum $(BINDIR)/pots
	@echo "PruneJuice removed"
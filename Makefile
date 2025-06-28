# Makefile for prunejuice project

.PHONY: help test test-pots test-manual shellcheck check-todos all test-env test-env-clean install uninstall dev-link dev-unlink

# Default target - show help
help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

test: test-pots ## Run all tests in the project
	@echo "All tests completed successfully!"

test-pots: ## Run POTS bats test suite
	@echo "Running POTS test suite..."
	@if command -v bats >/dev/null 2>&1; then \
		cd scripts/pots/test && ./run-tests.sh; \
	else \
		echo "Warning: bats not installed, running manual tests instead..."; \
		cd scripts/pots/test && ./manual-test.sh; \
	fi

test-manual: ## Run manual tests (without bats requirement)
	@echo "Running manual tests..."
	@cd scripts/pots/test && ./manual-test.sh

shellcheck: ## Run shellcheck linting on all shell scripts
	@echo "Running shellcheck on shell scripts..."
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
	@if grep -r "TODO\|FIXME\|XXX\|HACK" scripts/ --include="*.sh" --include="*.bats" 2>/dev/null; then \
		echo "Found TODO items above that need attention"; \
		exit 1; \
	else \
		echo "No TODO items found"; \
	fi

all: shellcheck test check-todos ## Run full validation suite (shellcheck + tests + todo check)
	@echo ""
	@echo "✅ All validation checks passed!"
	@echo "  - Shellcheck: PASSED"
	@echo "  - Tests: PASSED" 
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

dev-link: ## Create symlinks to local commands for development
	@echo "Creating development symlinks..."
	@sudo mkdir -p /usr/local/bin
	@sudo ln -sf "$(PROJECT_ROOT)/scripts/prunejuice-cli.sh" /usr/local/bin/prunejuice-cli
	@sudo ln -sf "$(PROJECT_ROOT)/scripts/prunejuice-cli.sh" /usr/local/bin/prj
	@sudo ln -sf "$(PROJECT_ROOT)/scripts/plum/plum" /usr/local/bin/plum
	@sudo ln -sf "$(PROJECT_ROOT)/scripts/pots/pots" /usr/local/bin/pots
	@echo "Development symlinks created in /usr/local/bin/"

dev-unlink: ## Remove development symlinks
	@echo "Removing development symlinks..."
	@sudo rm -f /usr/local/bin/prunejuice-cli /usr/local/bin/prj /usr/local/bin/plum /usr/local/bin/pots
	@echo "Development symlinks removed"

install: ## Install commands to system PATH
	@echo "Installing prunejuice commands to $(BINDIR)..."
	@mkdir -p $(BINDIR)
	@install -m 755 scripts/prunejuice-cli.sh $(BINDIR)/prunejuice-cli
	@ln -sf $(BINDIR)/prunejuice-cli $(BINDIR)/prj
	@install -m 755 scripts/plum/plum $(BINDIR)/plum
	@install -m 755 scripts/pots/pots $(BINDIR)/pots
	@echo "Commands installed to $(BINDIR)"

uninstall: ## Remove installed commands
	@echo "Removing prunejuice commands from $(BINDIR)..."
	@rm -f $(BINDIR)/prunejuice-cli $(BINDIR)/prj $(BINDIR)/plum $(BINDIR)/pots
	@echo "Commands removed"
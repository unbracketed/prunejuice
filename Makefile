# Makefile for prunejuice project

.PHONY: help test-env test-env-clean install uninstall dev-link dev-unlink

# Default target - show help
help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

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
	@echo "Development symlinks created in /usr/local/bin/"

dev-unlink: ## Remove development symlinks
	@echo "Removing development symlinks..."
	@sudo rm -f /usr/local/bin/prunejuice-cli /usr/local/bin/prj /usr/local/bin/plum
	@echo "Development symlinks removed"

install: ## Install commands to system PATH
	@echo "Installing prunejuice commands to $(BINDIR)..."
	@mkdir -p $(BINDIR)
	@install -m 755 scripts/prunejuice-cli.sh $(BINDIR)/prunejuice-cli
	@ln -sf $(BINDIR)/prunejuice-cli $(BINDIR)/prj
	@install -m 755 scripts/plum/plum $(BINDIR)/plum
	@echo "Commands installed to $(BINDIR)"

uninstall: ## Remove installed commands
	@echo "Removing prunejuice commands from $(BINDIR)..."
	@rm -f $(BINDIR)/prunejuice-cli $(BINDIR)/prj $(BINDIR)/plum
	@echo "Commands removed"
# Makefile for prunejuice project

.PHONY: help test-env test-env-clean

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
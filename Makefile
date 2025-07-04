.PHONY: install
install: ## Install the virtual environment and install the pre-commit hooks
	@echo "🚀 Creating virtual environment using uv"
	@uv sync
	@uv run pre-commit install

.PHONY: check
check: ## Run code quality tools.
	@echo "🚀 Checking lock file consistency with 'pyproject.toml'"
	@uv lock --locked
	@echo "🚀 Linting code: Running pre-commit"
	@uv run pre-commit run -a
	@echo "🚀 Static type checking: Running mypy"
	@uv run mypy
	@echo "🚀 Checking for obsolete dependencies: Running deptry"
	@uv run deptry src

.PHONY: test
test: ## Test the code with pytest
	@echo "🚀 Testing code: Running pytest"
	@uv run python -m pytest --cov --cov-config=pyproject.toml --cov-report=xml

.PHONY: build
build: clean-build ## Build wheel file
	@echo "🚀 Creating wheel file"
	@uvx --from build pyproject-build --installer uv

.PHONY: clean-build
clean-build: ## Clean build artifacts
	@echo "🚀 Removing build artifacts"
	@uv run python -c "import shutil; import os; shutil.rmtree('dist') if os.path.exists('dist') else None"

.PHONY: publish
publish: ## Publish a release to PyPI.
	@echo "🚀 Publishing."
	@uvx twine upload --repository-url https://upload.pypi.org/legacy/ dist/*

.PHONY: build-and-publish
build-and-publish: build publish ## Build and publish.

.PHONY: docs-test
docs-test: ## Test if documentation can be built without warnings or errors
	@uv run mkdocs build -s

.PHONY: docs
docs: ## Build and serve the documentation
	@uv run mkdocs serve

.PHONY: dump-project-db-tables
dump-project-db-tables: ## Dump all contents from projects, workspaces, and events tables
	@echo "📊 Dumping database tables..."
	@echo "=== PROJECTS TABLE ==="
	@uv run python -c "from pathlib import Path; from prunejuice.core.database.manager import Database; db = Database(Path('.prj/prunejuice.db')); exec('with db.connection() as conn: cursor = conn.cursor(); cursor.execute(\"SELECT * FROM projects\"); rows = cursor.fetchall()\nfor row in rows: print(row)')"
	@echo "\n=== WORKSPACES TABLE ==="
	@uv run python -c "from pathlib import Path; from prunejuice.core.database.manager import Database; db = Database(Path('.prj/prunejuice.db')); exec('with db.connection() as conn: cursor = conn.cursor(); cursor.execute(\"SELECT * FROM workspaces\"); rows = cursor.fetchall()\nfor row in rows: print(row)')"
	@echo "\n=== EVENTS TABLE ==="
	@uv run python -c "from pathlib import Path; from prunejuice.core.database.manager import Database; db = Database(Path('.prj/prunejuice.db')); exec('with db.connection() as conn: cursor = conn.cursor(); cursor.execute(\"SELECT * FROM event_log\"); rows = cursor.fetchall()\nfor row in rows: print(row)')"

.PHONY: help
help:
	@uv run python -c "import re; \
	[[print(f'\033[36m{m[0]:<20}\033[0m {m[1]}') for m in re.findall(r'^([a-zA-Z_-]+):.*?## (.*)$$', open(makefile).read(), re.M)] for makefile in ('$(MAKEFILE_LIST)').strip().split()]"

.DEFAULT_GOAL := help

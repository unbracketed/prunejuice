#!/bin/bash
set -euo pipefail

# PruneJuice Python Installation Script
# This script installs PruneJuice using uv for global usage

echo "🧃 Installing PruneJuice Python Implementation..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed. Please install uv first:"
    echo "curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Check if we're in the right directory
if [[ ! -f "pyproject.toml" ]]; then
    echo "❌ Error: This script must be run from the PruneJuice Python project directory"
    exit 1
fi

# Install globally using uvx
echo "📦 Installing PruneJuice globally..."
uvx install .

# Verify installation
if command -v prj &> /dev/null; then
    echo "✅ PruneJuice installed successfully!"
    echo ""
    echo "📋 Usage:"
    echo "  prj init                    # Initialize a project"
    echo "  prj list-commands          # List available commands"
    echo "  prj run <command> [args]   # Run a command"
    echo "  prj status                 # Show project status"
    echo ""
    echo "🔗 Integration:"
    echo "  Make sure 'plum' and 'pots' tools are in your PATH for full functionality"
    echo ""
    echo "📚 Documentation: https://github.com/your-org/prunejuice"
else
    echo "❌ Installation failed. Please check for errors above."
    exit 1
fi
from pathlib import Path

import typer
from rich.console import Console

from prunejuice.core.database.manager import Database

app = typer.Typer()

console = Console()


@app.command("init")
def init():
    """Initialize a new PruneJuice project in the current directory."""
    path = Path.cwd()

    console.print("🧃 Initializing PruneJuice project...", style="bold green")

    # Create project structure
    prj_dir = path / ".prj"
    prj_dir.mkdir(exist_ok=True)
    (prj_dir / "actions").mkdir(exist_ok=True)
    (prj_dir / "artifacts").mkdir(exist_ok=True)

    # Initialize database
    try:
        db = Database(prj_dir / "prunejuice.db")
        db.initialize()
        console.print("Database initialized", style="dim")
    except Exception as e:
        console.print(f"Warning: Database initialization failed: {e}", style="yellow")

    # Gather project info
    # slugify project name
    # add options
    # Need Git interface
    # db.insert_project()
    # db.insert_workspace()

    console.print("✅ Project initialized successfully!", style="bold green")


@app.command("status")
def status():
    """Show the current status of the PruneJuice project."""
    path = Path.cwd()
    prj_dir = path / ".prj"

    if not prj_dir.exists():
        console.print("❌ No PruneJuice project found in current directory", style="red")
        console.print("Run 'prunejuice init' to initialize a project", style="dim")
        return

    console.print("✅ PruneJuice project found", style="green")
    console.print(f"Project directory: {prj_dir}", style="dim")


if __name__ == "__main__":
    app()

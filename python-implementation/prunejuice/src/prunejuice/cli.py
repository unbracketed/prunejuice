"""CLI interface for PruneJuice using Typer."""

import typer
from rich.console import Console
from rich.table import Table
from pathlib import Path
from typing import Optional, List
import asyncio
import sys

from .core.config import Settings
from .core.database import Database
from .commands.loader import CommandLoader
from .utils.logging import setup_logging

# Create Typer app
app = typer.Typer(
    name="prunejuice",
    help="🧃 PruneJuice SDLC Orchestrator - Parallel Agentic Coding Workflow Manager",
    rich_markup_mode="rich"
)

console = Console()


@app.command()
def init(
    path: Path = typer.Argument(Path.cwd(), help="Project path to initialize")
):
    """Initialize a PruneJuice project."""
    console.print("🧃 Initializing PruneJuice project...", style="bold green")
    
    # Create project structure
    prj_dir = path / ".prj"
    prj_dir.mkdir(exist_ok=True)
    (prj_dir / "commands").mkdir(exist_ok=True)
    (prj_dir / "steps").mkdir(exist_ok=True)
    (prj_dir / "configs").mkdir(exist_ok=True)
    (prj_dir / "artifacts").mkdir(exist_ok=True)
    
    # Copy template commands
    try:
        from importlib import resources
        templates = resources.files("prunejuice.templates")
        for template_name in ["analyze-issue.yaml", "code-review.yaml", "feature-branch.yaml"]:
            try:
                template_path = templates / template_name
                if template_path.is_file():
                    (prj_dir / "commands" / template_name).write_text(
                        template_path.read_text()
                    )
            except Exception as e:
                console.print(f"Warning: Could not copy template {template_name}: {e}", style="yellow")
    except Exception as e:
        console.print(f"Warning: Could not load templates: {e}", style="yellow")
    
    # Initialize database
    try:
        settings = Settings()
        db = Database(prj_dir / "prunejuice.db")
        asyncio.run(db.initialize())
        console.print("Database initialized", style="dim")
    except Exception as e:
        console.print(f"Warning: Database initialization failed: {e}", style="yellow")
    
    console.print("✅ Project initialized successfully!", style="bold green")


@app.command()
def list_commands(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed info")
):
    """List available SDLC commands."""
    try:
        loader = CommandLoader()
        commands = asyncio.run(loader.discover_commands(Path.cwd()))
        
        if not commands:
            console.print("No commands found. Run 'prj init' first.", style="yellow")
            return
        
        table = Table(title="Available Commands")
        table.add_column("Command", style="cyan", no_wrap=True)
        table.add_column("Category", style="yellow")
        table.add_column("Description", style="green")
        
        if verbose:
            table.add_column("Steps", style="blue")
        
        for cmd in commands:
            row = [cmd.name, cmd.category, cmd.description]
            if verbose:
                steps = cmd.pre_steps + cmd.steps + cmd.post_steps
                row.append(f"{len(steps)} steps")
            table.add_row(*row)
        
        console.print(table)
        
    except Exception as e:
        console.print(f"❌ Error listing commands: {e}", style="bold red")
        raise typer.Exit(code=1)


@app.command()
def run(
    command: str = typer.Argument(help="Command name to execute"),
    args: Optional[List[str]] = typer.Argument(None, help="Command arguments in key=value format"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be executed"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output")
):
    """Run an SDLC command."""
    try:
        # Set up logging
        log_level = "DEBUG" if verbose else "INFO"
        setup_logging(level=log_level)
        
        console.print(f"🚀 Executing command: [bold cyan]{command}[/bold cyan]")
        
        # Import executor here to avoid circular imports
        from .core.executor import Executor
        
        settings = Settings()
        executor = Executor(settings)
        
        # Parse arguments
        parsed_args = {}
        for arg in args or []:
            if "=" in arg:
                key, value = arg.split("=", 1)
                parsed_args[key] = value
            else:
                console.print(f"❌ Invalid argument format: {arg}. Use key=value", style="bold red")
                raise typer.Exit(code=1)
        
        # Run command
        result = asyncio.run(
            executor.execute_command(command, Path.cwd(), parsed_args, dry_run)
        )
        
        if result.success:
            console.print("✅ Command completed successfully!", style="bold green")
            if result.artifacts_path:
                console.print(f"Artifacts stored in: {result.artifacts_path}", style="dim")
        else:
            console.print(f"❌ Command failed: {result.error}", style="bold red")
            raise typer.Exit(code=1)
            
    except Exception as e:
        console.print(f"❌ Error: {e}", style="bold red")
        if verbose:
            import traceback
            traceback.print_exc()
        raise typer.Exit(code=1)


@app.command()
def status():
    """Show PruneJuice project status."""
    try:
        settings = Settings()
        db = Database(settings.db_path)
        
        # Show project info
        console.print("📊 PruneJuice Project Status", style="bold")
        console.print(f"Project: {Path.cwd().name}")
        console.print(f"Database: {settings.db_path}")
        console.print(f"Artifacts: {settings.artifacts_dir}")
        
        # Show recent events
        events = asyncio.run(db.get_recent_events(limit=5))
        if events:
            table = Table(title="Recent Events")
            table.add_column("Command", style="cyan")
            table.add_column("Status", style="yellow")
            table.add_column("Start Time", style="green")
            table.add_column("Duration", style="blue")
            
            for event in events:
                # Calculate duration
                if event.end_time:
                    duration = event.end_time - event.start_time
                    duration_str = f"{duration.total_seconds():.1f}s"
                else:
                    duration_str = "running"
                
                # Format status with color
                status_style = {
                    "completed": "green",
                    "failed": "red",
                    "running": "yellow"
                }.get(event.status, "white")
                
                table.add_row(
                    event.command,
                    f"[{status_style}]{event.status}[/{status_style}]",
                    event.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                    duration_str
                )
            
            console.print(table)
        else:
            console.print("No recent events found.", style="dim")
            
        # Show active events
        active_events = asyncio.run(db.get_active_events())
        if active_events:
            console.print(f"\n🔄 Active Events: {len(active_events)}", style="bold yellow")
            for event in active_events:
                console.print(f"  - {event.command} (session: {event.session_id})")
        
    except Exception as e:
        console.print(f"❌ Error getting status: {e}", style="bold red")
        raise typer.Exit(code=1)


@app.command()
def cleanup(
    days: int = typer.Option(30, help="Clean up artifacts older than N days"),
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation")
):
    """Clean up old artifacts and sessions."""
    try:
        settings = Settings()
        
        if not confirm:
            response = typer.confirm(f"Clean up artifacts older than {days} days?")
            if not response:
                console.print("Cleanup cancelled.", style="yellow")
                return
        
        from .utils.artifacts import ArtifactStore
        artifact_store = ArtifactStore(settings.artifacts_dir)
        artifact_store.cleanup_old_sessions(days)
        
        console.print(f"✅ Cleaned up artifacts older than {days} days", style="bold green")
        
    except Exception as e:
        console.print(f"❌ Error during cleanup: {e}", style="bold red")
        raise typer.Exit(code=1)


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
from pathlib import Path

import typer
from rich.console import Console
from slugify import slugify

from prunejuice.core.database.manager import Database
from prunejuice.core.git_ops import GitManager
from prunejuice.core.models import Project, Workspace

app = typer.Typer()

console = Console()


@app.command("init")
def init(name: str = typer.Argument(None, help="Name for the project")):
    """Initialize a new PruneJuice project in the current directory."""
    current_path = Path.cwd()

    # Check Git repository status and determine project directory
    git_manager = GitManager(current_path)
    git_init_head_ref = None
    git_init_branch = None

    if git_manager.is_git_repository():
        # Use Git repository root as project directory
        path = git_manager.get_repository_root()
        git_init_branch = git_manager.get_current_branch()
        git_init_head_ref = git_manager.get_head_commit_sha()
        console.print(f"Git repository detected (branch: {git_init_branch})", style="dim")
        console.print(f"Using Git repository root: {path}", style="dim")
    else:
        # Use current directory if no Git repository
        path = current_path
        console.print("No Git repository found", style="dim yellow")

    # Determine project name
    if name is None:
        # Use the project directory name as default
        name = path.name

    project_slug = slugify(name)

    console.print(f"🧃 Initializing PruneJuice project: [bold]{name}[/bold]", style="bold green")

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
        raise typer.Exit(1) from e

    # Insert project into database
    try:
        worktree_path = path / ".worktrees"
        project_id = db.insert_project(
            name=name,
            slug=project_slug,
            path=str(path),
            worktree_path=str(worktree_path),
            git_init_head_ref=git_init_head_ref,
            git_init_branch=git_init_branch,
        )
        console.print(f"Project '{name}' registered (ID: {project_id})", style="dim")

        # Insert initial workspace (only if git repository exists)
        if git_init_branch:
            workspace_id = db.insert_workspace(
                name="main",
                slug="main",
                project_id=project_id,
                path=str(path),
                git_branch=git_init_branch,
                git_origin_branch=f"origin/{git_init_branch}",
            )
            console.print(f"Main workspace created (ID: {workspace_id})", style="dim")

    except Exception as e:
        console.print(f"Error: Failed to register project: {e}", style="red")
        raise typer.Exit(1) from e

    console.print("✅ Project initialized successfully!", style="bold green")


@app.command("status")
def status() -> Project:
    """Show the current status of the PruneJuice project."""
    path = Path.cwd()

    # Check if we're in a Git repository and use its root, otherwise use current directory
    git_manager = GitManager(path)
    project_path = git_manager.get_repository_root() if git_manager.is_git_repository() else path

    prj_dir = project_path / ".prj"

    if not prj_dir.exists():
        console.print("❌ No PruneJuice project found in current directory", style="red")
        console.print("Run 'prunejuice init' to initialize a project", style="dim")
        raise typer.Exit(1)

    # Use the path to lookup the Project in the `projects` table
    db = Database(prj_dir / "prunejuice.db")
    project_data = db.get_project_by_path(str(project_path))

    if not project_data:
        console.print("❌ Project not found in database", style="red")
        console.print("The .prj directory exists but no project is registered", style="dim")
        raise typer.Exit(1)

    # Create Project instance from database data
    project = Project(**project_data)

    # Get workspaces for this project
    workspaces_data = db.get_workspaces_by_project_id(project.id)
    workspaces = [Workspace(**workspace_data) for workspace_data in workspaces_data]

    # Display project status
    console.print("✅ PruneJuice project found", style="green")
    console.print(f"Project: [bold]{project.name}[/bold] (ID: {project.id})")
    console.print(f"Path: {project.path}")
    console.print(f"Slug: {project.slug}")
    if project.git_init_branch:
        console.print(f"Git branch: {project.git_init_branch}")
    if project.date_created:
        console.print(f"Created: {project.date_created}")

    # Display workspaces
    if workspaces:
        console.print(f"\nWorkspaces ({len(workspaces)}):", style="bold")
        for workspace in workspaces:
            console.print(f"  • {workspace.name} (ID: {workspace.id}) - {workspace.git_branch}")
    else:
        console.print("\nNo workspaces found", style="dim")

    return project


if __name__ == "__main__":
    app()

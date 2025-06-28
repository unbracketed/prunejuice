# PruneJuice Python Implementation Plan

**Date**: 2025-06-28  
**Status**: ACTIVE PLAN  
**Target**: Python 3.11+ with uv/uvx  

## Executive Summary

This plan outlines a clean Python implementation of PruneJuice's orchestration layer, designed as a simple prototype that executes command steps sequentially. The parallel coding capabilities come from running multiple agents in different git worktrees, not from parallel step execution. The `plum` and `pots` tools remain as lightweight shell utilities.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                   prunejuice (Python)                    │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐ │
│  │ CLI Layer   │  │ Orchestrator │  │ State Manager  │ │
│  │ (Typer)     │  │   Engine     │  │  (SQLite)     │ │
│  └─────────────┘  └──────────────┘  └────────────────┘ │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐ │
│  │ YAML Parser │  │ Task Runner  │  │ Artifact Store │ │
│  │ (Pydantic)  │  │ (sequential) │  │                │ │
│  └─────────────┘  └──────────────┘  └────────────────┘ │
└─────────────────────────┬───────────────────────────────┘
                          │ subprocess calls
         ┌────────────────┴────────────────┐
         │                                 │
    ┌────┴────┐                      ┌────┴────┐
    │  plum   │                      │  pots   │
    │ (shell) │                      │ (shell) │
    └─────────┘                      └─────────┘
```

## Technology Stack

### Core Dependencies
```toml
[project]
name = "prunejuice"
version = "0.5.0"
description = "Parallel agentic coding workflow orchestrator"
requires-python = ">=3.11"
dependencies = [
    "typer[all]>=0.12.0",      # CLI framework with rich formatting
    "pydantic>=2.5.0",         # Data validation and settings
    "pyyaml>=6.0",             # YAML parsing
    "aiosqlite>=0.19.0",       # Async SQLite operations
    "rich>=13.0.0",            # Beautiful terminal output
    "python-dotenv>=1.0.0",    # Environment variable management
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "mypy>=1.8.0",
    "ruff>=0.1.0",
]

[project.scripts]
prj = "prunejuice.cli:app"
prunejuice = "prunejuice.cli:app"
```

### Project Structure
```
prunejuice/
├── pyproject.toml
├── README.md
├── src/
│   └── prunejuice/
│       ├── __init__.py
│       ├── cli.py              # Typer CLI entry point
│       ├── core/
│       │   ├── __init__.py
│       │   ├── config.py       # Pydantic settings
│       │   ├── database.py     # SQLite with proper bindings
│       │   ├── executor.py     # Sequential task execution
│       │   ├── models.py       # Pydantic data models
│       │   └── state.py        # State management
│       ├── commands/
│       │   ├── __init__.py
│       │   ├── base.py         # Base command class
│       │   ├── analyze.py      # analyze-issue implementation
│       │   └── loader.py       # YAML command loader
│       ├── integrations/
│       │   ├── __init__.py
│       │   ├── plum.py         # Plum tool integration
│       │   ├── pots.py         # Pots tool integration
│       │   └── github.py       # GitHub API integration
│       ├── utils/
│       │   ├── __init__.py
│       │   ├── artifacts.py    # Artifact storage
│       │   ├── context.py      # Context gathering
│       │   └── logging.py      # Structured logging
│       └── templates/           # Command templates
│           ├── analyze-issue.yaml
│           ├── code-review.yaml
│           └── feature-branch.yaml
├── tests/
│   ├── conftest.py
│   ├── test_cli.py
│   ├── test_executor.py
│   └── test_integrations.py
└── scripts/
    └── install.sh              # uv-based installer
```

## Implementation Approach

### Phase 1: Core Foundation

#### 1.1 Project Setup
```bash
# Initialize with uv
uv init prunejuice-python
cd prunejuice-python
uv add typer rich pydantic pyyaml aiosqlite python-dotenv
uv add --dev pytest pytest-asyncio pytest-cov mypy ruff
```

#### 1.2 Core Models and Configuration
```python
# src/prunejuice/core/models.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class CommandArgument(BaseModel):
    name: str
    required: bool = True
    type: str = "string"
    default: Optional[Any] = None
    description: Optional[str] = None

class CommandStep(BaseModel):
    name: str
    args: Dict[str, Any] = Field(default_factory=dict)
    script: Optional[str] = None
    timeout: int = 300

class CommandDefinition(BaseModel):
    name: str
    description: str
    extends: Optional[str] = None
    category: str = "workflow"
    arguments: List[CommandArgument] = Field(default_factory=list)
    environment: Dict[str, str] = Field(default_factory=dict)
    pre_steps: List[str] = Field(default_factory=list)
    steps: List[str] = Field(default_factory=list)
    post_steps: List[str] = Field(default_factory=list)
    cleanup_on_failure: List[str] = Field(default_factory=list)
    working_directory: Optional[str] = None
    timeout: int = 1800

class ExecutionEvent(BaseModel):
    id: Optional[int] = None
    command: str
    project_path: str
    worktree_name: Optional[str] = None
    session_id: str
    artifacts_path: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    status: str = "running"
    exit_code: Optional[int] = None
    error_message: Optional[str] = None
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
```

#### 1.3 Database Layer with Secure Bindings
```python
# src/prunejuice/core/database.py
import aiosqlite
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    @asynccontextmanager
    async def connection(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA foreign_keys = ON")
            yield db
    
    async def initialize(self):
        """Initialize database with schema"""
        schema_path = Path(__file__).parent.parent / "schema.sql"
        async with self.connection() as db:
            with open(schema_path) as f:
                await db.executescript(f.read())
            await db.commit()
    
    async def start_event(
        self,
        command: str,
        project_path: str,
        session_id: str,
        artifacts_path: str,
        worktree_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """Create new event with proper parameter binding"""
        async with self.connection() as db:
            cursor = await db.execute(
                """
                INSERT INTO events 
                (command, project_path, worktree_name, session_id, 
                 artifacts_path, metadata)
                VALUES (?, ?, ?, ?, ?, json(?))
                """,
                (command, project_path, worktree_name, session_id,
                 artifacts_path, json.dumps(metadata or {}))
            )
            await db.commit()
            return cursor.lastrowid
    
    async def end_event(
        self,
        event_id: int,
        status: str,
        exit_code: int,
        error_message: Optional[str] = None
    ):
        """Update event status with secure parameters"""
        async with self.connection() as db:
            await db.execute(
                """
                UPDATE events 
                SET status = ?, exit_code = ?, error_message = ?,
                    end_time = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (status, exit_code, error_message, event_id)
            )
            await db.commit()
```

### Phase 2: CLI and Command Framework

#### 2.1 Main CLI Application
```python
# src/prunejuice/cli.py
import typer
from rich.console import Console
from rich.table import Table
from pathlib import Path
from typing import Optional, List
import asyncio

from .core.config import Settings
from .core.executor import Executor
from .commands.loader import CommandLoader
from .utils.logging import setup_logging

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
    """Initialize a PruneJuice project"""
    console.print("🧃 Initializing PruneJuice project...", style="bold green")
    
    # Create project structure
    prj_dir = path / ".prj"
    prj_dir.mkdir(exist_ok=True)
    (prj_dir / "commands").mkdir(exist_ok=True)
    (prj_dir / "steps").mkdir(exist_ok=True)
    (prj_dir / "configs").mkdir(exist_ok=True)
    
    # Copy template commands
    from importlib import resources
    templates = resources.files("prunejuice.templates")
    for template in ["analyze-issue.yaml", "code-review.yaml", "feature-branch.yaml"]:
        if (template_path := templates / template).is_file():
            (prj_dir / "commands" / template).write_text(
                template_path.read_text()
            )
    
    console.print("✅ Project initialized successfully!", style="bold green")

@app.command()
def list(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed info")
):
    """List available SDLC commands"""
    loader = CommandLoader()
    commands = asyncio.run(loader.discover_commands(Path.cwd()))
    
    table = Table(title="Available Commands")
    table.add_column("Command", style="cyan", no_wrap=True)
    table.add_column("Category", style="yellow")
    table.add_column("Description", style="green")
    
    for cmd in commands:
        table.add_row(cmd.name, cmd.category, cmd.description)
    
    console.print(table)

@app.command()
def run(
    command: str,
    args: Optional[List[str]] = typer.Argument(None, help="Command arguments"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be executed")
):
    """Run an SDLC command"""
    console.print(f"🚀 Executing command: [bold cyan]{command}[/bold cyan]")
    
    settings = Settings()
    executor = Executor(settings)
    
    # Parse arguments
    parsed_args = {}
    for arg in args or []:
        if "=" in arg:
            key, value = arg.split("=", 1)
            parsed_args[key] = value
    
    # Run command
    try:
        result = asyncio.run(
            executor.execute_command(command, Path.cwd(), parsed_args, dry_run)
        )
        if result.success:
            console.print("✅ Command completed successfully!", style="bold green")
        else:
            console.print(f"❌ Command failed: {result.error}", style="bold red")
            raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"❌ Error: {e}", style="bold red")
        raise typer.Exit(code=1)

@app.command()
def status():
    """Show PruneJuice project status"""
    from .core.database import Database
    from .core.config import Settings
    
    settings = Settings()
    db = Database(settings.db_path)
    
    # Show project info
    console.print("📊 PruneJuice Project Status", style="bold")
    console.print(f"Project: {Path.cwd().name}")
    console.print(f"Database: {settings.db_path}")
    
    # Show recent events
    events = asyncio.run(db.get_recent_events(limit=5))
    if events:
        table = Table(title="Recent Events")
        table.add_column("Command", style="cyan")
        table.add_column("Status", style="yellow")
        table.add_column("Start Time", style="green")
        
        for event in events:
            table.add_row(event.command, event.status, str(event.start_time))
        
        console.print(table)
```

#### 2.2 Command Execution Engine (Simplified)
```python
# src/prunejuice/core/executor.py
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import subprocess
import json
import logging

from .database import Database
from .models import CommandDefinition, ExecutionEvent, StepStatus
from .state import StateManager
from ..commands.loader import CommandLoader
from ..integrations.plum import PlumIntegration
from ..integrations.pots import PotsIntegration
from ..utils.artifacts import ArtifactStore

logger = logging.getLogger(__name__)

class StepExecutor:
    """Executes individual steps with proper isolation"""
    
    def __init__(self, builtin_steps: Dict[str, callable]):
        self.builtin_steps = builtin_steps
    
    async def execute(
        self,
        step_name: str,
        context: Dict[str, Any],
        timeout: int = 300
    ) -> tuple[bool, str]:
        """Execute a step and return (success, output)"""
        if step_name in self.builtin_steps:
            # Execute built-in step
            try:
                result = await asyncio.wait_for(
                    self.builtin_steps[step_name](context),
                    timeout=timeout
                )
                return True, str(result)
            except asyncio.TimeoutError:
                return False, f"Step '{step_name}' timed out after {timeout}s"
            except Exception as e:
                return False, f"Step '{step_name}' failed: {e}"
        else:
            # Look for custom step script
            step_paths = [
                context['project_path'] / ".prj" / "steps" / f"{step_name}.py",
                context['project_path'] / ".prj" / "steps" / f"{step_name}.sh",
            ]
            
            for step_path in step_paths:
                if step_path.exists():
                    return await self._execute_script(step_path, context, timeout)
            
            return False, f"Step '{step_name}' not found"
    
    async def _execute_script(
        self,
        script_path: Path,
        context: Dict[str, Any],
        timeout: int
    ) -> tuple[bool, str]:
        """Execute external script with context"""
        env = os.environ.copy()
        
        # Add context to environment
        for key, value in context.items():
            if isinstance(value, (str, int, float, bool)):
                env[f"PRUNEJUICE_{key.upper()}"] = str(value)
        
        try:
            if script_path.suffix == ".py":
                cmd = ["python", str(script_path)]
            else:
                cmd = ["bash", str(script_path)]
            
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            
            stdout, _ = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout
            )
            
            return proc.returncode == 0, stdout.decode()
        except asyncio.TimeoutError:
            return False, f"Script timed out after {timeout}s"
        except Exception as e:
            return False, f"Script execution failed: {e}"

class Executor:
    """Main command orchestration engine - simple sequential execution"""
    
    def __init__(self, settings):
        self.settings = settings
        self.db = Database(settings.db_path)
        self.loader = CommandLoader()
        self.state = StateManager(self.db)
        self.artifacts = ArtifactStore(settings.artifacts_dir)
        self.plum = PlumIntegration()
        self.pots = PotsIntegration()
        
        # Register built-in steps
        self.step_executor = StepExecutor({
            "setup-environment": self._setup_environment,
            "validate-prerequisites": self._validate_prerequisites,
            "create-worktree": self._create_worktree,
            "start-session": self._start_session,
            "gather-context": self._gather_context,
            "store-artifacts": self._store_artifacts,
            "cleanup": self._cleanup,
        })
    
    async def execute_command(
        self,
        command_name: str,
        project_path: Path,
        args: Dict[str, Any],
        dry_run: bool = False
    ) -> ExecutionResult:
        """Execute a command with full lifecycle management"""
        # Load command definition
        command = await self.loader.load_command(command_name, project_path)
        if not command:
            return ExecutionResult(
                success=False,
                error=f"Command '{command_name}' not found"
            )
        
        # Validate arguments
        validation_errors = self._validate_arguments(command, args)
        if validation_errors:
            return ExecutionResult(
                success=False,
                error=f"Invalid arguments: {', '.join(validation_errors)}"
            )
        
        # Create execution context
        session_id = f"{project_path.name}-{datetime.now().timestamp()}"
        artifact_dir = self.artifacts.create_session_dir(
            project_path, session_id, command_name
        )
        
        context = {
            'command': command,
            'project_path': project_path,
            'session_id': session_id,
            'artifact_dir': artifact_dir,
            'args': args,
            'environment': {**os.environ, **command.environment},
        }
        
        if dry_run:
            return self._dry_run(command, context)
        
        # Start event tracking
        event_id = await self.db.start_event(
            command=command_name,
            project_path=str(project_path),
            session_id=session_id,
            artifacts_path=str(artifact_dir)
        )
        context['event_id'] = event_id
        
        # Execute command with simple sequential execution
        try:
            # Execute all steps sequentially
            all_steps = command.pre_steps + command.steps + command.post_steps
            
            for i, step in enumerate(all_steps):
                logger.info(f"Executing step {i+1}/{len(all_steps)}: {step}")
                
                await self.state.begin_step(session_id, step)
                success, output = await self.step_executor.execute(
                    step, context, command.timeout
                )
                
                if success:
                    await self.state.complete_step(session_id, step)
                else:
                    await self.state.fail_step(session_id, step, output)
                    raise StepError(f"Step '{step}' failed: {output}")
            
            # Mark success
            await self.db.end_event(event_id, "completed", 0)
            return ExecutionResult(success=True)
            
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            
            # Run cleanup steps
            for step in command.cleanup_on_failure:
                try:
                    await self.step_executor.execute(step, context, 60)
                except Exception:
                    logger.error(f"Cleanup step '{step}' failed")
            
            # Mark failure
            await self.db.end_event(event_id, "failed", 1, str(e))
            return ExecutionResult(success=False, error=str(e))
    
    # Built-in step implementations
    async def _setup_environment(self, context: Dict[str, Any]) -> str:
        """Setup execution environment"""
        artifact_dir = context['artifact_dir']
        artifact_dir.mkdir(parents=True, exist_ok=True)
        (artifact_dir / "logs").mkdir(exist_ok=True)
        (artifact_dir / "outputs").mkdir(exist_ok=True)
        return "Environment setup complete"
    
    async def _create_worktree(self, context: Dict[str, Any]) -> str:
        """Create worktree via plum integration"""
        branch_name = context['args'].get(
            'branch_name',
            f"pj-{context['command'].name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        )
        
        worktree_path = await self.plum.create_worktree(
            context['project_path'],
            branch_name
        )
        
        context['worktree_path'] = worktree_path
        context['branch_name'] = branch_name
        return f"Created worktree at {worktree_path}"
    
    async def _start_session(self, context: Dict[str, Any]) -> str:
        """Start tmux session via pots integration"""
        session_name = await self.pots.create_session(
            context.get('worktree_path', context['project_path']),
            context['command'].name
        )
        
        context['tmux_session'] = session_name
        return f"Started tmux session: {session_name}"
```

### Phase 3: Tool Integrations

#### 3.1 Plum Integration
```python
# src/prunejuice/integrations/plum.py
import subprocess
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class PlumIntegration:
    """Integration with plum worktree manager"""
    
    def __init__(self, plum_path: Optional[Path] = None):
        self.plum_path = plum_path or self._find_plum()
    
    def _find_plum(self) -> Optional[Path]:
        """Find plum executable in standard locations"""
        locations = [
            Path.cwd() / "scripts" / "plum-cli.sh",
            Path.home() / ".local" / "bin" / "plum",
            Path("/usr/local/bin/plum"),
        ]
        
        for loc in locations:
            if loc.exists() and loc.is_file():
                return loc
        
        # Try which
        try:
            result = subprocess.run(
                ["which", "plum"],
                capture_output=True,
                text=True,
                check=True
            )
            return Path(result.stdout.strip())
        except subprocess.CalledProcessError:
            return None
    
    async def create_worktree(
        self,
        project_path: Path,
        branch_name: str
    ) -> Path:
        """Create a new worktree and return its path"""
        if not self.plum_path:
            logger.warning("Plum not found, using fallback")
            return project_path
        
        try:
            result = subprocess.run(
                [str(self.plum_path), "create", branch_name],
                cwd=project_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse worktree path from output
            for line in result.stdout.splitlines():
                if "Worktree created at:" in line:
                    return Path(line.split(":", 1)[1].strip())
            
            return project_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Plum create failed: {e.stderr}")
            raise RuntimeError(f"Failed to create worktree: {e.stderr}")
    
    async def list_worktrees(self, project_path: Path) -> List[Dict[str, Any]]:
        """List all worktrees for the project"""
        if not self.plum_path:
            return []
        
        try:
            result = subprocess.run(
                [str(self.plum_path), "list", "--json"],
                cwd=project_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            return json.loads(result.stdout)
            
        except subprocess.CalledProcessError:
            return []
```

#### 3.2 Pots Integration
```python
# src/prunejuice/integrations/pots.py
import subprocess
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class PotsIntegration:
    """Integration with pots tmux session manager"""
    
    def __init__(self, pots_path: Optional[Path] = None):
        self.pots_path = pots_path or self._find_pots()
    
    def _find_pots(self) -> Optional[Path]:
        """Find pots executable"""
        locations = [
            Path.cwd() / "scripts" / "pots" / "pots",
            Path.home() / ".local" / "bin" / "pots",
        ]
        
        for loc in locations:
            if loc.exists():
                return loc
        
        return None
    
    async def create_session(
        self,
        working_dir: Path,
        task_name: str
    ) -> str:
        """Create a new tmux session"""
        if not self.pots_path:
            logger.warning("Pots not found, skipping session creation")
            return f"prunejuice-{task_name}"
        
        try:
            result = subprocess.run(
                [str(self.pots_path), "create", str(working_dir), task_name],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse session name from output
            for line in result.stdout.splitlines():
                if "Session created:" in line:
                    return line.split(":", 1)[1].strip()
            
            return f"prunejuice-{task_name}"
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Pots create failed: {e.stderr}")
            # Don't fail the whole operation if tmux isn't available
            return f"prunejuice-{task_name}"
```

### Phase 4: Testing

#### 4.1 Test Suite
```python
# tests/test_executor.py
import pytest
from pathlib import Path
from prunejuice.core.executor import Executor
from prunejuice.core.models import CommandDefinition

@pytest.fixture
async def executor(tmp_path):
    """Create executor with test database"""
    settings = Settings(
        db_path=tmp_path / "test.db",
        artifacts_dir=tmp_path / "artifacts"
    )
    executor = Executor(settings)
    await executor.db.initialize()
    return executor

@pytest.fixture
def sample_command():
    """Sample command for testing"""
    return CommandDefinition(
        name="test-command",
        description="Test command",
        arguments=[
            CommandArgument(name="input", required=True)
        ],
        steps=["validate-prerequisites", "store-artifacts"]
    )

@pytest.mark.asyncio
async def test_execute_command_success(executor, sample_command, tmp_path):
    """Test successful command execution"""
    # Create command file
    cmd_dir = tmp_path / ".prj" / "commands"
    cmd_dir.mkdir(parents=True)
    (cmd_dir / "test-command.yaml").write_text(
        sample_command.model_dump_yaml()
    )
    
    # Execute
    result = await executor.execute_command(
        "test-command",
        tmp_path,
        {"input": "test-value"}
    )
    
    assert result.success
    assert not result.error

@pytest.mark.asyncio
async def test_sql_injection_protection(executor):
    """Verify SQL injection is prevented"""
    # Attempt SQL injection via event tracking
    malicious_input = "'; DROP TABLE events; --"
    
    event_id = await executor.db.start_event(
        command=malicious_input,
        project_path="/tmp",
        session_id="test",
        artifacts_path="/tmp"
    )
    
    # Verify table still exists
    async with executor.db.connection() as conn:
        cursor = await conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='events'"
        )
        assert await cursor.fetchone() is not None
```

### Phase 5: Future Features

#### 5.1 MCP Server Mode Support
```python
# src/prunejuice/mcp/server.py
from typing import Dict, Any
import json

class MCPServer:
    """Model Context Protocol server for Claude Code integration"""
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP requests from Claude Code"""
        method = request.get("method")
        params = request.get("params", {})
        
        if method == "listCommands":
            return await self._list_commands()
        elif method == "executeCommand":
            return await self._execute_command(params)
        elif method == "getContext":
            return await self._get_context(params)
        else:
            return {"error": f"Unknown method: {method}"}
```

## Installation and Usage

### Installation via uvx
```bash
# Install globally
uvx install prunejuice

# Or run directly
uvx prunejuice init
```

### Basic Usage
```bash
# Initialize project
prj init

# List commands
prj list

# Run a command
prj run analyze-issue issue_number=123

# Check status
prj status
```

### Creating Custom Commands
```yaml
# .prj/commands/my-workflow.yaml
name: my-workflow
description: Custom workflow example
category: custom
arguments:
  - name: target
    required: true
    description: Target to process
steps:
  - validate-prerequisites
  - create-worktree
  - name: custom-step
    script: |
      echo "Processing ${PRUNEJUICE_ARG_TARGET}"
  - store-artifacts
```

## Security Improvements

1. **SQL Injection Prevention**: All database queries use parameter binding
2. **No eval() Usage**: Commands are parsed as structured YAML, not executed as code
3. **Input Validation**: Pydantic models validate all inputs
4. **Subprocess Safety**: Proper argument escaping for all subprocess calls
5. **Path Traversal Protection**: All file operations validate paths

## Performance Considerations

1. **Async Operations**: Database and I/O operations are async
2. **Connection Pooling**: SQLite connections are properly managed
3. **Lazy Loading**: Commands are loaded on-demand
4. **Streaming Logs**: Large outputs are streamed, not buffered

## Development Approach

This is a new implementation, not a migration. The Python version will be developed as a clean prototype with:

1. **Simple sequential execution**: Commands steps run one after another
2. **Clear separation**: The "parallel" aspect refers to multiple agents in different worktrees, not step execution
3. **Iterative development**: Start simple, add features as needed
4. **No backward compatibility burden**: Fresh start allows clean design

## Success Metrics

- Zero SQL injection vulnerabilities
- 90%+ test coverage
- Sub-second command startup time
- Full CLI compatibility with shell version
- Successful integration with plum/pots

## Conclusion

This Python implementation provides a clean, simple foundation for PruneJuice as a prototype. By focusing on sequential step execution and clear separation of concerns, we avoid unnecessary complexity while maintaining the ability to run multiple coding agents in parallel across different worktrees. The design prioritizes simplicity and security, making it easy to iterate and add features as needed.
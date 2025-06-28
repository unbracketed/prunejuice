"""Tests for command executor."""

import pytest
from pathlib import Path
import yaml

from prunejuice.core.executor import Executor
from prunejuice.core.models import CommandDefinition, CommandArgument, ExecutionResult


@pytest.mark.asyncio
async def test_execute_simple_command(test_executor, test_project, sample_command):
    """Test execution of a simple command."""
    # Create command file
    cmd_dir = test_project / ".prj" / "commands"
    cmd_file = cmd_dir / "test-command.yaml"
    
    with open(cmd_file, 'w') as f:
        yaml.dump(sample_command.model_dump(), f)
    
    # Execute command
    result = await test_executor.execute_command(
        "test-command",
        test_project,
        {"input": "test-value"}
    )
    
    assert isinstance(result, ExecutionResult)
    assert result.success
    assert result.artifacts_path is not None


@pytest.mark.asyncio
async def test_missing_required_argument(test_executor, test_project, sample_command):
    """Test validation of required arguments."""
    # Create command file
    cmd_dir = test_project / ".prj" / "commands"
    cmd_file = cmd_dir / "test-command.yaml"
    
    with open(cmd_file, 'w') as f:
        yaml.dump(sample_command.model_dump(), f)
    
    # Execute without required argument
    result = await test_executor.execute_command(
        "test-command",
        test_project,
        {}  # Missing required 'input' argument
    )
    
    assert not result.success
    assert "Required argument 'input' missing" in result.error


@pytest.mark.asyncio
async def test_nonexistent_command(test_executor, test_project):
    """Test execution of non-existent command."""
    result = await test_executor.execute_command(
        "nonexistent-command",
        test_project,
        {}
    )
    
    assert not result.success
    assert "Command 'nonexistent-command' not found" in result.error


@pytest.mark.asyncio
async def test_dry_run(test_executor, test_project, sample_command):
    """Test dry run functionality."""
    # Create command file
    cmd_dir = test_project / ".prj" / "commands"
    cmd_file = cmd_dir / "test-command.yaml"
    
    with open(cmd_file, 'w') as f:
        yaml.dump(sample_command.model_dump(), f)
    
    # Execute dry run
    result = await test_executor.execute_command(
        "test-command",
        test_project,
        {"input": "test-value"},
        dry_run=True
    )
    
    assert result.success
    assert "Dry run for command: test-command" in result.output
    assert "validate-prerequisites" in result.output
    assert "store-artifacts" in result.output


@pytest.mark.asyncio
async def test_step_failure_cleanup(test_executor, test_project):
    """Test cleanup execution when a step fails."""
    # Create command with failing step and cleanup
    failing_command = CommandDefinition(
        name="failing-command",
        description="Command that fails",
        steps=["nonexistent-step"],
        cleanup_on_failure=["cleanup"]
    )
    
    cmd_dir = test_project / ".prj" / "commands"
    cmd_file = cmd_dir / "failing-command.yaml"
    
    with open(cmd_file, 'w') as f:
        yaml.dump(failing_command.model_dump(), f)
    
    # Execute failing command
    result = await test_executor.execute_command(
        "failing-command",
        test_project,
        {}
    )
    
    assert not result.success
    assert "Step 'nonexistent-step' not found" in result.error


@pytest.mark.asyncio
async def test_built_in_steps(test_executor, test_project):
    """Test built-in step execution."""
    # Create command using built-in steps
    builtin_command = CommandDefinition(
        name="builtin-test",
        description="Test built-in steps",
        steps=[
            "setup-environment",
            "validate-prerequisites",
            "gather-context",
            "store-artifacts"
        ]
    )
    
    cmd_dir = test_project / ".prj" / "commands"
    cmd_file = cmd_dir / "builtin-test.yaml"
    
    with open(cmd_file, 'w') as f:
        yaml.dump(builtin_command.model_dump(), f)
    
    # Execute command
    result = await test_executor.execute_command(
        "builtin-test",
        test_project,
        {}
    )
    
    assert result.success


@pytest.mark.asyncio
async def test_environment_variables(test_executor, test_project):
    """Test environment variable handling."""
    # Create command with environment variables
    env_command = CommandDefinition(
        name="env-test",
        description="Test environment variables",
        environment={"TEST_VAR": "test_value"},
        steps=["setup-environment"]
    )
    
    cmd_dir = test_project / ".prj" / "commands"
    cmd_file = cmd_dir / "env-test.yaml"
    
    with open(cmd_file, 'w') as f:
        yaml.dump(env_command.model_dump(), f)
    
    # Execute command
    result = await test_executor.execute_command(
        "env-test",
        test_project,
        {}
    )
    
    assert result.success


@pytest.mark.asyncio
async def test_argument_injection_protection(test_executor, test_project, sample_command):
    """Test protection against argument injection."""
    # Create command file
    cmd_dir = test_project / ".prj" / "commands"
    cmd_file = cmd_dir / "test-command.yaml"
    
    with open(cmd_file, 'w') as f:
        yaml.dump(sample_command.model_dump(), f)
    
    # Try to inject malicious arguments
    malicious_args = {
        "input": "; rm -rf /; echo 'pwned'",
        "optional": "'; DROP TABLE events; --"
    }
    
    # Execute command - should not execute injection
    result = await test_executor.execute_command(
        "test-command",
        test_project,
        malicious_args
    )
    
    # Command should succeed (arguments are just data)
    assert result.success
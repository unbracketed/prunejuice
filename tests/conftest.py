import subprocess
import uuid

import pytest


@pytest.fixture
def mock_subprocess(mocker):
    """Mock subprocess.run for unit tests"""
    return mocker.patch("subprocess.run")


@pytest.fixture
def tmux_manager():
    """Default TmuxManager instance"""
    from prunejuice.core.tmux_ops import TmuxManager

    return TmuxManager()


@pytest.fixture
def custom_tmux_manager():
    """TmuxManager with custom server name"""
    from prunejuice.core.tmux_ops import TmuxManager

    return TmuxManager("test_server")


@pytest.fixture
def isolated_tmux_server():
    """Create isolated tmux server for testing"""
    server_name = f"test_{uuid.uuid4().hex[:8]}"
    yield server_name
    # Cleanup: kill test server
    subprocess.run(["tmux", f"-L{server_name}", "kill-server"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


@pytest.fixture
def tmux_test_session(isolated_tmux_server):
    """Create test session in isolated server"""
    session_name = f"session_{uuid.uuid4().hex[:8]}"
    # Create session
    subprocess.run(
        ["tmux", f"-L{isolated_tmux_server}", "new", "-d", "-s", session_name],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    yield {"server": isolated_tmux_server, "session": session_name}

    # Cleanup: kill session
    subprocess.run(
        ["tmux", f"-L{isolated_tmux_server}", "kill-session", "-t", session_name],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

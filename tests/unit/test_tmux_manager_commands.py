import subprocess


class TestTmuxManagerCommands:
    """Unit tests for TmuxManager._tmux_cmd method"""

    def test_tmux_cmd_single_argument(self, tmux_manager, mocker):
        """U04: Basic command construction with single argument"""
        # Arrange
        expected_process = subprocess.CompletedProcess(
            args=["tmux", "-Lprunejuice", "list-sessions"], returncode=0, stdout=b"session1: 1 windows\n", stderr=b""
        )
        mock_run = mocker.patch("prunejuice.core.tmux_ops.subprocess.run")
        mock_run.return_value = expected_process

        # Act
        result = tmux_manager._tmux_cmd("list-sessions")

        # Assert
        mock_run.assert_called_once_with(["tmux", "-Lprunejuice", "list-sessions"], capture_output=True, check=False)
        assert result == expected_process
        assert isinstance(result, subprocess.CompletedProcess)

    def test_tmux_cmd_multiple_arguments(self, tmux_manager, mocker):
        """U05: Multiple arguments"""
        # Arrange
        expected_process = subprocess.CompletedProcess(
            args=["tmux", "-Lprunejuice", "new", "-d", "-s", "test"], returncode=0, stdout=b"", stderr=b""
        )
        mock_run = mocker.patch("prunejuice.core.tmux_ops.subprocess.run")
        mock_run.return_value = expected_process

        # Act
        result = tmux_manager._tmux_cmd("new", "-d", "-s", "test")

        # Assert
        mock_run.assert_called_once_with(
            ["tmux", "-Lprunejuice", "new", "-d", "-s", "test"],
            capture_output=True,
            check=False,
        )
        assert result == expected_process
        assert isinstance(result, subprocess.CompletedProcess)

    def test_tmux_cmd_returns_completed_process(self, tmux_manager, mocker):
        """U06: Bug fix verification - ensure method returns CompletedProcess, not None"""
        # Arrange
        expected_process = subprocess.CompletedProcess(
            args=["tmux", "-Lprunejuice", "-V"], returncode=0, stdout=b"tmux 3.3a\n", stderr=b""
        )
        mock_run = mocker.patch("prunejuice.core.tmux_ops.subprocess.run")
        mock_run.return_value = expected_process

        # Act
        result = tmux_manager._tmux_cmd("-V")

        # Assert
        assert result is not None
        assert isinstance(result, subprocess.CompletedProcess)
        assert result.returncode == 0
        assert result.stdout == b"tmux 3.3a\n"
        assert result.stderr == b""

    def test_tmux_cmd_with_custom_server_name(self, custom_tmux_manager, mocker):
        """Test _tmux_cmd with custom server name"""
        # Arrange
        expected_process = subprocess.CompletedProcess(
            args=["tmux", "-Ltest_server", "list-sessions"], returncode=0, stdout=b"", stderr=b""
        )
        mock_run = mocker.patch("prunejuice.core.tmux_ops.subprocess.run")
        mock_run.return_value = expected_process

        # Act
        result = custom_tmux_manager._tmux_cmd("list-sessions")

        # Assert
        mock_run.assert_called_once_with(["tmux", "-Ltest_server", "list-sessions"], capture_output=True, check=False)
        assert result == expected_process

    def test_tmux_cmd_with_error_response(self, tmux_manager, mocker):
        """Test _tmux_cmd handles error responses correctly"""
        # Arrange
        expected_process = subprocess.CompletedProcess(
            args=["tmux", "-Lprunejuice", "invalid-command"],
            returncode=1,
            stdout=b"",
            stderr=b"unknown command: invalid-command\n",
        )
        mock_run = mocker.patch("prunejuice.core.tmux_ops.subprocess.run")
        mock_run.return_value = expected_process

        # Act
        result = tmux_manager._tmux_cmd("invalid-command")

        # Assert
        assert result.returncode == 1
        assert result.stderr == b"unknown command: invalid-command\n"
        assert isinstance(result, subprocess.CompletedProcess)

    def test_tmux_cmd_no_arguments(self, tmux_manager, mocker):
        """Test _tmux_cmd with no additional arguments"""
        # Arrange
        expected_process = subprocess.CompletedProcess(
            args=["tmux", "-Lprunejuice"], returncode=1, stdout=b"", stderr=b"usage: tmux [-options]\n"
        )
        mock_run = mocker.patch("prunejuice.core.tmux_ops.subprocess.run")
        mock_run.return_value = expected_process

        # Act
        result = tmux_manager._tmux_cmd()

        # Assert
        mock_run.assert_called_once_with(["tmux", "-Lprunejuice"], capture_output=True, check=False)
        assert result == expected_process

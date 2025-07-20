from unittest.mock import Mock

from prunejuice.core.tmux_ops import TmuxManager


class TestCheckTmuxAvailable:
    """Test cases for TmuxManager.check_tmux_available method"""

    def test_tmux_available(self, tmux_manager, mocker):
        """U07: Tmux available (mock subprocess.run with returncode=0)"""
        # Mock successful tmux version check
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run = mocker.patch("prunejuice.core.tmux_ops.subprocess.run", return_value=mock_result)

        # Test the method
        result = tmux_manager.check_tmux_available()

        # Assertions
        assert result is True
        # Verify subprocess.run was called once with the correct keyword arguments
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args.kwargs["capture_output"] is True
        assert call_args.kwargs["check"] is False

    def test_tmux_not_available(self, tmux_manager, mocker):
        """U08: Tmux not available (mock subprocess.run with returncode=1)"""
        # Mock failed tmux version check
        mock_result = Mock()
        mock_result.returncode = 1
        mock_run = mocker.patch("prunejuice.core.tmux_ops.subprocess.run", return_value=mock_result)

        # Test the method
        result = tmux_manager.check_tmux_available()

        # Assertions
        assert result is False
        # Verify subprocess.run was called once with the correct keyword arguments
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args.kwargs["capture_output"] is True
        assert call_args.kwargs["check"] is False

    def test_tmux_filenotfound_error(self, tmux_manager, mocker):
        """U09: FileNotFoundError handling (mock subprocess.run to raise FileNotFoundError)"""
        # Mock subprocess.run to raise FileNotFoundError
        mock_run = mocker.patch(
            "prunejuice.core.tmux_ops.subprocess.run", side_effect=FileNotFoundError("tmux not found")
        )

        # Test the method
        result = tmux_manager.check_tmux_available()

        # Assertions
        assert result is False
        # Verify subprocess.run was called once with the correct keyword arguments
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args.kwargs["capture_output"] is True
        assert call_args.kwargs["check"] is False

    def test_custom_server_name(self, custom_tmux_manager, mocker):
        """Test check_tmux_available with custom server name"""
        # Mock successful tmux version check
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run = mocker.patch("prunejuice.core.tmux_ops.subprocess.run", return_value=mock_result)

        # Test the method
        result = custom_tmux_manager.check_tmux_available()

        # Assertions
        assert result is True
        # Verify subprocess.run was called once with the correct keyword arguments
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args.kwargs["capture_output"] is True
        assert call_args.kwargs["check"] is False

    def test_check_tmux_available_method_behavior(self, mocker):
        """Test that check_tmux_available calls _tmux_cmd with correct arguments"""
        # Create a manager instance
        manager = TmuxManager("test_server")

        # Mock the _tmux_cmd method directly
        mock_tmux_cmd = mocker.patch.object(manager, "_tmux_cmd")
        mock_result = Mock()
        mock_result.returncode = 0
        mock_tmux_cmd.return_value = mock_result

        # Test the method
        result = manager.check_tmux_available()

        # Assertions
        assert result is True
        mock_tmux_cmd.assert_called_once_with("-V")

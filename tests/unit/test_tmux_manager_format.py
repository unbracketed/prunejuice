"""Unit tests for TmuxManager show_formatted_command method."""


class TestTmuxManagerShowFormattedCommand:
    """Test cases for TmuxManager show_formatted_command method."""

    def test_u17_single_argument(self, tmux_manager):
        """U17: Single argument (args=("list-sessions",))."""
        # Act
        result = tmux_manager.show_formatted_command("list-sessions")

        # Assert
        expected = "tmux -Lprunejuice list-sessions"
        assert result == expected

    def test_u18_multiple_arguments(self, tmux_manager):
        """U18: Multiple arguments (args=("new", "-d", "-s", "test"))."""
        # Act
        result = tmux_manager.show_formatted_command("new", "-d", "-s", "test")

        # Assert
        expected = "tmux -Lprunejuice new -d -s test"
        assert result == expected

    def test_u19_no_arguments(self, tmux_manager):
        """U19: No arguments (args=())."""
        # Act
        result = tmux_manager.show_formatted_command()

        # Assert
        expected = "tmux -Lprunejuice "
        assert result == expected

    def test_custom_server_name_formatting(self, custom_tmux_manager):
        """Additional test: Verify custom server name is used in formatting."""
        # Act
        result = custom_tmux_manager.show_formatted_command("list-sessions")

        # Assert
        expected = "tmux -Ltest_server list-sessions"
        assert result == expected

    def test_arguments_with_spaces(self, tmux_manager):
        """Additional test: Arguments containing spaces are handled correctly."""
        # Act
        result = tmux_manager.show_formatted_command("new", "-s", "session with spaces")

        # Assert
        expected = "tmux -Lprunejuice new -s session with spaces"
        assert result == expected

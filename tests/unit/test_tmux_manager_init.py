"""Unit tests for TmuxManager __init__ method."""

from prunejuice.core.tmux_ops import TmuxManager


class TestTmuxManagerInit:
    """Test cases for TmuxManager initialization."""

    def test_u01_default_initialization(self):
        """U01: Default initialization - server_name should be 'prunejuice'."""
        # Act
        manager = TmuxManager()

        # Assert
        assert manager.server_name == "prunejuice"

    def test_u02_custom_server_name(self):
        """U02: Custom server name - should use provided server name."""
        # Arrange
        custom_name = "custom_server"

        # Act
        manager = TmuxManager(server_name=custom_name)

        # Assert
        assert manager.server_name == custom_name

    def test_u03_empty_server_name(self):
        """U03: Empty server name - should handle empty string appropriately."""
        # Act
        manager = TmuxManager(server_name="")

        # Assert
        assert manager.server_name == ""
        # Note: Empty string is accepted as valid. The actual tmux command
        # behavior with empty server name would be tested in integration tests.

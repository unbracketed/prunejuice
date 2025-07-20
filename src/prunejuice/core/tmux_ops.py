import logging
import subprocess
from typing import Any

logger = logging.getLogger(__name__)


class TmuxManager:
    def __init__(self, server_name: str = "prunejuice"):
        self.server_name = server_name

    def _tmux_cmd(self, *args: str) -> subprocess.CompletedProcess[bytes]:
        result = subprocess.run(
            ["tmux", f"-L{self.server_name}", *args],
            capture_output=True,
            check=False,
        )
        return result

    def check_tmux_available(self) -> bool:
        """Check if tmux is available and working.

        Returns:
            True if tmux is available, False otherwise
        """
        try:
            return self._tmux_cmd("-V").returncode == 0
        except FileNotFoundError:
            return False

    def list_sessions(self) -> list[dict[str, Any]]:
        """List all tmux sessions.

        Returns:
            List of session information dictionaries
        """
        try:
            result = subprocess.run(
                [
                    "tmux",
                    f"-L{self.server_name}",
                    "list-sessions",
                    "-F",
                    "#{session_name}|#{session_path}|#{session_created}|#{session_attached}",
                ],
                capture_output=True,
                check=False,
            )
            stdout, stderr = result.stdout, result.stderr

            if result.returncode != 0:
                if "no server running" in stderr.decode().lower():
                    return []  # No tmux server running, no sessions
                raise RuntimeError(f"Failed to list sessions: {stderr.decode()}")

            sessions = []
            for line in stdout.decode().strip().splitlines():
                if not line:
                    continue

                parts = line.split("|")
                if len(parts) >= 4:
                    sessions.append({
                        "name": parts[0],
                        "path": parts[1],
                        "created": parts[2],
                        "attached": parts[3] == "1",
                    })
        except Exception:
            logger.exception("Failed to list tmux sessions")
            return []
        else:
            return sessions

    def show_formatted_command(self, *args: str) -> str:
        return f"tmux -L{self.server_name} {' '.join(args)}"

    def run_command_detached(
        self, cmd: str, session_name: str, working_dir: str = ""
    ) -> subprocess.CompletedProcess[bytes]:
        args = ["new", "-d", "-s", session_name, cmd]
        if working_dir:
            args.extend(["-c", working_dir])
        return self._tmux_cmd(*args)

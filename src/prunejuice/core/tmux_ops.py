import subprocess
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class TmuxManager:

    def __init__(self, server_name: str="prunejuice"):
        self.server_name = server_name

    def _tmux_cmd(self, *args):
        result = subprocess.run(
                ["tmux", f"-L{self.server_name}"].extend(args),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
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
        
    def list_sessions(self) -> List[Dict[str, Any]]:
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
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
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
                    sessions.append(
                        {
                            "name": parts[0],
                            "path": parts[1],
                            "created": parts[2],
                            "attached": parts[3] == "1",
                        }
                    )

            return sessions

        except Exception as e:
            logger.error(f"Failed to list tmux sessions: {e}")
            return []

    def show_formatted_command(self, *args) -> str:
        return f"tmux -L{self.server_name} {' '.join(args)}"

    def run_command_detached(self, cmd: str, session_name: str, working_dir:str="") -> subprocess.CompletedProcess[str]:
        "tmux -Lprunejuice new-session -d -s <workspace-slug> 'uv run python some_script.py | tee <artifact-dir>/<job>/<timestamp>.log'"
        # TODO tmux log
        args = ["new", "-d", "-s", session_name, cmd]
        if working_dir:
            args.extend(["-c", working_dir])
        return self._tmux_cmd(*args)

"""
Using isolated/multiple servers
tmux -Lprunejuice new
tmux -Lprunejuice list-sessions
0: 1 windows (created Sat Jul  5 16:23:25 2025)
tmux -Lprunejuice list-windows
0: zsh* (1 panes) [87x54] [layout bbdd,87x54,0,0,0] @0 (active)
tmux -Lprunejuice list-panes
0: [87x54] [history 1/2000, 2850 bytes] %0 (active)

https://github.com/tmux/tmux/wiki/Advanced-Use#working-directories
Each tmux session has default working directory. This is the working directory used for each new pane.

A session's working directory is set when it is first created:
$ tmux new -c/tmp

Service layer
session_for_workspace
- create or attach to session named for workspace; 
- use workspace dir for working dir
- set pane title and color


tmux -Lprunejuice new
# doesn't work with aliases
tmux -Lprunejuice new-session -d -s wet-claude 'claude'
tmux -Lprunejuice new-session -d -s vim-hello 'vim hello.txt'
tmux -Lprunejuice attach -t wet-claude
tmux -Lprunejuice attach -t git-status

https://claude.ai/share/1ed98118-fd1f-450d-b420-3a759d9402a8
tmux new -d 'script.sh |& tee tmux.log'

#!/bin/bash
# run_with_logging.sh
LOGFILE="task_$(date +%Y%m%d_%H%M%S).log"
echo "=== Task started at $(date) ===" | tee "$LOGFILE"
echo "Command: $*" | tee -a "$LOGFILE"
echo "==============================" | tee -a "$LOGFILE"

# Run the command and capture everything
"$@" 2>&1 | tee -a "$LOGFILE"
EXIT_CODE=${PIPESTATUS[0]}

echo "==============================" | tee -a "$LOGFILE"
echo "=== Task ended at $(date) ===" | tee -a "$LOGFILE"
echo "Exit code: $EXIT_CODE" | tee -a "$LOGFILE"

exit $EXIT_CODE


- Each Project has its own server `tmux -L<project-slug>`
- New Workspace: `tmux -Lprunejuice new-session -d -s <workspace-slug>`
- Run command in detached with logging:
    `tmux -Lprunejuice new-session -d -s <workspace-slug> 'uv run python some_script.py | tee <artifact-dir>/<job>/<timestamp>.log'
"""
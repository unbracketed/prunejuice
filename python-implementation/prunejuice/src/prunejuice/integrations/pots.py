"""Integration with pots tmux session manager."""

import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class PotsIntegration:
    """Integration with pots tmux session manager."""
    
    def __init__(self, pots_path: Optional[Path] = None):
        """Initialize pots integration."""
        self.pots_path = pots_path or self._find_pots()
    
    def _find_pots(self) -> Optional[Path]:
        """Find pots executable."""
        locations = [
            Path.cwd() / "scripts" / "pots" / "pots",
            Path.home() / ".local" / "bin" / "pots",
            Path("/usr/local/bin/pots"),
        ]
        
        for loc in locations:
            if loc.exists() and loc.is_file():
                return loc
        
        # Try which command
        try:
            result = subprocess.run(
                ["which", "pots"],
                capture_output=True,
                text=True,
                check=True
            )
            return Path(result.stdout.strip())
        except subprocess.CalledProcessError:
            return None
    
    async def create_session(
        self,
        working_dir: Path,
        task_name: str
    ) -> str:
        """Create a new tmux session."""
        session_name = f"prunejuice-{task_name}"
        
        if not self.pots_path:
            logger.warning("Pots not found, skipping session creation")
            return session_name
        
        try:
            result = subprocess.run(
                [str(self.pots_path), "create", str(working_dir), task_name],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse session name from output
            for line in result.stdout.splitlines():
                if "Session created:" in line:
                    return line.split(":", 1)[1].strip()
                elif "Created session" in line:
                    # Alternative output format
                    parts = line.split()
                    if len(parts) > 2:
                        return parts[2].strip()
            
            return session_name
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Pots create failed: {e.stderr}")
            # Don't fail the whole operation if tmux isn't available
            return session_name
    
    async def list_sessions(self) -> List[Dict[str, Any]]:
        """List all pots sessions."""
        if not self.pots_path:
            return []
        
        try:
            result = subprocess.run(
                [str(self.pots_path), "list"],
                capture_output=True,
                text=True,
                check=True
            )
            
            sessions = []
            for line in result.stdout.splitlines():
                if line.strip() and not line.startswith("#"):
                    parts = line.split()
                    if len(parts) >= 2:
                        sessions.append({
                            "name": parts[0],
                            "path": parts[1] if len(parts) > 1 else "unknown",
                            "status": parts[2] if len(parts) > 2 else "unknown"
                        })
            
            return sessions
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Pots list failed: {e.stderr}")
            return []
    
    async def attach_session(self, session_name: str) -> bool:
        """Attach to an existing session."""
        if not self.pots_path:
            return False
        
        try:
            subprocess.run(
                [str(self.pots_path), "attach", session_name],
                check=True
            )
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Pots attach failed: {e.stderr}")
            return False
    
    async def kill_session(self, session_name: str) -> bool:
        """Kill a session."""
        if not self.pots_path:
            return False
        
        try:
            subprocess.run(
                [str(self.pots_path), "kill", session_name],
                capture_output=True,
                text=True,
                check=True
            )
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Pots kill failed: {e.stderr}")
            return False
    
    def is_available(self) -> bool:
        """Check if pots is available."""
        return self.pots_path is not None and self.pots_path.exists()
"""Integration with plum worktree manager."""

import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging
import json

logger = logging.getLogger(__name__)


class PlumIntegration:
    """Integration with plum worktree manager."""
    
    def __init__(self, plum_path: Optional[Path] = None):
        """Initialize plum integration."""
        self.plum_path = plum_path or self._find_plum()
    
    def _find_plum(self) -> Optional[Path]:
        """Find plum executable in standard locations."""
        locations = [
            Path.cwd() / "scripts" / "plum-cli.sh",
            Path.cwd() / "scripts" / "plum" / "plum",
            Path.home() / ".local" / "bin" / "plum",
            Path("/usr/local/bin/plum"),
        ]
        
        for loc in locations:
            if loc.exists() and loc.is_file():
                return loc
        
        # Try which command
        try:
            result = subprocess.run(
                ["which", "plum"],
                capture_output=True,
                text=True,
                check=True
            )
            return Path(result.stdout.strip())
        except subprocess.CalledProcessError:
            return None
    
    async def create_worktree(
        self,
        project_path: Path,
        branch_name: str
    ) -> Path:
        """Create a new worktree and return its path."""
        if not self.plum_path:
            logger.warning("Plum not found, using fallback to project path")
            return project_path
        
        try:
            result = subprocess.run(
                [str(self.plum_path), "create", branch_name],
                cwd=project_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse worktree path from output
            for line in result.stdout.splitlines():
                if "Worktree created at:" in line:
                    return Path(line.split(":", 1)[1].strip())
                elif "Created worktree" in line and "at" in line:
                    # Alternative output format
                    parts = line.split("at")
                    if len(parts) > 1:
                        return Path(parts[-1].strip())
            
            # Fallback: assume worktree is in ../worktrees/branch_name
            worktree_path = project_path.parent / "worktrees" / branch_name
            if worktree_path.exists():
                return worktree_path
            
            logger.warning("Could not parse worktree path from plum output")
            return project_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Plum create failed: {e.stderr}")
            raise RuntimeError(f"Failed to create worktree: {e.stderr}")
    
    async def list_worktrees(self, project_path: Path) -> List[Dict[str, Any]]:
        """List all worktrees for the project."""
        if not self.plum_path:
            return []
        
        try:
            result = subprocess.run(
                [str(self.plum_path), "list"],
                cwd=project_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Try to parse JSON output if available
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                # Parse text output
                worktrees = []
                for line in result.stdout.splitlines():
                    if line.strip() and not line.startswith("#"):
                        parts = line.split()
                        if len(parts) >= 2:
                            worktrees.append({
                                "path": parts[0],
                                "branch": parts[1] if len(parts) > 1 else "unknown"
                            })
                return worktrees
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Plum list failed: {e.stderr}")
            return []
    
    async def remove_worktree(self, project_path: Path, worktree_path: Path) -> bool:
        """Remove a worktree."""
        if not self.plum_path:
            return False
        
        try:
            subprocess.run(
                [str(self.plum_path), "remove", str(worktree_path)],
                cwd=project_path,
                capture_output=True,
                text=True,
                check=True
            )
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Plum remove failed: {e.stderr}")
            return False
    
    def is_available(self) -> bool:
        """Check if plum is available."""
        return self.plum_path is not None and self.plum_path.exists()
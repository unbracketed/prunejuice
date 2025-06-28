"""YAML command loader for PruneJuice."""

import yaml
from pathlib import Path
from typing import List, Optional, Dict, Any
import hashlib
import logging

from ..core.models import CommandDefinition, CommandArgument

logger = logging.getLogger(__name__)


class CommandLoader:
    """Loads and manages YAML command definitions."""
    
    def __init__(self):
        """Initialize command loader."""
        self._command_cache: Dict[str, CommandDefinition] = {}
    
    async def discover_commands(self, project_path: Path) -> List[CommandDefinition]:
        """Discover all available commands in project and templates."""
        commands = []
        
        # Project-specific commands
        project_cmd_dir = project_path / ".prj" / "commands"
        if project_cmd_dir.exists():
            commands.extend(await self._load_commands_from_dir(project_cmd_dir))
        
        # Built-in template commands
        try:
            from importlib import resources
            template_files = resources.files("prunejuice.templates")
            for template_file in template_files.iterdir():
                if template_file.name.endswith('.yaml'):
                    try:
                        content = template_file.read_text()
                        cmd = self._parse_command_yaml(content, str(template_file))
                        if cmd:
                            commands.append(cmd)
                    except Exception as e:
                        logger.warning(f"Failed to load template {template_file.name}: {e}")
        except Exception as e:
            logger.warning(f"Failed to load template commands: {e}")
        
        return commands
    
    async def load_command(self, command_name: str, project_path: Path) -> Optional[CommandDefinition]:
        """Load a specific command by name."""
        # Check cache first
        if command_name in self._command_cache:
            return self._command_cache[command_name]
        
        # Look for command file
        search_paths = [
            project_path / ".prj" / "commands" / f"{command_name}.yaml",
            project_path / ".prj" / "commands" / f"{command_name}.yml",
        ]
        
        for cmd_path in search_paths:
            if cmd_path.exists():
                try:
                    with open(cmd_path, 'r') as f:
                        content = f.read()
                    
                    cmd = self._parse_command_yaml(content, str(cmd_path))
                    if cmd:
                        self._command_cache[command_name] = cmd
                        return cmd
                except Exception as e:
                    logger.error(f"Failed to load command {command_name}: {e}")
        
        # Try built-in templates
        try:
            from importlib import resources
            template_files = resources.files("prunejuice.templates")
            template_path = template_files / f"{command_name}.yaml"
            if template_path.is_file():
                content = template_path.read_text()
                cmd = self._parse_command_yaml(content, str(template_path))
                if cmd:
                    self._command_cache[command_name] = cmd
                    return cmd
        except Exception as e:
            logger.warning(f"Failed to load template command {command_name}: {e}")
        
        return None
    
    async def _load_commands_from_dir(self, cmd_dir: Path) -> List[CommandDefinition]:
        """Load all commands from a directory."""
        commands = []
        
        for cmd_file in cmd_dir.glob("*.yaml"):
            try:
                with open(cmd_file, 'r') as f:
                    content = f.read()
                
                cmd = self._parse_command_yaml(content, str(cmd_file))
                if cmd:
                    commands.append(cmd)
                    self._command_cache[cmd.name] = cmd
            except Exception as e:
                logger.error(f"Failed to load command from {cmd_file}: {e}")
        
        return commands
    
    def _parse_command_yaml(self, content: str, file_path: str) -> Optional[CommandDefinition]:
        """Parse YAML content into CommandDefinition."""
        try:
            data = yaml.safe_load(content)
            if not data:
                return None
            
            # Parse arguments
            arguments = []
            for arg_data in data.get('arguments', []):
                if isinstance(arg_data, dict):
                    arguments.append(CommandArgument(**arg_data))
                elif isinstance(arg_data, str):
                    arguments.append(CommandArgument(name=arg_data))
            
            # Create command definition
            cmd = CommandDefinition(
                name=data['name'],
                description=data.get('description', ''),
                extends=data.get('extends'),
                category=data.get('category', 'workflow'),
                arguments=arguments,
                environment=data.get('environment', {}),
                pre_steps=data.get('pre_steps', []),
                steps=data.get('steps', []),
                post_steps=data.get('post_steps', []),
                cleanup_on_failure=data.get('cleanup_on_failure', []),
                working_directory=data.get('working_directory'),
                timeout=data.get('timeout', 1800)
            )
            
            return cmd
            
        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error in {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing command from {file_path}: {e}")
            return None
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate hash of a file for change detection."""
        with open(file_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
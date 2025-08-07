"""
JARVIS VS Code Integration - Workspace control and code assistance
"""

import os
import json
import subprocess
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class VSCodeIntegration:
    """VS Code integration for workspace control and code assistance"""
    
    def __init__(self):
        self.vscode_command = self._find_vscode_command()
        self.current_workspace = None
        self.recent_files = []
        
        logger.info(f"VS Code integration initialized with command: {self.vscode_command}")
    
    def _find_vscode_command(self) -> str:
        """Find the VS Code command on the system"""
        possible_commands = [
            'code',           # Standard VS Code
            'code-insiders', # VS Code Insiders
            'codium',        # VSCodium
            '/usr/bin/code',
            '/snap/bin/code',
            '/opt/visual-studio-code/bin/code'
        ]
        
        for cmd in possible_commands:
            try:
                result = subprocess.run([cmd, '--version'], 
                                      capture_output=True, 
                                      text=True, 
                                      timeout=5)
                if result.returncode == 0:
                    return cmd
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
        
        return 'code'  # Default fallback
    
    def open_workspace(self, path: str) -> bool:
        """Open a workspace or folder in VS Code"""
        try:
            workspace_path = Path(path).resolve()
            
            if not workspace_path.exists():
                logger.error(f"Workspace path does not exist: {workspace_path}")
                return False
            
            # Open in VS Code
            result = subprocess.run([
                self.vscode_command, 
                str(workspace_path)
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.current_workspace = str(workspace_path)
                logger.info(f"Opened workspace: {workspace_path}")
                return True
            else:
                logger.error(f"Failed to open workspace: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error opening workspace: {e}")
            return False
    
    def open_file(self, file_path: str, line_number: Optional[int] = None) -> bool:
        """Open a specific file in VS Code"""
        try:
            file_path = Path(file_path).resolve()
            
            if not file_path.exists():
                logger.error(f"File does not exist: {file_path}")
                return False
            
            # Build command
            cmd = [self.vscode_command, str(file_path)]
            
            # Add line number if specified
            if line_number:
                cmd.extend(['--goto', f"{file_path}:{line_number}"])
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Add to recent files
                if str(file_path) not in self.recent_files:
                    self.recent_files.insert(0, str(file_path))
                    self.recent_files = self.recent_files[:10]  # Keep last 10
                
                logger.info(f"Opened file: {file_path}")
                return True
            else:
                logger.error(f"Failed to open file: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error opening file: {e}")
            return False
    
    def create_file(self, file_path: str, content: str = "") -> bool:
        """Create a new file with optional content"""
        try:
            file_path = Path(file_path)
            
            # Create directory if it doesn't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Open in VS Code
            self.open_file(str(file_path))
            
            logger.info(f"Created and opened file: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating file: {e}")
            return False
    
    def search_in_workspace(self, query: str) -> List[Dict[str, Any]]:
        """Search for text in the current workspace"""
        if not self.current_workspace:
            return []
        
        try:
            # Use grep to search for text
            result = subprocess.run([
                'grep', '-r', '-n', '--include=*.py', '--include=*.js', 
                '--include=*.ts', '--include=*.html', '--include=*.css',
                '--include=*.md', '--include=*.txt', '--include=*.json',
                query, self.current_workspace
            ], capture_output=True, text=True)
            
            matches = []
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if ':' in line:
                        parts = line.split(':', 2)
                        if len(parts) >= 3:
                            matches.append({
                                'file': parts[0],
                                'line': int(parts[1]) if parts[1].isdigit() else 0,
                                'content': parts[2].strip()
                            })
            
            logger.info(f"Found {len(matches)} matches for '{query}'")
            return matches
            
        except Exception as e:
            logger.error(f"Error searching workspace: {e}")
            return []
    
    def get_workspace_files(self, extensions: Optional[List[str]] = None) -> List[str]:
        """Get list of files in the current workspace"""
        if not self.current_workspace:
            return []
        
        try:
            workspace_path = Path(self.current_workspace)
            files = []
            
            # Default extensions if none specified
            if extensions is None:
                extensions = ['.py', '.js', '.ts', '.html', '.css', '.md', '.txt', '.json']
            
            # Walk through workspace directory
            for file_path in workspace_path.rglob('*'):
                if file_path.is_file():
                    if any(file_path.suffix == ext for ext in extensions):
                        # Skip hidden files and common ignore patterns
                        if not any(part.startswith('.') for part in file_path.parts):
                            if 'node_modules' not in file_path.parts:
                                if '__pycache__' not in file_path.parts:
                                    files.append(str(file_path))
            
            logger.info(f"Found {len(files)} files in workspace")
            return sorted(files)
            
        except Exception as e:
            logger.error(f"Error getting workspace files: {e}")
            return []
    
    def run_terminal_command(self, command: str) -> Dict[str, Any]:
        """Run a command in VS Code's integrated terminal"""
        try:
            # Open VS Code with terminal command
            result = subprocess.run([
                self.vscode_command,
                '--command', f'workbench.action.terminal.sendSequence',
                '--args', json.dumps({'text': f'{command}\n'})
            ], capture_output=True, text=True)
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr
            }
            
        except Exception as e:
            logger.error(f"Error running terminal command: {e}")
            return {
                'success': False,
                'output': '',
                'error': str(e)
            }
    
    def install_extension(self, extension_id: str) -> bool:
        """Install a VS Code extension"""
        try:
            result = subprocess.run([
                self.vscode_command,
                '--install-extension', extension_id
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Installed extension: {extension_id}")
                return True
            else:
                logger.error(f"Failed to install extension {extension_id}: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error installing extension: {e}")
            return False
    
    def get_installed_extensions(self) -> List[str]:
        """Get list of installed VS Code extensions"""
        try:
            result = subprocess.run([
                self.vscode_command,
                '--list-extensions'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                extensions = result.stdout.strip().split('\n')
                return [ext for ext in extensions if ext]
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error getting extensions: {e}")
            return []
    
    def format_document(self, file_path: str) -> bool:
        """Format a document using VS Code's formatter"""
        try:
            # Open file and format
            result = subprocess.run([
                self.vscode_command,
                str(file_path),
                '--command', 'editor.action.formatDocument'
            ], capture_output=True, text=True)
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Error formatting document: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get VS Code integration status"""
        return {
            'vscode_available': self._is_vscode_available(),
            'vscode_command': self.vscode_command,
            'current_workspace': self.current_workspace,
            'recent_files': self.recent_files,
            'installed_extensions': len(self.get_installed_extensions())
        }
    
    def _is_vscode_available(self) -> bool:
        """Check if VS Code is available"""
        try:
            result = subprocess.run([
                self.vscode_command, '--version'
            ], capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False

# Global VS Code integration instance
vscode_integration = None

def get_vscode_integration() -> VSCodeIntegration:
    """Get global VS Code integration instance"""
    global vscode_integration
    if vscode_integration is None:
        vscode_integration = VSCodeIntegration()
    return vscode_integration

"""
Utility functions for system operations
"""
import os
import sys
import platform
import subprocess
from pathlib import Path

def is_windows():
    """Check if running on Windows"""
    return platform.system() == "Windows"

def is_macos():
    """Check if running on macOS"""
    return platform.system() == "Darwin"

def is_linux():
    """Check if running on Linux"""
    return platform.system() == "Linux"

def run_command(cmd, shell=False):
    """
    Run a system command and return output
    """
    try:
        result = subprocess.run(
            cmd, 
            shell=shell, 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timeout"
    except Exception as e:
        return -1, "", str(e)

def open_path(path):
    """
    Open a path in the system file manager
    """
    if not os.path.exists(path):
        return False, f"Path does not exist: {path}"
    
    try:
        if is_windows():
            os.startfile(path)
        elif is_macos():
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
        return True, f"Opened: {path}"
    except Exception as e:
        return False, f"Error opening path: {str(e)}"

def get_special_folders():
    """
    Get common special folders
    """
    home = Path.home()
    folders = {
        "home": str(home),
        "desktop": str(home / "Desktop"),
        "documents": str(home / "Documents"),
        "downloads": str(home / "Downloads"),
        "pictures": str(home / "Pictures"),
        "music": str(home / "Music"),
        "videos": str(home / "Videos"),
    }
    
    # Verify which folders actually exist
    existing = {name: path for name, path in folders.items() if os.path.exists(path)}
    return existing

def check_app_installed(app_name):
    """
    Check if an application is installed
    """
    try:
        if is_windows():
            result = subprocess.run(
                ["where", app_name], 
                capture_output=True, 
                text=True
            )
            return result.returncode == 0
        else:
            result = subprocess.run(
                ["which", app_name], 
                capture_output=True, 
                text=True
            )
            return result.returncode == 0
    except:
        return False

def get_running_processes():
    """
    Get list of running processes
    """
    try:
        if is_windows():
            cmd = ["tasklist"]
        else:
            cmd = ["ps", "aux"]
        
        _, stdout, _ = run_command(cmd)
        return stdout
    except:
        return "Unable to get process list"
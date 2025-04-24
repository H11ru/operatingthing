import os
import json
from pathlib import Path

class VirtualFile:
    def __init__(self, name, content="", file_type="txt"):
        self.name = name
        self.content = content
        self.file_type = file_type
        self.metadata = {}

class VirtualDirectory:
    def __init__(self, name):
        self.name = name
        self.files = {}
        self.directories = {}

class FileSystem:
    def __init__(self):
        self.root = VirtualDirectory("root")
        self._real_root = Path("filesystem")
        self._real_root.mkdir(exist_ok=True)
        self.current_dir = self.root
        self._load_filesystem()

    def _load_filesystem(self):
        """Load the real filesystem into virtual filesystem"""
        if not self._real_root.exists():
            return

        for path in self._real_root.rglob("*"):
            if path.is_file():
                rel_path = path.relative_to(self._real_root)
                self.create_file(str(rel_path), path.read_text(), path.suffix[1:] if path.suffix else "txt")

    def create_file(self, path, content="", file_type="txt"):
        """Create a file in both virtual and real filesystem"""
        parts = path.strip("/").split("/")
        filename = parts[-1]
        dir_path = parts[:-1]

        current = self.root
        for dir_name in dir_path:
            if dir_name not in current.directories:
                current.directories[dir_name] = VirtualDirectory(dir_name)
            current = current.directories[dir_name]

        virtual_file = VirtualFile(filename, content, file_type)
        current.files[filename] = virtual_file

        # Create real file
        real_path = self._real_root / Path(*dir_path) / filename
        real_path.parent.mkdir(parents=True, exist_ok=True)
        real_path.write_text(content)

        return virtual_file

    def read_file(self, path):
        """Read a file from the virtual filesystem"""
        parts = path.strip("/").split("/")
        filename = parts[-1]
        dir_path = parts[:-1]

        current = self.root
        for dir_name in dir_path:
            if dir_name not in current.directories:
                raise FileNotFoundError(f"Directory not found: {dir_name}")
            current = current.directories[dir_name]

        if filename not in current.files:
            raise FileNotFoundError(f"File not found: {filename}")

        return current.files[filename]

    def list_directory(self, path=""):
        """List contents of a directory"""
        if not path:
            current = self.root
        else:
            parts = path.strip("/").split("/")
            current = self.root
            for dir_name in parts:
                if dir_name not in current.directories:
                    raise FileNotFoundError(f"Directory not found: {dir_name}")
                current = current.directories[dir_name]

        return {
            "directories": list(current.directories.keys()),
            "files": list(current.files.keys())
        }

    def execute_file(self, path):
        """Execute a file if it's executable"""
        file = self.read_file(path)
        if file.file_type == "pya":  # PyOS App format
            return file.content  # Return the code instead of executing it
        elif file.file_type == "py":  # Standard Python file
            real_path = self._real_root / path
            if real_path.exists():
                return str(real_path)
            return False
        return False
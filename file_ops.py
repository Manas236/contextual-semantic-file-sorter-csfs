import os
import shutil
import hashlib
from pathlib import Path
from typing import Union, List, Optional

def calculate_file_hash(file_path: Union[str, Path], chunk_size: int = 8192) -> str:
    """Generates a SHA-256 hash for content verification."""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(chunk_size):
            sha256.update(chunk)
    return sha256.hexdigest()

def ensure_directory(directory_path: Union[str, Path]) -> None:
    """Creates a directory if it does not exist."""
    Path(directory_path).mkdir(parents=True, exist_ok=True)

def safe_move(source: Union[str, Path], destination: Union[str, Path], dry_run: bool = False) -> None:
    """Moves a file, optionally simulating the action."""
    src = Path(source)
    dst = Path(destination)
    
    if not src.exists():
        raise FileNotFoundError(f"Source file not found: {src}")

    if dry_run:
        print(f"[DRY-RUN] Would move: {src} -> {dst}")
    else:
        ensure_directory(dst.parent)
        shutil.move(str(src), str(dst))

def get_file_metadata(file_path: Union[str, Path]) -> dict:
    """Extracts basic filesystem metadata."""
    stat = os.stat(file_path)
    return {
        "size": stat.st_size,
        "created": stat.st_ctime,
        "modified": stat.st_mtime,
        "extension": Path(file_path).suffix.lower()
    }

def list_files_recursive(root_dir: Union[str, Path], ignore_patterns: Optional[List[str]] = None) -> List[Path]:
    """Recursively lists files, supporting basic ignore patterns (e.g., .git, __pycache__)."""
    ignore_patterns = ignore_patterns or ['.git', '__pycache__', '.DS_Store']
    file_list = []
    
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in ignore_patterns]
        for file in files:
            file_list.append(Path(root) / file)
    
    return file_list

def is_text_file(file_path: Union[str, Path], block_size: int = 512) -> bool:
    """Heuristic to determine if a file is plain text."""
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(block_size)
            return b'\0' not in chunk
    except (IOError, OSError):
        return False
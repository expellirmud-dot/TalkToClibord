
# Test Module 5 - File system and I/O operations
import os
import shutil
import hashlib
from pathlib import Path
from typing import List, Optional, BinaryIO

class FileManager:
    """File system manager for various I/O operations.
    
    Capabilities:
    - File and directory operations
    - Hash calculation for integrity verification
    - Batch file processing
    - Archive management
    
    Attributes:
        base_path: Root directory for file operations
        buffer_size: Size of read/write buffer in bytes
    """
    
    def __init__(self, base_path: str, buffer_size: int = 8192):
        self.base_path = Path(base_path)
        self.buffer_size = buffer_size
        
    def ensure_directory(self, path: str) -> bool:
        """Ensure directory exists, create if necessary."""
        dir_path = self.base_path / path
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path.exists()
    
    def calculate_hash(self, file_path: str, algorithm: str = 'sha256') -> str:
        """Calculate hash of file for integrity verification."""
        hash_func = hashlib.new(algorithm)
        full_path = self.base_path / file_path
        
        with open(full_path, 'rb') as f:
            while chunk := f.read(self.buffer_size):
                hash_func.update(chunk)
        
        return hash_func.hexdigest()
    
    def copy_file(self, src: str, dst: str) -> bool:
        """Copy file with progress tracking."""
        src_path = self.base_path / src
        dst_path = self.base_path / dst
        
        try:
            shutil.copy2(src_path, dst_path)
            return True
        except Exception as e:
            print(f"Copy failed: {e}")
            return False
    
    def batch_copy(self, file_pairs: List[tuple]) -> Dict:
        """Copy multiple files in batch operation."""
        results = {'success': 0, 'failed': 0, 'errors': []}
        
        for src, dst in file_pairs:
            if self.copy_file(src, dst):
                results['success'] += 1
            else:
                results['failed'] += 1
                results['errors'].append(f"{src} -> {dst}")
        
        return results
    
    def list_files(self, pattern: str = '*') -> List[str]:
        """List files matching pattern in base directory."""
        return [str(f) for f in self.base_path.glob(pattern) if f.is_file()]
    
    def get_file_info(self, file_path: str) -> Dict:
        """Get detailed information about a file."""
        full_path = self.base_path / file_path
        stat = full_path.stat()
        
        return {
            'name': full_path.name,
            'size': stat.st_size,
            'created': stat.st_ctime,
            'modified': stat.st_mtime,
            'is_file': full_path.is_file(),
            'is_dir': full_path.is_dir()
        }

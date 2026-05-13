# vision_reference_loader.py (V3.2 - Smart File Loading with Recursive Search)
import os
import re
from typing import List, Dict, Optional, Tuple

# Import path constants
from src.utils.vision_paths import ROOT_DIR

class ReferenceLoader:
    """Smart file loading with reference patterns, lazy loading, and recursive search"""
    
    def __init__(self, project_dir=None):
        # Use ROOT_DIR from vision_paths.py as single source of truth
        self.project_dir = project_dir if project_dir else ROOT_DIR
        self._file_cache = {}
        self._metadata_cache = {}
        
        # Reference patterns
        self.reference_patterns = [
            r'@([\w_\-\.]+\.(?:py|txt|md|json|yaml|yml|csv))',
            r'@([\w_\-\.]+)',  # Function/class names
            r'([\w_\-\.]+\.(?:py|txt|md|json|yaml|yml|csv))'  # Direct file references
        ]
        
        # Function/class pattern
        self.func_pattern = r'(?:def|class)\s+([\w_]+)'
    
    def detect_references(self, text: str) -> List[str]:
        """Detect @path patterns in the prompt"""
        references = []
        
        for pattern in self.reference_patterns:
            matches = re.findall(pattern, text)
            references.extend(matches)
        
        # Remove duplicates and preserve order
        seen = set()
        unique_refs = []
        for ref in references:
            if ref not in seen:
                seen.add(ref)
                unique_refs.append(ref)
        
        return unique_refs
    
    def _recursive_find_file(self, reference: str) -> Optional[str]:
        """Recursively search for a file in the project directory"""
        # Extract basename in case reference includes partial paths
        basename = os.path.basename(reference)
        
        try:
            for root, dirs, files in os.walk(self.project_dir):
                # Skip common ignore directories to optimize search speed
                dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'venv', 'venv_build', 'node_modules', '.idea', '.vscode']]
                
                if basename in files:
                    full_path = os.path.join(root, basename)
                    # Ensure the found file matches the partial path if provided
                    # e.g., if reference is "data/config.json", it must match the end of the path
                    normalized_ref = os.path.normpath(reference)
                    if full_path.endswith(normalized_ref):
                        return full_path
        except Exception as e:
            print(f"[ReferenceLoader] ERROR during recursive file search for {reference}: {e}")
            
        return None

    def get_file_path(self, reference: str) -> Optional[str]:
        """Resolve reference to actual file path"""
        # If it's already a file with extension
        if '.' in reference and reference.split('.')[-1] in ['py', 'txt', 'md', 'json', 'yaml', 'yml', 'csv']:
            # 1. Try relative to project dir (Root level)
            rel_path = os.path.join(self.project_dir, reference)
            if os.path.exists(rel_path):
                return rel_path
            
            # 2. Try absolute path
            if os.path.exists(reference):
                return reference
                
            # 3. Try recursive search in project directory (NEW FIX)
            found_path = self._recursive_find_file(reference)
            if found_path:
                return found_path
            
            # 4. Try in vision_ modules
            if not reference.startswith('vision_'):
                vision_ref = f"vision_{reference}"
                
                # Try root level vision_ file
                vision_path = os.path.join(self.project_dir, vision_ref)
                if os.path.exists(vision_path):
                    return vision_path
                    
                # Try recursive search for vision_ file
                found_vision_path = self._recursive_find_file(vision_ref)
                if found_vision_path:
                    return found_vision_path
            
            # If it has an extension but cannot be found anywhere, return None
            return None
        
        # If it's a function/class name (no extension), search in Python files
        return self.find_function_in_project(reference)
    
    def find_function_in_project(self, func_name: str) -> Optional[str]:
        """Find function/class definition in project files"""
        try:
            for root, dirs, files in os.walk(self.project_dir):
                # Skip common ignore directories
                dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'venv', 'venv_build', 'node_modules']]
                
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        if self.file_contains_function(file_path, func_name):
                            return file_path
        except Exception as e:
            print(f"[ReferenceLoader] ERROR searching for function {func_name}: {e}")
        
        return None
    
    def file_contains_function(self, file_path: str, func_name: str) -> bool:
        """Check if file contains function/class definition"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                pattern = rf'(?:def|class)\s+{re.escape(func_name)}\s*\('
                return bool(re.search(pattern, content))
        except Exception:
            return False
    
    def get_file_metadata(self, file_path: str) -> Dict[str, any]:
        """Get file metadata instead of full content"""
        if file_path in self._metadata_cache:
            return self._metadata_cache[file_path]
        
        try:
            if not os.path.exists(file_path):
                return {"error": "File not found"}
            
            stat = os.stat(file_path)
            
            # Extract basic info
            metadata = {
                "path": file_path,
                "size": stat.st_size,
                "extension": os.path.splitext(file_path)[1],
                "modified": stat.st_mtime
            }
            
            # Extract function/class names if Python file
            if file_path.endswith('.py'):
                functions, classes = self.extract_python_signatures(file_path)
                metadata["functions"] = functions
                metadata["classes"] = classes
                metadata["imports"] = self.extract_imports(file_path)
            
            self._metadata_cache[file_path] = metadata
            return metadata
            
        except Exception as e:
            error_meta = {"error": str(e)}
            self._metadata_cache[file_path] = error_meta
            return error_meta
    
    def extract_python_signatures(self, file_path: str) -> Tuple[List[str], List[str]]:
        """Extract function and class signatures from Python file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            functions = re.findall(r'def\s+([\w_]+)\s*\(', content)
            classes = re.findall(r'class\s+([\w_]+)\s*:', content)
            
            return functions, classes
        except Exception:
            return [], []
    
    def extract_imports(self, file_path: str) -> List[str]:
        """Extract import statements from Python file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            imports = re.findall(r'(?:import|from)\s+([\w_.]+)', content)
            return list(set(imports))
        except Exception:
            return []
    
    def load_file_reference(self, reference: str, max_lines: int = 50, lazy: bool = True) -> Dict[str, any]:
        """Load file reference with lazy loading option"""
        file_path = self.get_file_path(reference)
        
        if not file_path:
            return {"error": f"Reference '{reference}' not found"}
        
        if lazy:
            # Return metadata only
            metadata = self.get_file_metadata(file_path)
            metadata["reference"] = reference
            metadata["loading_mode"] = "lazy"
            return metadata
        else:
            # Load actual content (limited)
            return self.load_file_content(file_path, max_lines, reference)
    
    def load_file_content(self, file_path: str, max_lines: int = 50, reference: str = "") -> Dict[str, any]:
        """Load file content with line limit"""
        try:
            if not os.path.exists(file_path):
                return {"error": "File not found"}
            
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Limit lines
            if len(lines) > max_lines:
                content_lines = lines[:max_lines]
                truncated = True
            else:
                content_lines = lines
                truncated = False
            
            content = ''.join(content_lines)
            
            return {
                "reference": reference,
                "path": file_path,
                "content": content,
                "lines_loaded": len(content_lines),
                "total_lines": len(lines),
                "truncated": truncated,
                "loading_mode": "full"
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def load_function_reference(self, func_name: str, context_lines: int = 5) -> Dict[str, any]:
        """Load specific function with context"""
        file_path = self.find_function_in_project(func_name)
        
        if not file_path:
            return {"error": f"Function '{func_name}' not found"}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Find function definition
            func_pattern = rf'def\s+{re.escape(func_name)}\s*\('
            for i, line in enumerate(lines):
                if re.search(func_pattern, line):
                    # Get context lines
                    start = max(0, i - context_lines)
                    end = min(len(lines), i + context_lines + 1)
                    
                    content = ''.join(lines[start:end])
                    
                    return {
                        "reference": func_name,
                        "path": file_path,
                        "content": content,
                        "line_number": i + 1,
                        "context_lines": context_lines
                    }
            
            return {"error": f"Function '{func_name}' definition not found"}
            
        except Exception as e:
            return {"error": str(e)}
    
    def batch_load_references(self, references: List[str], lazy: bool = True) -> List[Dict]:
        """Load multiple references efficiently"""
        results = []
        
        for ref in references:
            # Check if it's a function reference
            if not '.' in ref or ref.split('.')[-1] not in ['py', 'txt', 'md', 'json', 'yaml', 'yml', 'csv']:
                result = self.load_function_reference(ref)
            else:
                result = self.load_file_reference(ref, lazy=lazy)
            
            results.append(result)
        
        return results
    
    def clear_cache(self):
        """Clear file and metadata cache"""
        self._file_cache.clear()
        self._metadata_cache.clear()
        print("[ReferenceLoader] Cache cleared")
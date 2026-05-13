# vision_dependency_graph.py (V3.1 - Structural Mapper)
import os
import re
from typing import Dict, List, Set, Tuple

# Import path constants
from src.utils.vision_paths import ROOT_DIR

class DependencyGraph:
    """Map file dependencies and provide task optimization insights"""
    
    def __init__(self, project_dir=None):
        # Use ROOT_DIR from vision_paths.py as single source of truth
        self.project_dir = project_dir if project_dir else ROOT_DIR
        self._dependency_graph = {}
        self._reverse_graph = {}
        self._file_metadata = {}
        
        # Dependency patterns
        self.import_patterns = [
            r'from\s+([\w_.]+)\s+import',
            r'import\s+([\w_.]+)'
        ]
        
        # Ignore directories
        self.ignore_dirs = ['__pycache__', '.git', 'venv', 'venv_build', 'data', 'lite', 'build', 'dist']
    
    def scan_project(self) -> Dict[str, List[str]]:
        """Scan project directory to map file dependencies"""
        self._dependency_graph = {}
        self._reverse_graph = {}
        self._file_metadata = {}
        
        try:
            for root, dirs, files in os.walk(self.project_dir):
                # Skip ignored directories
                dirs[:] = [d for d in dirs if d not in self.ignore_dirs]
                
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        relative_path = os.path.relpath(file_path, self.project_dir)
                        
                        # Extract dependencies
                        dependencies = self._extract_dependencies(file_path)
                        self._dependency_graph[relative_path] = dependencies
                        
                        # Build reverse graph
                        for dep in dependencies:
                            if dep not in self._reverse_graph:
                                self._reverse_graph[dep] = []
                            self._reverse_graph[dep].append(relative_path)
                        
                        # Store metadata
                        self._file_metadata[relative_path] = {
                            "path": file_path,
                            "size": os.path.getsize(file_path),
                            "dependencies": dependencies
                        }
            
            print(f"[DependencyGraph] Scanned {len(self._dependency_graph)} Python files")
            return self._dependency_graph
            
        except Exception as e:
            print(f"[DependencyGraph] ERROR scanning project: {e}")
            return {}
    
    def _extract_dependencies(self, file_path: str) -> List[str]:
        """Extract import dependencies from a Python file"""
        dependencies = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract imports
            for pattern in self.import_patterns:
                matches = re.findall(pattern, content)
                dependencies.extend(matches)
            
            # Filter and normalize
            dependencies = list(set(dependencies))  # Remove duplicates
            dependencies = [d for d in dependencies if not d.startswith('.')]  # Skip relative imports
            
            return dependencies
            
        except Exception as e:
            print(f"[DependencyGraph] ERROR extracting dependencies from {file_path}: {e}")
            return []
    
    def get_graph(self) -> Dict[str, List[str]]:
        """Get the dependency graph"""
        return self._dependency_graph
    
    def get_reverse_graph(self) -> Dict[str, List[str]]:
        """Get the reverse dependency graph (what depends on what)"""
        return self._reverse_graph
    
    def get_file_dependencies(self, file_path: str) -> List[str]:
        """Get dependencies for a specific file"""
        relative_path = os.path.relpath(file_path, self.project_dir) if os.path.isabs(file_path) else file_path
        return self._dependency_graph.get(relative_path, [])
    
    def get_dependents(self, module_name: str) -> List[str]:
        """Get files that depend on a specific module"""
        return self._reverse_graph.get(module_name, [])
    
    def find_highly_related_files(self, files: List[str]) -> List[List[str]]:
        """Group highly related files based on shared dependencies"""
        if not files:
            return []
        
        # Build similarity matrix
        groups = []
        used = set()
        
        for i, file1 in enumerate(files):
            if file1 in used:
                continue
            
            deps1 = set(self._dependency_graph.get(file1, []))
            group = [file1]
            used.add(file1)
            
            for file2 in files[i+1:]:
                if file2 in used:
                    continue
                
                deps2 = set(self._dependency_graph.get(file2, []))
                
                # Check if files share dependencies
                if deps1.intersection(deps2):
                    group.append(file2)
                    used.add(file2)
            
            if len(group) > 1:
                groups.append(group)
            else:
                groups.append([file1])
        
        return groups
    
    def get_dependency_chain(self, file_path: str) -> List[str]:
        """Get full dependency chain for a file"""
        chain = []
        visited = set()
        
        def _get_chain(file: str):
            if file in visited:
                return
            
            visited.add(file)
            chain.append(file)
            
            deps = self._dependency_graph.get(file, [])
            for dep in deps:
                _get_chain(dep)
        
        relative_path = os.path.relpath(file_path, self.project_dir) if os.path.isabs(file_path) else file_path
        _get_chain(relative_path)
        
        return chain
    
    def get_circular_dependencies(self) -> List[List[str]]:
        """Detect circular dependencies in the graph"""
        circular = []
        visited = set()
        
        for file in self._dependency_graph:
            if file not in visited:
                path = []
                if self._has_cycle(file, path, visited):
                    circular.append(path.copy())
        
        return circular
    
    def _has_cycle(self, file: str, path: List[str], visited: Set[str]) -> bool:
        """Helper to detect cycles using DFS"""
        if file in path:
            return True
        
        if file in visited:
            return False
        
        path.append(file)
        visited.add(file)
        
        for dep in self._dependency_graph.get(file, []):
            if self._has_cycle(dep, path, visited):
                return True
        
        path.pop()
        return False
    
    def get_critical_files(self) -> List[str]:
        """Get files with many dependents (high impact)"""
        critical = []
        
        for file, dependents in self._reverse_graph.items():
            if len(dependents) >= 3:  # Files with 3+ dependents
                critical.append(file)
        
        # Sort by number of dependents
        critical.sort(key=lambda x: len(self._reverse_graph[x]), reverse=True)
        
        return critical
    
    def suggest_task_grouping(self, files: List[str]) -> Dict[str, List[str]]:
        """Suggest task grouping based on dependency analysis"""
        if not files:
            return {}
        
        # Group by shared dependencies
        related_groups = self.find_highly_related_files(files)
        
        # Create task groups
        task_groups = {}
        for i, group in enumerate(related_groups):
            task_groups[f"group_{i+1}"] = group
        
        return task_groups
    
    def get_graph_stats(self) -> Dict[str, any]:
        """Get statistics about the dependency graph"""
        total_files = len(self._dependency_graph)
        total_dependencies = sum(len(deps) for deps in self._dependency_graph.values())
        avg_dependencies = total_dependencies / total_files if total_files > 0 else 0
        
        max_deps = 0
        file_with_max_deps = ""
        for file, deps in self._dependency_graph.items():
            if len(deps) > max_deps:
                max_deps = len(deps)
                file_with_max_deps = file
        
        return {
            "total_files": total_files,
            "total_dependencies": total_dependencies,
            "avg_dependencies_per_file": avg_dependencies,
            "file_with_most_dependencies": file_with_max_deps,
            "max_dependencies": max_deps,
            "critical_files_count": len(self.get_critical_files())
        }
    
    def visualize_graph(self) -> str:
        """Generate text-based graph visualization"""
        lines = []
        lines.append("=" * 60)
        lines.append("DEPENDENCY GRAPH")
        lines.append("=" * 60)
        
        for file, deps in sorted(self._dependency_graph.items()):
            if deps:
                lines.append(f"{file}")
                for dep in deps:
                    lines.append(f"  -> {dep}")
            else:
                lines.append(f"{file} (no dependencies)")
        
        return "\n".join(lines)

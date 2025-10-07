#!/usr/bin/env python3
"""
Jerry AI Assistant - Code Quality Improvement Script
Addresses critical linting issues and modernizes Python practices.
"""

import ast
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


class CodeQualityFixer:
    """Automated code quality improvements for Jerry project."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.src_dir = project_root / "src"
        self.tests_dir = project_root / "tests"
        
    def fix_exception_chaining(self) -> List[str]:
        """Fix exception chaining issues (B904)."""
        fixes = []
        
        # Pattern for exception handling without 'from'
        pattern = r'raise\s+(\w+Exception)\s*\([^)]*\)\s*$'
        
        for py_file in self.src_dir.rglob("*.py"):
            content = py_file.read_text()
            lines = content.split('\n')
            modified = False
            
            for i, line in enumerate(lines):
                # Look for raise statements in except blocks
                if re.match(r'\s*raise\s+\w+Exception', line):
                    # Check if we're in an except block
                    for j in range(i-1, max(0, i-10), -1):
                        if 'except' in lines[j] and 'as' in lines[j]:
                            # Extract exception variable
                            match = re.search(r'except\s+\w+\s+as\s+(\w+)', lines[j])
                            if match:
                                exc_var = match.group(1)
                                # Add 'from exc_var' if not present
                                if 'from' not in line:
                                    lines[i] = line.rstrip() + f' from {exc_var}'
                                    modified = True
                                    fixes.append(f"Fixed exception chaining in {py_file}:{i+1}")
                            break
            
            if modified:
                py_file.write_text('\n'.join(lines))
        
        return fixes
    
    def fix_unused_imports(self) -> List[str]:
        """Remove unused imports identified by ruff."""
        fixes = []
        
        # Run ruff to get unused imports
        result = subprocess.run([
            'uv', 'run', 'ruff', 'check', 'src/', '--select', 'F401', '--fix'
        ], capture_output=True, text=True, cwd=self.project_root)
        
        if result.returncode == 0:
            fixes.append("Fixed unused imports via ruff")
        
        return fixes
    
    def fix_type_comparisons(self) -> List[str]:
        """Fix type comparison issues (E721)."""
        fixes = []
        
        for py_file in self.src_dir.rglob("*.py"):
            content = py_file.read_text()
            modified = False
            
            # Replace type equality with 'is' comparison
            patterns = [
                (r'var_type\s*==\s*bool', 'var_type is bool'),
                (r'var_type\s*==\s*int', 'var_type is int'),
                (r'var_type\s*==\s*float', 'var_type is float'),
                (r'var_type\s*==\s*list', 'var_type is list'),
                (r'var_type\s*==\s*str', 'var_type is str'),
                (r'var_type\s*==\s*dict', 'var_type is dict'),
            ]
            
            for pattern, replacement in patterns:
                new_content = re.sub(pattern, replacement, content)
                if new_content != content:
                    content = new_content
                    modified = True
            
            if modified:
                py_file.write_text(content)
                fixes.append(f"Fixed type comparisons in {py_file}")
        
        return fixes
    
    def fix_pathlib_usage(self) -> List[str]:
        """Replace open() with pathlib.Path usage."""
        fixes = []
        
        for py_file in self.src_dir.rglob("*.py"):
            content = py_file.read_text()
            lines = content.split('\n')
            modified = False
            
            for i, line in enumerate(lines):
                # Simple pattern matching for open() calls
                if 'with open(' in line and 'Path(' not in line:
                    # Extract the file path variable
                    match = re.search(r'with open\(([^,)]+)', line)
                    if match:
                        file_var = match.group(1).strip()
                        # Replace with Path().open()
                        new_line = line.replace(f'open({file_var}', f'{file_var}.open(')
                        lines[i] = new_line
                        modified = True
            
            if modified:
                py_file.write_text('\n'.join(lines))
                fixes.append(f"Updated pathlib usage in {py_file}")
        
        return fixes
    
    def remove_unused_variables(self) -> List[str]:
        """Remove unused variable assignments."""
        fixes = []
        
        # Run ruff to fix unused variables
        result = subprocess.run([
            'uv', 'run', 'ruff', 'check', 'src/', '--select', 'F841', '--fix'
        ], capture_output=True, text=True, cwd=self.project_root)
        
        if result.returncode == 0:
            fixes.append("Removed unused variables via ruff")
        
        return fixes
    
    def fix_whitespace_issues(self) -> List[str]:
        """Fix trailing whitespace and blank line issues."""
        fixes = []
        
        for py_file in self.src_dir.rglob("*.py"):
            content = py_file.read_text()
            lines = content.split('\n')
            modified = False
            
            for i, line in enumerate(lines):
                # Remove trailing whitespace
                stripped = line.rstrip()
                if stripped != line:
                    lines[i] = stripped
                    modified = True
                
                # Fix blank lines with whitespace
                if line.strip() == '' and line != '':
                    lines[i] = ''
                    modified = True
            
            if modified:
                py_file.write_text('\n'.join(lines))
                fixes.append(f"Fixed whitespace in {py_file}")
        
        return fixes
    
    def apply_all_fixes(self) -> None:
        """Apply all code quality fixes."""
        print("🔧 Starting Jerry AI code quality improvements...")
        
        all_fixes = []
        
        # Apply fixes in order
        fixes_methods = [
            ("Unused imports", self.fix_unused_imports),
            ("Type comparisons", self.fix_type_comparisons),
            ("Pathlib usage", self.fix_pathlib_usage),
            ("Unused variables", self.remove_unused_variables),
            ("Whitespace issues", self.fix_whitespace_issues),
            ("Exception chaining", self.fix_exception_chaining),
        ]
        
        for description, method in fixes_methods:
            print(f"📝 Fixing {description}...")
            fixes = method()
            all_fixes.extend(fixes)
            print(f"   ✅ {len(fixes)} issues fixed")
        
        # Final format pass
        print("🎨 Running final formatting...")
        subprocess.run([
            'uv', 'run', 'ruff', 'format', 'src/', 'tests/'
        ], cwd=self.project_root)
        
        print(f"\n🎉 Code quality improvements complete!")
        print(f"📊 Total fixes applied: {len(all_fixes)}")
        
        # Final validation
        print("\n🔍 Running final validation...")
        result = subprocess.run([
            'uv', 'run', 'ruff', 'check', 'src/', 'tests/'
        ], capture_output=True, text=True, cwd=self.project_root)
        
        if result.returncode == 0:
            print("✅ All checks passed!")
        else:
            print("⚠️  Some issues remain:")
            print(result.stdout)


def main():
    """Main entry point."""
    project_root = Path(__file__).parent
    fixer = CodeQualityFixer(project_root)
    fixer.apply_all_fixes()


if __name__ == "__main__":
    main()
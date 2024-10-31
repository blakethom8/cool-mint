"""Utility functions for path management and import resolution.

This module provides functionality to ensure consistent import behavior
whether running from project root or in interactive mode.
"""

import sys
from pathlib import Path
from typing import Optional


def setup_project_path(fallback_path: Optional[Path] = None) -> None:
    """Sets up the Python path to include the project root.

    Args:
        fallback_path: Optional path to use as project root if automatic
            detection fails.

    Raises:
        ValueError: If project root cannot be determined.
    """
    # Try to find app directory by walking up from current file
    current = Path(__file__).resolve()
    for parent in [current, *current.parents]:
        if (parent / "app").is_dir():
            project_root = parent
            break
    else:
        if fallback_path is None:
            raise ValueError("Could not determine project root")
        project_root = fallback_path

    # Add project root to path if not already there
    project_root_str = str(project_root)
    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)

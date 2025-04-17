import sys
from pathlib import Path

from services.prompt_loader import PromptManager

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "app"))

"""
This playground is used to test the PromptManager and the prompts themselves.
"""

# --------------------------------------------------------------
# Test support prompt
# --------------------------------------------------------------

support_prompt = PromptManager.get_prompt("template", workflow="", ticket={})
print(support_prompt)

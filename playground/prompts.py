import sys

sys.path.append("..")

from services.prompt_loader import PromptManager


# --------------------------------------------------------------
# Test support prompt
# --------------------------------------------------------------

support_prompt = PromptManager.get_prompt(
    "ticket_analysis", pipeline="support", ticket={}
)
print(support_prompt)

# --------------------------------------------------------------
# Test helpdesk prompt
# --------------------------------------------------------------

helpdesk_prompt = PromptManager.get_prompt(
    "ticket_analysis", pipeline="helpdesk", ticket={}
)
print(helpdesk_prompt)

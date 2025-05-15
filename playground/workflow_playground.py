import logging
import sys
from datetime import datetime
from pathlib import Path

from schemas.langfuse_tracing_schema import LangfuseTracingEventSchema
from workflows.langfuse_tracing_workflow import LangfuseTracingWorkflow

logging.basicConfig(level=logging.INFO)

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "app"))
sys.path.append(str(project_root))

"""
This playground is used to test the WorkflowRegistry and the workflows themselves.
"""

event = LangfuseTracingEventSchema(
    event="comment.posted",
    timestamp=datetime.now(),
    comment_id="cmt_44210",
    thread_id="thr_103",
    user_id="user_998",
    content="You're all idiots if you believe that nonsense.",
)

output = LangfuseTracingWorkflow().run(event.model_dump())
output.model_dump()

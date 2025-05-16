from typing import Optional

from pydantic_ai import RunContext

from core.nodes.agent import AgentNode, AgentConfig, ModelProvider
from core.task import TaskContext
from schemas.langfuse_tracing_schema import LangfuseTracingEventSchema


class ViolationDetectionNode(AgentNode):
    def get_agent_config(self) -> AgentConfig:
        return AgentConfig(
            system_prompt="Determine whether the comment is a violation or not. If it is a violation, provide a reason for violation. If it is not a violation, provide a reason for non-violation.",
            output_type=self.ViolationDetectionResult,
            deps_type=LangfuseTracingEventSchema,
            model_provider=ModelProvider.OPENAI,
            model_name="gpt-4.1",
            instrument=True
        )

    class ViolationDetectionResult(AgentNode.OutputType):
        comment_id: str
        violation: bool
        reason: Optional[str] = None

    def process(self, task_context: TaskContext) -> TaskContext:
        event: LangfuseTracingEventSchema = task_context.event

        @self.agent.system_prompt
        async def add_context(
                ctx: RunContext[LangfuseTracingEventSchema],
        ) -> str:
            return event.model_dump_json()

        result = self.agent.run_sync(user_prompt=event.model_dump_json())

        task_context.update_node(node_name=self.node_name, results=result.output)
        return task_context

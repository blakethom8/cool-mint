from pydantic_ai import RunContext

from core.nodes.agent import AgentNode, AgentConfig, ModelProvider
from core.task import TaskContext
from schemas.langfuse_tracing_schema import LangfuseTracingEventSchema


class ContextSummaryResult(AgentNode):
    def get_agent_config(self) -> AgentConfig:
        return AgentConfig(
            system_prompt="Summarize the comment in a concise and concise way.",
            output_type=self.ContextSummaryResult,
            deps_type=LangfuseTracingEventSchema,
            model_provider=ModelProvider.OPENAI,
            model_name="gpt-4.1",
            instrument=True,
        )

    class ContextSummaryResult(AgentNode.OutputType):
        comment_id: str
        summary: str

    def process(self, task_context: TaskContext) -> TaskContext:
        event: LangfuseTracingEventSchema = task_context.event

        @self.agent.instructions
        async def add_context(
            ctx: RunContext[LangfuseTracingEventSchema],
        ) -> str:
            return event.model_dump_json()

        result = self.agent.run_sync(user_prompt=event.model_dump_json())

        task_context.update_node(node_name=self.node_name, results=result.output)
        return task_context

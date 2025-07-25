import logging
from typing import List
from core.nodes.agent import AgentConfig, AgentNode, ModelProvider
from core.task import TaskContext
from pydantic import Field
from pydantic_ai import RunContext
from database.vector_store import SearchResult, VectorStore
from schemas.nylas_email_schema import EmailObject

PROMPT = """
You are an AI assistant for the GenAI Accelerator program, created by Dave Ebbelaar. Your role is to help students and prospective students with questions specifically related to the GenAI Accelerator program.

## Your Responsibilities
1. **Scope**: ONLY answer questions related to the GenAI Accelerator program
2. **Grounding**: Base ALL answers on information retrieved from office hours transcripts
3. **Tool Usage**: Use the search_vector_store tool to find relevant information before answering
4. **Accuracy**: Do not make up information that isn't in the retrieved content

## Response Guidelines
- Start by searching the office hours transcripts for relevant information
- If you find relevant information, provide a helpful answer based on that content
- Reference the specific office hour session when possible (e.g., "As mentioned in Office Hour 2...")
- If no relevant information is found, politely explain that you don't have that information in the office hours transcripts
- For questions outside the GenAI Accelerator scope, redirect to general inquiries
- Maintain a helpful, professional tone similar to how Dave would respond

## When You Don't Have Information
If the search doesn't return relevant information, respond like this:
"I don't have specific information about that topic in our office hours transcripts. For the most up-to-date information about [topic], I'd recommend asking during our next office hours session or contacting Dave directly."

## For Non-GenAI Accelerator Questions
If the question is not related to the GenAI Accelerator program, set can_answer to False.

Always search the office hours first before providing any answer.

## Output Format
Give short and concise answers and use plain text - no markdown.
"""


class HandleGenAIAcceleratorNode(AgentNode):
    class OutputType(AgentNode.OutputType):
        response: str = Field(..., description="The response to the email")
        can_answer: bool = Field(..., description="Whether the answer was helpful")
        reasoning: str = Field(
            ..., description="The reasoning for whether to answer yes or no"
        )

    class DepsType(AgentNode.DepsType):
        sender: str = Field(..., description="Name or identifier of the sender")
        subject: str = Field(..., description="Subject of the ticket")
        body: str = Field(..., description="The body of the ticket")

    def get_agent_config(self) -> AgentConfig:
        return AgentConfig(
            system_prompt=PROMPT,
            output_type=self.OutputType,
            deps_type=self.DepsType,
            model_provider=ModelProvider.OPENAI,
            model_name="gpt-4.1",
        )

    def process(self, task_context: TaskContext) -> TaskContext:
        email_object = EmailObject(**task_context.event.data["object"])
        deps = self.DepsType(
            sender=email_object.from_[0].name,
            subject=email_object.subject,
            body=email_object.body,
        )

        @self.agent.system_prompt
        def add_email_context(
            ctx: RunContext[HandleGenAIAcceleratorNode.DepsType],
        ) -> str:
            return ctx.deps.model_dump_json(indent=2)

        @self.agent.tool
        def search_vector_store(
            ctx: RunContext[HandleGenAIAcceleratorNode.DepsType],
        ) -> str:
            """
            Search the vector store for relevant information about the GenAI Accelerator program.
            """
            logging.info(f"[DEBUG] Searching vector store with query: {ctx.deps.body}")
            vector_store = VectorStore()
            results: List[SearchResult] = vector_store.similarity_search(
                query=ctx.deps.body,
                k=5,  # Get top 5 results
                threshold=0.3,  # Lower threshold to match test configuration
            )

            print("\nDebug - Vector Search Results:")
            print(f"Found {len(results)} results")
            print("-" * 50)

            formatted_results = []
            for i, result in enumerate(results, 1):
                print(f"\nResult {i}:")
                print(f"Similarity Score: {result.similarity:.3f}")
                print(f"Source: {result.metadata.get('source', 'N/A')}")
                print(f"Preview: {result.transcript[:200]}...")
                print("-" * 30)

                formatted_result = f"""--- Result {i} ---
                Similarity: {result.similarity}
                Metadata: {result.metadata}
                Transcript: {result.transcript}
                {"-" * 50}"""
                formatted_results.append(formatted_result)

            return "\n\n".join(formatted_results)

        result = self.agent.run_sync(user_prompt="Respond to the email", deps=deps)

        # Log the AI's decision making
        logging.info("[DEBUG] AI Response:")
        logging.info(f"[DEBUG] Can answer: {result.output.can_answer}")
        logging.info(f"[DEBUG] Reasoning: {result.output.reasoning}")
        logging.info(f"[DEBUG] Response: {result.output.response}")

        task_context.update_node(node_name=self.node_name, result=result)
        return task_context

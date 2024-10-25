from typing import Set

from core.schema import PipelineSchema


class PipelineValidator:
    """Validator for pipeline schemas."""

    def __init__(self, schema: PipelineSchema):
        self.schema = schema

    def validate(self) -> bool:
        """
        Validate that the pipeline schema forms a DAG and non-router steps have only one next step.

        Returns:
            bool: True if the schema is valid.

        Raises:
            ValueError: If the schema is invalid, with a description of the issue.
        """
        visited: Set[str] = set()
        stack: Set[str] = set()

        def dfs(node: str) -> None:
            if node in stack:
                raise ValueError(f"Cycle detected involving step: {node}")
            if node in visited:
                return

            visited.add(node)
            stack.add(node)

            step_config = self.schema.steps.get(node)
            if step_config:
                # Check that non-router steps have only one next step
                if not step_config.is_router and len(step_config.next) > 1:
                    raise ValueError(
                        f"Non-router step '{node}' has multiple next steps"
                    )

                for next_step in step_config.next:
                    if next_step not in self.schema.steps:
                        raise ValueError(
                            f"Step '{next_step}' referenced but not defined"
                        )
                    dfs(next_step)

            stack.remove(node)

        dfs(self.schema.start)

        unreachable = set(self.schema.steps.keys()) - visited
        if unreachable:
            raise ValueError(f"Unreachable steps detected: {', '.join(unreachable)}")

        return True

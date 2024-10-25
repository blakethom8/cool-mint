from typing import Set, Type

from core.base import Step
from core.schema import PipelineSchema


class PipelineValidator:
    """Validator for pipeline schemas."""

    def __init__(self, schema: PipelineSchema):
        self.schema = schema

    def validate(self) -> bool:
        """
        Validate that the pipeline schema forms a DAG and non-router nodes have only one next node.

        Returns:
            bool: True if the schema is valid.

        Raises:
            ValueError: If the schema is invalid, with a description of the issue.
        """
        visited: Set[Type[Step]] = set()
        stack: Set[Type[Step]] = set()

        def dfs(node_class: Type[Step]) -> None:
            if node_class in stack:
                raise ValueError(
                    f"Cycle detected involving node: {node_class.__name__}"
                )
            if node_class in visited:
                return

            visited.add(node_class)
            stack.add(node_class)

            node_config = next(
                (nc for nc in self.schema.nodes if nc.node == node_class), None
            )
            if node_config:
                # Check that non-router nodes have only one next node
                if not node_config.is_router and len(node_config.connections) > 1:
                    raise ValueError(
                        f"Non-router node '{node_class.__name__}' has multiple next nodes"
                    )

                for next_node in node_config.connections:
                    if next_node not in [nc.node for nc in self.schema.nodes]:
                        raise ValueError(
                            f"Node '{next_node.__name__}' referenced but not defined"
                        )
                    dfs(next_node)

            stack.remove(node_class)

        dfs(self.schema.start)

        all_nodes = {nc.node for nc in self.schema.nodes}
        unreachable = all_nodes - visited
        if unreachable:
            raise ValueError(
                f"Unreachable nodes detected: {', '.join(node.__name__ for node in unreachable)}"
            )

        return True

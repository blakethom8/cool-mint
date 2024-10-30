from collections import deque
from typing import Set, Type

from core.base import Node
from core.schema import PipelineSchema


class PipelineValidator:
    """Validator for pipeline schemas."""

    def __init__(self, pipeline_schema: PipelineSchema):
        self.pipeline_schema = pipeline_schema

    def validate(self):
        """Validate the pipeline schema."""
        self._validate_dag()
        self._validate_connections()

    def _validate_dag(self):
        """Validate that the pipeline schema forms a proper DAG."""
        # Check for cycles
        if self._has_cycle():
            raise ValueError("Pipeline schema contains a cycle")

        # Check if all nodes are reachable from the start node
        reachable_nodes = self._get_reachable_nodes()
        all_nodes = set(nc.node for nc in self.pipeline_schema.nodes)
        unreachable_nodes = all_nodes - reachable_nodes
        if unreachable_nodes:
            raise ValueError(
                f"The following nodes are unreachable: {unreachable_nodes}"
            )

    def _has_cycle(self) -> bool:
        """Check if the pipeline schema contains a cycle."""
        visited = set()
        rec_stack = set()

        def dfs(node: Type[Node]) -> bool:
            visited.add(node)
            rec_stack.add(node)

            node_config = next(
                (nc for nc in self.pipeline_schema.nodes if nc.node == node), None
            )
            if node_config:
                for neighbor in node_config.connections:
                    if neighbor not in visited:
                        if dfs(neighbor):
                            return True
                    elif neighbor in rec_stack:
                        return True

            rec_stack.remove(node)
            return False

        for node_config in self.pipeline_schema.nodes:
            if node_config.node not in visited:
                if dfs(node_config.node):
                    return True

        return False

    def _get_reachable_nodes(self) -> Set[Type[Node]]:
        """Get all nodes reachable from the start node."""
        reachable = set()
        queue = deque([self.pipeline_schema.start])

        while queue:
            node = queue.popleft()
            if node not in reachable:
                reachable.add(node)
                node_config = next(
                    (nc for nc in self.pipeline_schema.nodes if nc.node == node), None
                )
                if node_config:
                    queue.extend(node_config.connections)

        return reachable

    def _validate_connections(self):
        """Validate that only router nodes have multiple connections."""
        for node_config in self.pipeline_schema.nodes:
            if len(node_config.connections) > 1 and not node_config.is_router:
                raise ValueError(
                    f"Node {node_config.node.__name__} has multiple connections but is not marked as a router."
                )

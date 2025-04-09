from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor

from core.base import Node
from core.schema import NodeConfig
from core.task import TaskContext


class ParallelizationNode(Node, ABC):
    def execute_nodes_in_parallel(self, task_context: TaskContext):
        node_config: NodeConfig = task_context.metadata['nodes'][self.__class__]
        future_list = []
        with ThreadPoolExecutor() as executor:
            for node in node_config.parallel_nodes:
                future = executor.submit(node().process, task_context)
                future_list.append(future)

            results = [future.result() for future in future_list]
        return results

    @abstractmethod
    def process(self, task_context: TaskContext) -> TaskContext:
        self.execute_nodes_in_parallel(task_context)
        return task_context

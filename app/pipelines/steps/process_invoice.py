from pipelines.core.base import BaseStep
from models.domain.task import TaskContext
import logging


class ProcessInvoice(BaseStep):
    def process(self, task_context: TaskContext) -> TaskContext:
        self._get_invoice(task_context)
        return task_context

    def _get_invoice(self, task_context: TaskContext):
        logging.info("Billing intent detected. Invoice service should be called.")
        # Add logic to retrieve and process invoice here
        task_context.steps[self.step_name] = {"invoice_retrieved": True}

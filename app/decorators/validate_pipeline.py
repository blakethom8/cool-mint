from functools import wraps

from pipelines.core.pipeline import PipelineSchema, StepType


def validate_pipeline_configuration(pipeline_schema: PipelineSchema) -> None:
    """Validates the pipeline configuration.

    Args:
        pipeline_schema: A PipelineSchema object representing the pipeline configuration.

    Raises:
        ValueError: If any part of the pipeline configuration is invalid.
    """
    steps = pipeline_schema.steps
    start: StepType = pipeline_schema.start

    if start.__name__ not in steps:
        raise ValueError(f"Start step '{start.__name__}' not found in steps.")

    for step_name, step_config in steps.items():
        if step_config.next is not None and step_config.routes is not None:
            raise ValueError(
                f"Step '{step_name}' cannot have both 'next' and 'routes' defined."
            )

        if step_config.routes:
            for route, next_step in step_config.routes.items():
                if not isinstance(next_step, type):
                    raise ValueError(
                        f"Route '{route}' for step '{step_name}' must be a class, not an instance."
                    )
                if next_step.__name__ not in steps:
                    raise ValueError(
                        f"Route '{route}' for step '{step_name}' points to non-existent step '{next_step.__name__}'."
                    )

        if step_config.next is not None:
            if not isinstance(step_config.next, type):
                raise ValueError(
                    f"'next' for step '{step_name}' must be a class, not an instance."
                )
            if step_config.next.__name__ not in steps:
                raise ValueError(
                    f"'next' for step '{step_name}' points to non-existent step '{step_config.next.__name__}'."
                )

    # Check for circular dependencies
    visited = {}

    def dfs(step_name: str) -> None:
        if step_name in visited:
            if visited[step_name]:
                raise ValueError(
                    f"Circular dependency detected involving step '{step_name}'."
                )
            return
        visited[step_name] = True
        step_config = steps[step_name]
        if step_config.next:
            dfs(step_config.next.__name__)
        elif step_config.routes:
            for next_step in step_config.routes.values():
                dfs(next_step.__name__)
        visited[step_name] = False

    dfs(start.__name__)


def validate_pipeline(cls):
    """Decorator to validate the pipeline configuration.

    This decorator wraps the __init__ method of the class and calls
    validate_pipeline_configuration after the original initialization.

    Args:
        cls: The class to be decorated.

    Returns:
        The decorated class.

    Raises:
        ValueError: If the pipeline configuration is invalid.
    """
    original_init = cls.__init__

    @wraps(original_init)
    def new_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        validate_pipeline_configuration(self.pipeline_schema)

    cls.__init__ = new_init
    return cls

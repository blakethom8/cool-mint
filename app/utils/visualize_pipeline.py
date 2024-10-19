from graphviz import Digraph
from pipelines.core.pipeline import Pipeline


def visualize_pipeline(pipeline: Pipeline) -> Digraph:
    """
    Generates a visual representation of the pipeline flow with a modern look.

    Args:
        pipeline: The Pipeline object to visualize.

    Returns:
        A graphviz Digraph object representing the pipeline with modern styling.

    Raises:
        ImportError: If graphviz is not installed.

    Note:
        Requires both the Graphviz Python package and system package to be installed.
        See the class docstring for installation instructions.
    """
    try:
        dot = Digraph(comment="Customer Pipeline")
        dot.attr(
            rankdir="LR",
            bgcolor="transparent",
            fontname="Helvetica,Arial,sans-serif",
            pad="0.5",
            nodesep="0.5",
            ranksep="0.75",
        )

        # Define modern node style
        dot.attr(
            "node",
            shape="rectangle",
            style="filled",
            fillcolor="#ececfd",
            color="#8e71d5",
            fontcolor="#333333",
            fontname="Helvetica,Arial,sans-serif",
            fontsize="12",
            height="0.6",
            width="1.5",
            penwidth="2",
        )

        # Define modern edge style
        dot.attr(
            "edge",
            color="#333333",
            penwidth="2",
            arrowsize="0.8",
            fontname="Helvetica,Arial,sans-serif",
            fontsize="10",
        )

        # Add nodes
        for step, config in pipeline.pipeline_schema.steps.items():
            if isinstance(config, dict) and "routes" in config:
                # Use diamond shape for router nodes
                dot.node(step, step, shape="diamond")
            else:
                dot.node(step, step)

        # Add edges
        start_node = pipeline.pipeline_schema.start.__name__
        dot.node("Event", "Event", shape="ellipse", fillcolor="#ececfd")
        dot.edge("Event", start_node, tailport="e", headport="w")

        for step, config in pipeline.pipeline_schema.steps.items():
            if isinstance(config, dict):
                if "next" in config and config.next:
                    dot.edge(step, config.next.__name__, tailport="e", headport="w")
                elif "routes" in config:
                    for route in config.routes:
                        dot.edge(step, route.__name__, tailport="e", headport="w")
            else:  # StepConfig object
                if config.next:
                    dot.edge(step, config.next.__name__, tailport="e", headport="w")
                elif config.routes:
                    for route in config.routes.values():
                        dot.edge(step, route.__name__, tailport="e", headport="w")

        return dot
    except ImportError:
        raise ImportError("Please install graphviz: pip install graphviz")

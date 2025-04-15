import sys
from pathlib import Path

from core.pipeline import Pipeline
from playground.utils.visualize_pipeline import visualize_pipeline

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "app"))

"""
This playground is used to visualize the pipelines.
"""


def generate(pipeline: Pipeline):
    image = visualize_pipeline(pipeline)
    with open("pipeline.png", "wb") as f:
        f.write(image.data)

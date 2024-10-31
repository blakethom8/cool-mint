import sys
from pathlib import Path

app_root = Path(__file__).parent.parent
sys.path.append(str(app_root / "app"))

from utils.visualize_pipeline import visualize_pipeline  # noqa: E402
from pipelines.customer_pipeline import CustomerSupportPipeline  # noqa: E402

"""
This playground is used to visualize the pipelines.
"""

pipeline = CustomerSupportPipeline()
visualize_pipeline(pipeline)

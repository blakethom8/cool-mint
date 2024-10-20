import sys

sys.path.append("..")

from app.utils.visualize_pipeline import visualize_pipeline
from pipelines.customer_pipeline import CustomerPipeline

pipeline = CustomerPipeline()
visualize_pipeline(pipeline)

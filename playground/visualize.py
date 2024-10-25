import sys

sys.path.append("..")

from app.utils.visualize_pipeline import visualize_pipeline
from pipelines.customer_pipeline import CustomerSupportPipeline

pipeline = CustomerSupportPipeline()
visualize_pipeline(pipeline)

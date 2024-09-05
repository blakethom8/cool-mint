import os

from celery import Celery
from dotenv import load_dotenv

load_dotenv()

redis_host = f"{os.getenv('PROJECT_NAME')}_redis"
redis_url = f"redis://{redis_host}:6379/0"

celery_app = Celery("tasks", broker=redis_url, backend=redis_url)
celery_app.conf.update(
    result_backend=redis_url,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    enable_utc=True,
    broker_connection_retry_on_startup=True,
)
celery_app.autodiscover_tasks(["tasks"], force=True)

import os
from datetime import timedelta

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class VectorStoreConfig(BaseSettings):
    """Settings for the VectorStore."""

    table_name: str = "embeddings"
    embedding_dimensions: int = 1536
    time_partition_interval: timedelta = timedelta(days=7)


class DatabaseConfig(BaseSettings):
    """Settings for the database."""

    host: str = os.getenv("DATABASE_HOST", "localhost")
    port: str = os.getenv("DATABASE_PORT", "5432")
    name: str = os.getenv("DATABASE_NAME", "launchpad")
    user: str = os.getenv("DATABASE_USER", "postgres")
    password: str = os.getenv("DATABASE_PASSWORD")
    service_url: str = f"postgres://{user}:{password}@{host}:{port}/{name}"
    vector_store: VectorStoreConfig = VectorStoreConfig()

from enum import StrEnum


class VectorType(StrEnum):
    MILVUS = "milvus"
    QDRANT = "qdrant"
    CHROMA = "chroma"
    PGVECTOR = "pgvector"
    WEAVIATE = "weaviate"

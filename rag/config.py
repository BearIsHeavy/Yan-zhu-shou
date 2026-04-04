"""
RAG Configuration.

Loads settings from environment variables.
"""

import os


class RAGConfig:
    """RAG configuration."""
    
    # Vector Store
    VECTOR_STORE_TYPE: str = os.getenv("VECTOR_STORE_TYPE", "pgvector")
    
    # Embedding Model
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    EMBEDDING_DIMENSION: int = int(os.getenv("EMBEDDING_DIMENSION", "1536"))
    EMBEDDING_MODEL_PATH: str = os.getenv("EMBEDDING_MODEL_PATH", "")
    
    # RAG Settings
    SEARCH_TOP_K: int = int(os.getenv("RAG_SEARCH_TOP_K", "5"))
    SIMILARITY_THRESHOLD: float = float(os.getenv("RAG_SIMILARITY_THRESHOLD", "0.7"))
    MAX_CONTEXT_TOKENS: int = int(os.getenv("RAG_MAX_CONTEXT_TOKENS", "4000"))
    
    # Chunk Settings
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "500"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "50"))
    
    @classmethod
    def use_local_embedding(cls) -> bool:
        """Check if using local embedding model."""
        return bool(cls.EMBEDDING_MODEL_PATH)
    
    @classmethod
    def get_embedding_model(cls) -> str:
        """Get embedding model name or path."""
        if cls.use_local_embedding():
            return cls.EMBEDDING_MODEL_PATH
        return cls.EMBEDDING_MODEL

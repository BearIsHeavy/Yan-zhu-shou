"""
Embedding Service.

Generates vector embeddings for text using OpenAI or local models.
"""

import asyncio
import logging
from typing import List, Optional
import os

from rag.config import RAGConfig

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Service for generating text embeddings.
    
    Supports:
    - OpenAI API (text-embedding-3-small, text-embedding-3-large)
    - Local models via sentence-transformers (bge-large-zh, m3e-base)
    """
    
    def __init__(self, use_local: Optional[bool] = None):
        """
        Initialize embedding service.
        
        Args:
            use_local: Force use of local model (default: from config)
        """
        self.use_local = use_local if use_local is not None else RAGConfig.use_local_embedding()
        self.dimension = RAGConfig.EMBEDDING_DIMENSION
        self._model = None
        self._client = None
        
        if self.use_local:
            self._init_local_model()
        else:
            self._init_openai_client()
    
    def _init_openai_client(self):
        """Initialize OpenAI client for embeddings."""
        try:
            from openai import OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not set in environment")
            self._client = OpenAI(api_key=api_key)
            self.model_name = RAGConfig.EMBEDDING_MODEL
            logger.info(f"Initialized OpenAI embedding client: {self.model_name}")
        except ImportError:
            logger.warning("openai not installed. Falling back to local model.")
            self.use_local = True
            self._init_local_model()
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise
    
    def _init_local_model(self):
        """Initialize local embedding model."""
        try:
            from sentence_transformers import SentenceTransformer
            model_path = RAGConfig.EMBEDDING_MODEL_PATH or "BAAI/bge-large-zh-v1.5"
            self._model = SentenceTransformer(model_path)
            self.dimension = self._model.get_sentence_embedding_dimension()
            logger.info(f"Initialized local embedding model: {model_path}")
        except ImportError:
            logger.error("sentence-transformers not installed. Please install with: pip install sentence-transformers")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize local model: {e}")
            raise
    
    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        if self.use_local:
            return await self._embed_local(text)
        else:
            return await self._embed_openai(text)
    
    async def _embed_openai(self, text: str) -> List[float]:
        """Generate embedding using OpenAI API."""
        try:
            response = self._client.embeddings.create(
                model=self.model_name,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"OpenAI embedding failed: {e}")
            raise
    
    async def _embed_local(self, text: str) -> List[float]:
        """Generate embedding using local model."""
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None,
                lambda: self._model.encode(text, convert_to_numpy=True).tolist()
            )
            return embedding
        except Exception as e:
            logger.error(f"Local embedding failed: {e}")
            raise
    
    async def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing
            
        Returns:
            List of embedding vectors
        """
        if self.use_local:
            return await self._embed_batch_local(texts, batch_size)
        else:
            return await self._embed_batch_openai(texts, batch_size)
    
    async def _embed_batch_openai(self, texts: List[str], batch_size: int) -> List[List[float]]:
        """Generate batch embeddings using OpenAI."""
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            try:
                response = self._client.embeddings.create(
                    model=self.model_name,
                    input=batch
                )
                # Sort by index to maintain order
                sorted_data = sorted(response.data, key=lambda x: x.index)
                all_embeddings.extend([item.embedding for item in sorted_data])
            except Exception as e:
                logger.error(f"OpenAI batch embedding failed: {e}")
                raise
        
        return all_embeddings
    
    async def _embed_batch_local(self, texts: List[str], batch_size: int) -> List[List[float]]:
        """Generate batch embeddings using local model."""
        loop = asyncio.get_event_loop()
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            try:
                embeddings = await loop.run_in_executor(
                    None,
                    lambda: self._model.encode(batch, convert_to_numpy=True).tolist()
                )
                all_embeddings.extend(embeddings)
            except Exception as e:
                logger.error(f"Local batch embedding failed: {e}")
                raise
        
        return all_embeddings
    
    def encode_query(self, query: str) -> List[float]:
        """
        Encode a query for retrieval.
        
        Some models benefit from query-specific prefixes.
        
        Args:
            query: Search query
            
        Returns:
            Query embedding
        """
        # Add query prefix for certain models
        if self.use_local:
            model_name = (RAGConfig.EMBEDDING_MODEL_PATH or "").lower()
            if "bge" in model_name:
                query = f"为这个句子生成表示以用于检索：{query}"
            elif "m3e" in model_name:
                query = f"query: {query}"
        
        import asyncio
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.embed_text(query))

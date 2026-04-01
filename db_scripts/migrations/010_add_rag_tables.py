"""
Migration: Add RAG (Retrieval-Augmented Generation) tables

This migration creates tables for:
- knowledge_embeddings: Vector embeddings for knowledge points
- document_chunks: Chunked document content with embeddings
- rag_queries: Query history for analytics

Requires pgvector extension: CREATE EXTENSION vector;

Run: python db_scripts/migrations/010_add_rag_tables.py
"""

import asyncio
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
sys.path.insert(0, PROJECT_ROOT)

from sqlalchemy import text
from database import engine


async def migrate():
    """Create RAG tables with pgvector support."""
    async with engine.begin() as conn:
        print("=" * 60)
        print("RAG Tables Migration")
        print("=" * 60)
        
        # Enable pgvector extension
        print("\n[0/4] Enabling pgvector extension...")
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        print("✓ pgvector extension enabled")
        
        # 1. Create knowledge_embeddings table
        print("\n[1/4] Creating knowledge_embeddings table...")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS knowledge_embeddings (
                id SERIAL PRIMARY KEY,
                knowledge_id INTEGER REFERENCES knowledge_points(id) ON DELETE CASCADE,
                content TEXT NOT NULL,
                embedding vector(1536),
                metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ke_knowledge ON knowledge_embeddings(knowledge_id)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ke_embedding ON knowledge_embeddings USING ivfflat (embedding vector_cosine_ops)"))
        print("✓ Created knowledge_embeddings table with vector index")
        
        # 2. Create document_chunks table
        print("\n[2/4] Creating document_chunks table...")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS document_chunks (
                id SERIAL PRIMARY KEY,
                book_id INTEGER REFERENCES user_books(id) ON DELETE CASCADE,
                chapter VARCHAR(200),
                content TEXT NOT NULL,
                embedding vector(1536),
                page_number INTEGER,
                chunk_index INTEGER,
                token_count INTEGER,
                metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_dc_book ON document_chunks(book_id)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_dc_chapter ON document_chunks(chapter)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_dc_embedding ON document_chunks USING ivfflat (embedding vector_cosine_ops)"))
        print("✓ Created document_chunks table with vector index")
        
        # 3. Create rag_queries table (for analytics)
        print("\n[3/4] Creating rag_queries table...")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS rag_queries (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES "User"(user_id) ON DELETE CASCADE,
                query_text TEXT NOT NULL,
                query_embedding vector(1536),
                results_count INTEGER DEFAULT 0,
                response_type VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_rq_user ON rag_queries(user_id)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_rq_created ON rag_queries(created_at)"))
        print("✓ Created rag_queries table")
        
        # 4. Create helper functions
        print("\n[4/4] Creating helper functions...")
        
        # Function to search similar embeddings
        await conn.execute(text("""
            CREATE OR REPLACE FUNCTION search_similar_knowledge(
                query_embedding vector(1536),
                match_threshold FLOAT DEFAULT 0.7,
                match_count INT DEFAULT 5
            )
            RETURNS TABLE (
                id INT,
                knowledge_id INT,
                content TEXT,
                similarity FLOAT,
                metadata JSONB
            )
            LANGUAGE plpgsql
            AS $$
            BEGIN
                RETURN QUERY
                SELECT
                    ke.id::INT,
                    ke.knowledge_id::INT,
                    ke.content::TEXT,
                    (1 - (ke.embedding <=> query_embedding))::FLOAT AS similarity,
                    ke.metadata
                FROM knowledge_embeddings ke
                WHERE 1 - (ke.embedding <=> query_embedding) > match_threshold
                ORDER BY ke.embedding <=> query_embedding
                LIMIT match_count;
            END;
            $$;
        """))
        
        # Function to search similar documents
        await conn.execute(text("""
            CREATE OR REPLACE FUNCTION search_similar_documents(
                query_embedding vector(1536),
                match_threshold FLOAT DEFAULT 0.7,
                match_count INT DEFAULT 5,
                filter_book_id INT DEFAULT NULL
            )
            RETURNS TABLE (
                id INT,
                book_id INT,
                chapter TEXT,
                content TEXT,
                similarity FLOAT,
                page_number INT,
                metadata JSONB
            )
            LANGUAGE plpgsql
            AS $$
            BEGIN
                RETURN QUERY
                SELECT
                    dc.id::INT,
                    dc.book_id::INT,
                    dc.chapter::TEXT,
                    dc.content::TEXT,
                    (1 - (dc.embedding <=> query_embedding))::FLOAT AS similarity,
                    dc.page_number::INT,
                    dc.metadata
                FROM document_chunks dc
                WHERE 1 - (dc.embedding <=> query_embedding) > match_threshold
                AND (filter_book_id IS NULL OR dc.book_id = filter_book_id)
                ORDER BY dc.embedding <=> query_embedding
                LIMIT match_count;
            END;
            $$;
        """))
        
        print("✓ Created helper functions")
        
        print("\n" + "=" * 60)
        print("RAG Migration completed successfully!")
        print("=" * 60)
        print("\nTables created:")
        print("  - knowledge_embeddings (with vector index)")
        print("  - document_chunks (with vector index)")
        print("  - rag_queries")
        print("\nFunctions created:")
        print("  - search_similar_knowledge()")
        print("  - search_similar_documents()")
        print("\nNote: Remember to run 'pip install pgvector' first!")


async def rollback():
    """Drop RAG tables."""
    async with engine.begin() as conn:
        print("Rolling back RAG tables...")
        
        await conn.execute(text("DROP FUNCTION IF EXISTS search_similar_documents CASCADE"))
        print("✓ Dropped search_similar_documents")
        
        await conn.execute(text("DROP FUNCTION IF EXISTS search_similar_knowledge CASCADE"))
        print("✓ Dropped search_similar_knowledge")
        
        await conn.execute(text("DROP TABLE IF EXISTS rag_queries CASCADE"))
        print("✓ Dropped rag_queries")
        
        await conn.execute(text("DROP TABLE IF EXISTS document_chunks CASCADE"))
        print("✓ Dropped document_chunks")
        
        await conn.execute(text("DROP TABLE IF EXISTS knowledge_embeddings CASCADE"))
        print("✓ Dropped knowledge_embeddings")
        
        print("\nRollback completed.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        asyncio.run(rollback())
    else:
        asyncio.run(migrate())

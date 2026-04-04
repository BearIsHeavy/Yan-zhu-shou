# RAG Integration Guide

RAG (Retrieval-Augmented Generation) integration for enhanced AI analysis with textbook context.

---

## Overview

RAG enhances AI responses by:
1. **Retrieving** relevant textbook content and knowledge points
2. **Augmenting** the LLM prompt with this context
3. **Generating** answers with specific citations

### Before RAG vs After RAG

| Scenario | Without RAG | With RAG |
|----------|-------------|----------|
| **Wrong Question Analysis** | "You struggle with quadratic equations" | "You struggle with the discriminant formula (b²-4ac). Review textbook P.124 Example 3." |
| **Student Q&A** | "The quadratic formula is x = (-b ± √(b²-4ac)) / 2a" | "According to your textbook 'High School Math' P.123, the quadratic formula is..." |
| **Recommendations** | "Practice more quadratic equations" | "Complete exercises 5-8 on P.130 of your textbook, then try quiz #234-238" |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    RAG Pipeline                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  User Question/Wrong Answers                                 │
│         ↓                                                    │
│  ┌─────────────────┐                                        │
│  │ Embedding Service│ ← Generate query embedding            │
│  └────────┬────────┘                                        │
│           ↓                                                  │
│  ┌─────────────────┐                                        │
│  │Retrieval Service│ ← Search similar content               │
│  └────────┬────────┘                                        │
│           ↓                                                  │
│  ┌─────────────────┐                                        │
│  │  Vector Store   │ ← pgvector (PostgreSQL extension)      │
│  │  - knowledge_embeddings                                  │
│  │  - document_chunks                                       │
│  └────────┬────────┘                                        │
│           ↓                                                  │
│  ┌─────────────────┐                                        │
│  │  RAG Enhancer   │ ← Build context + Call LLM            │
│  └────────┬────────┘                                        │
│           ↓                                                  │
│  Response with citations                                     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Installation

### 1. Install Python Dependencies

```bash
uv pip install pgvector chromadb sentence-transformers
# or
pip install pgvector chromadb sentence-transformers
```

### 2. Enable pgvector Extension

```sql
-- Connect to your PostgreSQL database
psql -U api -d fastapi_db

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify installation
SELECT * FROM pg_extension WHERE extname = 'vector';
```

### 3. Run Database Migration

```bash
python db_scripts/migrations/010_add_rag_tables.py
```

### 4. Configure Environment

Edit `.env`:

```bash
# RAG Configuration
VECTOR_STORE_TYPE=pgvector

# Embedding Model (OpenAI)
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSION=1536

# Or use local model (Chinese optimized)
# EMBEDDING_MODEL_PATH=BAAI/bge-large-zh-v1.5

# RAG Settings
RAG_SEARCH_TOP_K=5
RAG_SIMILARITY_THRESHOLD=0.7
RAG_MAX_CONTEXT_TOKENS=4000

# Chunk Settings
CHUNK_SIZE=500
CHUNK_OVERLAP=50
```

---

## API Usage

### 1. Semantic Search

```bash
POST /api/rag/search?query=quadratic+formula&limit=10
```

**Response:**
```json
{
  "knowledge": [
    {
      "knowledge_id": 45,
      "name": "Quadratic Formula",
      "subject": "Mathematics",
      "content": "Formula for solving ax² + bx + c = 0",
      "similarity": 0.92,
      "description": "x = (-b ± √(b²-4ac)) / 2a"
    }
  ],
  "documents": [
    {
      "book_id": 3,
      "book_title": "High School Mathematics",
      "chapter": "Chapter 3: Quadratic Equations",
      "content": "The quadratic formula states that...",
      "page_number": 123,
      "similarity": 0.89
    }
  ]
}
```

### 2. RAG-Enhanced Analysis

```bash
POST /api/rag/analyze
Content-Type: application/json

{
  "wrong_questions": [
    {
      "question_no": 234,
      "category": "Algebra",
      "stem": "Solve x² - 5x + 6 = 0",
      "user_answer": "x = 2",
      "correct_ans_summary": "x = 2 or x = 3"
    }
  ],
  "subject": "Mathematics"
}
```

**Response:**
```json
{
  "weak_points": [
    {
      "knowledge": "Quadratic Formula",
      "description": "Student missed one of the two solutions",
      "textbook_ref": "High School Mathematics P.124",
      "error_count": 3
    }
  ],
  "error_patterns": ["Incomplete solution"],
  "recommendations": [
    {
      "type": "review",
      "action": "Review the quadratic formula derivation",
      "reference": "P.123-124",
      "estimated_time": "15 minutes"
    },
    {
      "type": "practice",
      "action": "Complete exercises 1-10",
      "reference": "P.130",
      "estimated_time": "30 minutes"
    }
  ],
  "summary": "Student understands the formula but often misses the second solution.",
  "context_used": {
    "knowledge_points_count": 3,
    "textbook_chunks_count": 2,
    "sources": [
      {"title": "High School Mathematics", "page": 123}
    ]
  }
}
```

### 3. RAG-Powered Q&A

```bash
POST /api/rag/answer?question=What%20is%20the%20quadratic%20formula?&subject=Mathematics
```

**Response:**
```json
{
  "question": "What is the quadratic formula?",
  "answer": "The quadratic formula is x = (-b ± √(b²-4ac)) / 2a. This formula gives the solutions to any quadratic equation of the form ax² + bx + c = 0.\n\nAs shown in your textbook 'High School Mathematics' (P.123), the formula is derived by completing the square...",
  "sources": [
    {"title": "High School Mathematics", "chapter": "Chapter 3", "page": 123}
  ],
  "confidence": "high"
}
```

### 4. Vectorize a Book

```bash
POST /api/rag/books/1/vectorize
```

**Response:**
```json
{
  "success": true,
  "chunks": 45,
  "book_id": 1,
  "book_title": "High School Mathematics"
}
```

---

## Vectorization Workflow

### Step 1: Upload Book

```bash
POST /api/books/upload
# Upload PDF/Markdown/DOCX file
```

### Step 2: Vectorize Content

```bash
POST /api/rag/books/{book_id}/vectorize
```

This will:
1. Read the book content
2. Split into chunks (500 words each, 50 word overlap)
3. Generate embeddings for each chunk
4. Store in `document_chunks` table

### Step 3: Search & Analyze

Now the book content is available for:
- Semantic search
- RAG-enhanced analysis
- Q&A with citations

---

## Database Schema

### knowledge_embeddings

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| knowledge_id | INTEGER | FK to knowledge_points |
| content | TEXT | Original text |
| embedding | vector(1536) | Vector embedding |
| metadata | JSONB | Additional info |

### document_chunks

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| book_id | INTEGER | FK to user_books |
| chapter | VARCHAR(200) | Chapter name |
| content | TEXT | Chunk content |
| embedding | vector(1536) | Vector embedding |
| page_number | INTEGER | Page in original |
| chunk_index | INTEGER | Order in document |

### rag_queries

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| user_id | INTEGER | FK to User |
| query_text | TEXT | Original query |
| query_embedding | vector(1536) | Query vector |
| results_count | INTEGER | Results returned |
| response_type | VARCHAR(50) | analysis/qa/search |

---

## Configuration Options

### Embedding Models

| Model | Dimension | Language | Cost |
|-------|-----------|----------|------|
| text-embedding-3-small | 1536 | Multi | $ |
| text-embedding-3-large | 3072 | Multi | $$ |
| bge-large-zh | 1024 | Chinese | Free |
| m3e-base | 768 | Chinese | Free |

### Chunk Settings

```bash
# Larger chunks = more context, slower search
CHUNK_SIZE=500

# Overlap prevents losing context at boundaries
CHUNK_OVERLAP=50

# More results = better coverage, more tokens
RAG_SEARCH_TOP_K=5

# Higher threshold = more precise, fewer results
RAG_SIMILARITY_THRESHOLD=0.7
```

---

## Performance Tips

### 1. Index Optimization

```sql
-- Create index for faster similarity search
CREATE INDEX ON document_chunks 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

### 2. Batch Vectorization

```python
# Vectorize multiple books
for book_id in book_ids:
    await service.vectorize_book(book_id)
```

### 3. Cache Embeddings

Query embeddings are cached automatically. Repeated queries are instant.

### 4. Limit Context

```bash
# Reduce token usage
RAG_MAX_CONTEXT_TOKENS=4000
```

---

## Troubleshooting

### pgvector Not Found

```sql
-- Check if extension is installed
SELECT * FROM pg_extension WHERE extname = 'vector';

-- If not found, install:
CREATE EXTENSION vector;
```

### Embedding Service Fails

```bash
# Check OpenAI API key
echo $OPENAI_API_KEY

# Test connection
curl https://api.openai.com/v1/embeddings \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{"input": "test", "model": "text-embedding-3-small"}'
```

### No Results from Search

1. Check if books are vectorized: `SELECT count(*) FROM document_chunks;`
2. Lower similarity threshold: `RAG_SIMILARITY_THRESHOLD=0.5`
3. Verify embedding dimension matches

---

## Next Steps

1. **Vectorize existing books**: Run `/api/rag/books/{id}/vectorize` for all uploaded books
2. **Vectorize knowledge points**: Call `vectorize_knowledge_point()` for each knowledge point
3. **Test RAG analysis**: Use `/api/rag/analyze` with sample wrong questions
4. **Monitor queries**: Check `/api/rag/query-history` for usage patterns

---

## API Reference

See full API documentation at: http://localhost:8000/docs

Key endpoints:
- `/api/rag/search` - Semantic search
- `/api/rag/analyze` - RAG-enhanced analysis
- `/api/rag/answer` - Q&A with citations
- `/api/rag/books/{id}/vectorize` - Vectorize book

---

**Version**: 1.0  
**Created**: 2024-01-01  
**Author**: Development Team

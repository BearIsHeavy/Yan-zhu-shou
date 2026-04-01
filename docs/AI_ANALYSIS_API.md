# AI Analysis API Usage Guide

Complete guide for using the AI-powered wrong question analysis features.

---

## Table of Contents

1. [Overview](#overview)
2. [Setup](#setup)
3. [Knowledge Management](#knowledge-management)
4. [Book Upload & Parsing](#book-upload--parsing)
5. [Analysis Reports](#analysis-reports)
6. [API Examples](#api-examples)

---

## Overview

The AI Analysis module provides:

- **Knowledge Graph**: Hierarchical knowledge point management
- **Book Parsing**: Extract knowledge from textbooks (PDF/Markdown/DOCX)
- **Weak Point Analysis**: AI-powered analysis of wrong questions
- **Recommendations**: Personalized learning suggestions

---

## Setup

### 1. Install Dependencies

```bash
uv pip install openai tiktoken pypdf python-docx
# or
pip install openai tiktoken pypdf python-docx
```

### 2. Configure Environment

Edit `.env` file:

```bash
# Required for AI features
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4-turbo-preview

# Optional settings
AI_ANALYSIS_ENABLED=true
AI_MAX_TOKENS=4000
```

### 3. Run Database Migration

```bash
python db_scripts/migrations/009_add_ai_analysis_tables.py
```

---

## Knowledge Management

### Get Knowledge Tree

```bash
GET /api/knowledge/tree?subject=Mathematics
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "Algebra",
    "subject": "Mathematics",
    "difficulty": 3,
    "children": [
      {
        "id": 2,
        "name": "Linear Equations",
        "difficulty": 2,
        "children": []
      }
    ]
  }
]
```

### Create Knowledge Point

```bash
POST /api/knowledge
Content-Type: application/json

{
  "name": "Quadratic Equations",
  "subject": "Mathematics",
  "difficulty": 3,
  "description": "Equations of the form ax² + bx + c = 0",
  "parent_id": 2
}
```

### Link Question to Knowledge

```bash
POST /api/knowledge/questions/link
Content-Type: application/json

{
  "question_no": 123,
  "knowledge_id": 5,
  "weight": 0.8
}
```

---

## Book Upload & Parsing

### Upload Book

```bash
POST /api/books/upload
Content-Type: multipart/form-data

file: [your-book.pdf]
title: "High School Mathematics"
```

**Response:**
```json
{
  "id": 1,
  "title": "High School Mathematics",
  "file_path": "uploads/books/1/abc123.pdf",
  "status": 0,
  "message": "Upload successful. Processing will begin shortly."
}
```

### List User Books

```bash
GET /api/books?status=2&limit=10
```

**Status Codes:**
- `0`: Pending
- `1`: Processing
- `2`: Completed
- `3`: Failed

### Parse Book (Extract Knowledge)

```bash
POST /api/books/{book_id}/parse
Content-Type: application/x-www-form-urlencoded

subject=Mathematics
```

**Response:**
```json
{
  "book_id": 1,
  "status": "completed",
  "result": {
    "success": true,
    "content_length": 50000,
    "chapters": [...],
    "knowledge_tree": {...}
  }
}
```

### Get Book Content

```bash
GET /api/books/{book_id}/content
```

---

## Analysis Reports

### Generate Weak Point Report

```bash
POST /api/reports/generate/weak-points
```

**Response:**
```json
{
  "report_id": 1,
  "report_type": "weak_point",
  "generated_at": "2024-01-01T10:00:00",
  "analysis": {
    "statistical_analysis": {
      "by_category": {
        "total_errors": 25,
        "categories": {
          "Algebra": {"error_count": 10, "percentage": 40.0},
          "Geometry": {"error_count": 15, "percentage": 60.0}
        }
      },
      "error_patterns": {
        "by_type": {"single_choice": 15, "multiple_choice": 10},
        "mastery_rate": 25.5
      }
    },
    "ai_analysis": {
      "weak_points": [
        {"knowledge": "Quadratic Equations", "error_count": 5, "confidence": 0.85}
      ],
      "error_patterns": ["Sign errors", "Formula misapplication"],
      "recommendations": ["Review quadratic formula", "Practice factoring"],
      "summary": "Student struggles with quadratic equations..."
    }
  }
}
```

### Generate Recommendation Report

```bash
POST /api/reports/generate/recommendations
```

**Response:**
```json
{
  "report_id": 2,
  "report_type": "recommendation",
  "recommendations": {
    "user_level": "intermediate",
    "weak_points": [
      {"knowledge": "Quadratic Equations", "error_count": 5, "priority": 1}
    ],
    "recommendations": [
      {
        "type": "practice",
        "priority": 1,
        "knowledge": "Quadratic Equations",
        "action": "Practice 5 questions on quadratic equations",
        "question_ids": [101, 102, 103, 104, 105],
        "estimated_time": "20 minutes"
      },
      {
        "type": "review",
        "priority": 2,
        "knowledge": "Factoring",
        "action": "Review factoring techniques",
        "estimated_time": "15 minutes"
      }
    ]
  }
}
```

### Get Latest Reports

```bash
# Get latest weak point report
GET /api/reports/latest/weak-points

# Get latest recommendation report
GET /api/reports/latest/recommendations
```

### List All Reports

```bash
GET /api/reports?report_type=weak_point&limit=10
```

---

## API Examples

### Complete Workflow Example

```python
import httpx

BASE_URL = "http://localhost:8000"
TOKEN = "your-access-token"

headers = {"Authorization": f"Bearer {TOKEN}"}

async with httpx.AsyncClient() as client:
    # 1. Upload a textbook
    with open("math_book.pdf", "rb") as f:
        response = await client.post(
            f"{BASE_URL}/api/books/upload",
            headers=headers,
            files={"file": f},
            data={"title": "Math Textbook"}
        )
    book_id = response.json()["id"]
    
    # 2. Parse the book to extract knowledge
    response = await client.post(
        f"{BASE_URL}/api/books/{book_id}/parse",
        headers=headers,
        data={"subject": "Mathematics"}
    )
    
    # 3. Generate weak point analysis
    response = await client.post(
        f"{BASE_URL}/api/reports/generate/weak-points",
        headers=headers
    )
    analysis = response.json()
    
    # 4. Generate recommendations
    response = await client.post(
        f"{BASE_URL}/api/reports/generate/recommendations",
        headers=headers
    )
    recommendations = response.json()
    
    # 5. Get study plan
    print("Your personalized study plan:")
    for rec in recommendations["recommendations"]["recommendations"]:
        print(f"- {rec['action']} ({rec['estimated_time']})")
```

### cURL Examples

```bash
# Upload book
curl -X POST "http://localhost:8000/api/books/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@math_book.pdf" \
  -F "title=Math Textbook"

# Generate analysis
curl -X POST "http://localhost:8000/api/reports/generate/weak-points" \
  -H "Authorization: Bearer $TOKEN"

# Get knowledge tree
curl -X GET "http://localhost:8000/api/knowledge/tree?subject=Mathematics" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Error Handling

### Common Error Responses

**400 Bad Request:**
```json
{
  "detail": "Unsupported file type. Allowed: PDF, Markdown, DOCX"
}
```

**403 Forbidden:**
```json
{
  "detail": "Insufficient permissions"
}
```

**404 Not Found:**
```json
{
  "detail": "Book not found"
}
```

**503 Service Unavailable:**
```json
{
  "detail": "AI analysis is not available (missing API key)"
}
```

---

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| Book Upload | 10 per hour |
| AI Analysis | 5 per hour |
| Knowledge CRUD | 100 per hour |

---

## Best Practices

1. **Upload books during off-peak hours** for faster processing
2. **Cache analysis reports** - they're valid for 1 hour
3. **Use subject filter** when extracting knowledge for better accuracy
4. **Review AI recommendations** before presenting to students
5. **Monitor token usage** if using paid AI API

---

## Troubleshooting

### AI Analysis Not Working

1. Check `OPENAI_API_KEY` in `.env`
2. Verify API key is valid: `https://platform.openai.com/api-keys`
3. Check network connectivity to OpenAI

### Book Parsing Fails

1. Ensure file is under 50MB
2. Check file format (PDF/Markdown/DOCX)
3. Verify file is not corrupted

### Knowledge Tree Empty

1. Ensure book has been processed (status = 2)
2. Check AI analysis completed successfully
3. Try with different subject filter

---

## Support

For issues or questions:
- Check API docs: http://localhost:8000/docs
- Review logs: `logs/` directory
- Contact: dev@example.com

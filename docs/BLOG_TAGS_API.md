# Blog Tags API Documentation

The Blog Tags API allows users to categorize blog posts with tags and filter blogs by tags.

## Tag Constraints

- **Maximum tags per blog**: 5
- **Maximum tag length**: 10 characters per tag
- **Tag format**: Alphanumeric strings (no empty or whitespace-only tags)
- **Uniqueness**: Tags are unique across the system (case-sensitive)

---

## Endpoints

### List Blogs with Tag Filter

```http
GET /blogs?tags=python,fastapi
```

**Query Parameters:**
- `tags` (optional): Comma-separated list of tag names
  - Blogs must have **ALL** specified tags
  - Example: `?tags=python,fastapi` returns blogs tagged with both "python" AND "fastapi"

**Example:**
```bash
# Get blogs tagged with "python"
curl "http://localhost:8000/blogs?tags=python"

# Get blogs tagged with both "python" AND "fastapi"
curl "http://localhost:8000/blogs?tags=python,fastapi"

# Combine with other filters
curl "http://localhost:8000/blogs?tags=python&search=API&page_size=10"
```

**Response:**
```json
{
  "items": [
    {
      "blog_id": 1,
      "title": "FastAPI Tutorial",
      "tags": [
        {"tag_id": 1, "name": "python"},
        {"tag_id": 2, "name": "fastapi"}
      ],
      ...
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

---

### Create Blog with Tags

```http
POST /blogs
```

**Request Body:**
```json
{
  "title": "My Blog Post",
  "content": "# Content here",
  "content_type": "markdown",
  "is_published": true,
  "tags": ["python", "fastapi", "api"]
}
```

**Tag Validation:**
- Maximum 5 tags per blog
- Each tag max 10 characters
- Tags cannot be empty or whitespace

**Example:**
```bash
curl -X POST "http://localhost:8000/blogs" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "FastAPI Tutorial",
    "content": "# Getting Started with FastAPI",
    "tags": ["python", "fastapi", "web"]
  }'
```

**Error (too many tags):**
```json
{
  "detail": [
    {
      "type": "value_error",
      "msg": "Value error, Maximum 5 tags allowed",
      "loc": ["body", "tags"]
    }
  ]
}
```

**Error (tag too long):**
```json
{
  "detail": [
    {
      "type": "value_error",
      "msg": "Value error, Each tag must be at most 10 characters",
      "loc": ["body", "tags"]
    }
  ]
}
```

---

### Update Blog Tags

```http
PUT /blogs/{blog_id}
```

**Request Body:**
```json
{
  "tags": ["python", "updated"]
}
```

**Note:** Updating tags replaces all existing tags on the blog.

**Example:**
```bash
curl -X PUT "http://localhost:8000/blogs/1" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "tags": ["python", "fastapi", "updated"]
  }'
```

---

### List All Tags

```http
GET /blogs/tags
```

**Query Parameters:**
- `search` (optional): Filter tags by name (partial match)

**Example:**
```bash
# Get all tags
curl "http://localhost:8000/blogs/tags"

# Search for tags containing "py"
curl "http://localhost:8000/blogs/tags?search=py"
```

**Response:**
```json
{
  "items": [
    {"tag_id": 1, "name": "python"},
    {"tag_id": 5, "name": "pytorch"},
    {"tag_id": 3, "name": "fastapi"}
  ],
  "total": 3
}
```

---

### Get Blog with Tags

```http
GET /blogs/{blog_id}
```

The response includes the blog's tags:

```json
{
  "blog_id": 1,
  "title": "FastAPI Tutorial",
  "content": "...",
  "tags": [
    {"tag_id": 1, "name": "python"},
    {"tag_id": 2, "name": "fastapi"},
    {"tag_id": 3, "name": "web"}
  ],
  ...
}
```

---

## Database Schema

### `blog_tags` Table

| Column | Type | Description |
|--------|------|-------------|
| tag_id | INTEGER | Primary key |
| name | VARCHAR(10) | Unique tag name (max 10 chars) |
| created_at | DATETIME | Creation timestamp |

### `blog_tags_association` Table

| Column | Type | Description |
|--------|------|-------------|
| blog_id | INTEGER | Foreign key to blogs (composite PK) |
| tag_id | INTEGER | Foreign key to blog_tags (composite PK) |

---

## Tag Filtering Logic

When filtering by tags, blogs must have **ALL** specified tags:

- `?tags=python` → Blogs with "python" tag
- `?tags=python,fastapi` → Blogs with BOTH "python" AND "fastapi" tags
- `?tags=python,fastapi,web` → Blogs with ALL THREE tags

This is implemented using a SQL `GROUP BY` with `HAVING COUNT` to ensure exact matching.

---

## Migration

To add the tags system to an existing database:

```bash
python db_scripts/migrations/003_add_blog_tags.py
```

To rollback:

```bash
python db_scripts/migrations/003_add_blog_tags.py --rollback
```

---

## Best Practices

1. **Use consistent tagging**: Agree on common tags (e.g., "python" vs "Python")
2. **Keep tags short**: Max 10 characters encourages concise categorization
3. **Limit tags per blog**: Max 5 tags keeps categorization focused
4. **Search before creating**: Check existing tags to avoid duplicates

---

## Error Responses

| Status Code | Description |
|-------------|-------------|
| 400 | Tag validation failed (too many tags, tag too long, empty tag) |
| 404 | Blog or tag not found |
| 403 | Unauthorized to modify blog |

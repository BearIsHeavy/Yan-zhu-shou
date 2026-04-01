# Blog API Documentation

The Blog API allows users to create, share, and interact with HTML/Markdown blog posts.

## Base URL

```
/blogs
```

## Authentication

Most endpoints require authentication via JWT token. Include the token in the `Authorization` header:

```
Authorization: Bearer <your-token>
```

---

## Endpoints

### Blog Posts

#### List All Blogs
```http
GET /blogs
```

Query Parameters:
- `search` (optional): Search in title
- `user_id` (optional): Filter by author ID
- `content_type` (optional): Filter by content type (`markdown` or `html`)
- `sort_by` (optional): Sort field (`created_at`, `updated_at`, `view_count`, `like_count`)
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 20)

**Example:**
```bash
curl "http://localhost:8000/blogs?search=Python&page=1&page_size=10"
```

---

#### Get My Blogs
```http
GET /blogs/my
```

Returns all blogs created by the current user (including drafts).

**Requires authentication.**

---

#### Get Blog Statistics
```http
GET /blogs/stats
```

Returns statistics about blog posts (personal if authenticated, global otherwise).

Response:
```json
{
  "total_posts": 10,
  "total_views": 500,
  "total_likes": 50,
  "total_comments": 30,
  "published_count": 8,
  "draft_count": 2
}
```

---

#### Create Blog Post
```http
POST /blogs
```

**Requires authentication.**

Request Body:
```json
{
  "title": "My First Blog Post",
  "content": "# Hello World\n\nThis is my **first** blog post!",
  "content_type": "markdown",
  "is_published": true
}
```

Fields:
- `title` (required): 1-200 characters
- `content` (required): Blog content (HTML or Markdown)
- `content_type` (optional): `markdown` or `html` (default: `markdown`)
- `is_published` (optional): Publish immediately (default: `true`)

**Example:**
```bash
curl -X POST "http://localhost:8000/blogs" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My First Blog Post",
    "content": "# Hello World\n\nThis is my **first** blog post!",
    "content_type": "markdown",
    "is_published": true
  }'
```

---

#### Get Blog Post
```http
GET /blogs/{blog_id}
```

Increments view count on each access.

**Note:** Unpublished blogs are only accessible by their authors.

---

#### Update Blog Post
```http
PUT /blogs/{blog_id}
```

**Requires authentication and ownership.**

Request Body (all fields optional):
```json
{
  "title": "Updated Title",
  "content": "Updated content",
  "content_type": "html",
  "is_published": false
}
```

---

#### Delete Blog Post
```http
DELETE /blogs/{blog_id}
```

**Requires authentication and ownership.**

Returns `204 No Content` on success.

---

### Likes

#### Toggle Like
```http
POST /blogs/{blog_id}/like
```

**Requires authentication.**

- If not liked: Adds like
- If already liked: Removes like

**Cannot like your own blog.**

Response:
```json
{
  "has_liked": true,
  "like_count": 15
}
```

---

#### Get Like Status
```http
GET /blogs/{blog_id}/like
```

**Requires authentication.**

Returns current user's like status and total like count.

---

### Comments

#### List Comments
```http
GET /blogs/{blog_id}/comments
```

Query Parameters:
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 50)

Returns top-level comments with nested replies.

---

#### Create Comment
```http
POST /blogs/{blog_id}/comments
```

**Requires authentication.**

Request Body:
```json
{
  "content": "Great post! Very helpful.",
  "parent_id": null
}
```

Fields:
- `content` (required): 1-5000 characters
- `parent_id` (optional): Parent comment ID for replies

**Example (reply to comment):**
```json
{
  "content": "I agree!",
  "parent_id": 123
}
```

---

#### Update Comment
```http
PUT /blogs/comments/{comment_id}?content=Updated comment text
```

**Requires authentication and ownership.**

Query Parameters:
- `content` (required): New comment text

---

#### Delete Comment
```http
DELETE /blogs/comments/{comment_id}
```

**Requires authentication.**

Soft deletes the comment (marks as deleted, preserves for replies).

**Blog owners can delete any comment on their blog.**

---

## Database Schema

### Tables

#### `blogs`
| Column | Type | Description |
|--------|------|-------------|
| blog_id | INTEGER | Primary key |
| user_id | INTEGER | Foreign key to User |
| title | VARCHAR(200) | Blog title |
| content | TEXT | HTML or Markdown content |
| content_type | VARCHAR(20) | `markdown` or `html` |
| is_published | BOOLEAN | Publication status |
| view_count | INTEGER | Number of views |
| like_count | INTEGER | Number of likes |
| comment_count | INTEGER | Number of comments |
| created_at | DATETIME | Creation timestamp |
| updated_at | DATETIME | Last update timestamp |

#### `blog_likes`
| Column | Type | Description |
|--------|------|-------------|
| like_id | INTEGER | Primary key |
| blog_id | INTEGER | Foreign key to blogs |
| user_id | INTEGER | Foreign key to User |
| created_at | DATETIME | Like timestamp |

**Unique constraint:** One like per user per blog

#### `blog_comments`
| Column | Type | Description |
|--------|------|-------------|
| comment_id | INTEGER | Primary key |
| blog_id | INTEGER | Foreign key to blogs |
| user_id | INTEGER | Foreign key to User |
| parent_id | INTEGER | Parent comment (for replies) |
| content | TEXT | Comment text |
| is_deleted | BOOLEAN | Soft delete flag |
| created_at | DATETIME | Creation timestamp |
| updated_at | DATETIME | Last update timestamp |

---

## Setup

1. Run database migrations:
```bash
python db_scripts/init_db.py
```

2. Start the server:
```bash
uvicorn main:app --reload
```

3. Access interactive API docs:
```
http://localhost:8000/docs
```

---

## Error Responses

| Status Code | Description |
|-------------|-------------|
| 400 | Bad request (e.g., liking own blog) |
| 401 | Unauthorized (missing/invalid token) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not found |

---

## Rate Limiting

Currently, there are no rate limits on blog operations. Consider implementing rate limiting for production use.

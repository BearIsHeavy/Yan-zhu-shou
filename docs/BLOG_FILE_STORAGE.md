# Blog Content File Storage API Documentation

The Blog API now stores content as files (Markdown or HTML) instead of plain text in the database. Only the relative file path is stored in the database.

## File Storage

### Storage Location

Blog content files are stored in:
```
uploads/blogs/<user_id>/blog_<blog_id>_<uuid>.<ext>
```

Example:
```
uploads/blogs/123/blog_456_a1b2c3d4.md
```

### Supported File Types

- **Markdown**: `.md`, `.markdown`
- **HTML**: `.html`, `.htm`

### File Size Limit

Maximum file size: **5MB**

---

## API Changes

### Create Blog Post

```http
POST /blogs
Content-Type: multipart/form-data
```

**Form Fields:**
- `title` (required): Blog post title (1-200 characters)
- `content_file` (required): Markdown or HTML file
- `content_type` (optional): `markdown` or `html` (default: `markdown`)
- `is_published` (optional): `true` or `false` (default: `true`)
- `tags` (optional): Comma-separated tags (e.g., `python,fastapi,web`)

**Example (using curl):**
```bash
curl -X POST "http://localhost:8000/blogs" \
  -H "Authorization: Bearer <token>" \
  -F "title=My Blog Post" \
  -F "content_file=@post.md" \
  -F "content_type=markdown" \
  -F "is_published=true" \
  -F "tags=python,fastapi"
```

**Response:**
```json
{
  "blog_id": 1,
  "user_id": 123,
  "title": "My Blog Post",
  "content_file_path": "uploads/blogs/123/blog_1_a1b2c3d4.md",
  "content_type": "markdown",
  "is_published": true,
  "tags": [
    {"tag_id": 1, "name": "python"},
    {"tag_id": 2, "name": "fastapi"}
  ],
  ...
}
```

---

### Get Blog Post

```http
GET /blogs/{blog_id}
```

**Response:** Returns blog metadata (content is NOT included in this response).

```json
{
  "blog_id": 1,
  "title": "My Blog Post",
  "content_file_path": "uploads/blogs/123/blog_1_a1b2c3d4.md",
  "content_type": "markdown",
  ...
}
```

---

### Get Blog Content

```http
GET /blogs/{blog_id}/content
```

**Response:** Returns raw markdown/HTML content as plain text.

```markdown
# My Blog Post

This is the content of my blog post...
```

**Example:**
```bash
curl -X GET "http://localhost:8000/blogs/1/content" \
  -H "Authorization: Bearer <token>"
```

---

### Update Blog Post

```http
PUT /blogs/{blog_id}
Content-Type: multipart/form-data
```

**Form Fields (all optional):**
- `title`: New title
- `content_file`: New content file (replaces existing)
- `content_type`: New content type
- `is_published`: Publication status
- `tags`: Comma-separated tags

**Example:**
```bash
curl -X PUT "http://localhost:8000/blogs/1" \
  -H "Authorization: Bearer <token>" \
  -F "title=Updated Title" \
  -F "content_file=@updated-post.md" \
  -F "tags=python,updated"
```

---

### Delete Blog Post

```http
DELETE /blogs/{blog_id}
```

**Effect:** Deletes both the database record and the content file.

---

## Migration

To update an existing database:

```bash
python db_scripts/migrations/004_add_blog_content_file_path.py
```

**What this migration does:**
1. Adds `content_file_path` column (VARCHAR(255))
2. Drops old `content` column (TEXT)

**Warning:** Existing blog content in the `content` column will be lost. Run this migration only on fresh databases or after backing up data.

To rollback:
```bash
python db_scripts/migrations/004_add_blog_content_file_path.py --rollback
```

---

## Database Schema

### blogs Table

| Column | Type | Description |
|--------|------|-------------|
| blog_id | INTEGER | Primary key |
| user_id | INTEGER | Foreign key to User |
| title | VARCHAR(200) | Blog title |
| content_file_path | VARCHAR(255) | **Relative path to content file** |
| content_type | VARCHAR(20) | `markdown` or `html` |
| is_published | BOOLEAN | Publication status |
| view_count | INTEGER | View count |
| like_count | INTEGER | Like count |
| comment_count | INTEGER | Comment count |
| created_at | DATETIME | Creation timestamp |
| updated_at | DATETIME | Last update timestamp |

---

## Benefits of File Storage

1. **Better Performance**: Database stays small, queries are faster
2. **Easier Backups**: Files can be backed up separately
3. **CDN Ready**: Files can be served from a CDN
4. **No Size Limits**: Database text fields have limits; files don't
5. **Version Control**: Content files can be tracked in git

---

## Security

- Files are stored with unique UUID-based names
- Path traversal attacks are prevented
- Users can only access published blogs or their own drafts
- File type validation prevents malicious uploads

---

## Error Responses

| Status Code | Description |
|-------------|-------------|
| 400 | Invalid file type or file size exceeds 5MB |
| 401 | Unauthorized (missing/invalid token) |
| 403 | Forbidden (accessing draft without permission) |
| 404 | Blog or content file not found |

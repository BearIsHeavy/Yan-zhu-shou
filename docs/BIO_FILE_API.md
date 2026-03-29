# Self-Introduction (Bio File) API Documentation

The Self-Introduction API allows users to upload, view, and delete their personal introduction in Markdown format.

## Base URL

```
/users/bio
```

## Authentication

All endpoints require authentication via JWT token. Include the token in the `Authorization` header:

```
Authorization: Bearer <your-token>
```

---

## Endpoints

### Upload Self-Introduction

```http
POST /users/bio
```

**Content-Type:** `multipart/form-data`

**Request:**
- `file` (required): Markdown file (.md or .markdown)
  - Maximum size: 1MB
  - Allowed extensions: `.md`, `.markdown`

**Response:**
```json
{
  "file_path": "uploads/bios/123/a1b2c3d4e5f6.md",
  "file_name": "my-intro.md",
  "uploaded_at": "2026-03-29T10:30:00"
}
```

**Example (using curl):**
```bash
curl -X POST "http://localhost:8000/users/bio" \
  -H "Authorization: Bearer <your-token>" \
  -F "file=@/path/to/your-intro.md"
```

**Notes:**
- Uploading a new file will replace any existing self-introduction
- The file is stored with a unique filename to prevent conflicts

---

### Get My Self-Introduction

```http
GET /users/bio
```

**Response:** Returns raw Markdown content as plain text.

**Example:**
```bash
curl -X GET "http://localhost:8000/users/bio" \
  -H "Authorization: Bearer <your-token>"
```

**Response:**
```markdown
# Hello!

I'm John Doe, a software engineer...
```

**Error (no bio uploaded):**
```json
{
  "detail": "No self-introduction uploaded yet"
}
```

---

### Get Another User's Self-Introduction

```http
GET /users/bio/{user_id}
```

**Path Parameters:**
- `user_id`: The ID of the user whose bio you want to view

**Response:** Returns raw Markdown content as plain text.

**Example:**
```bash
curl -X GET "http://localhost:8000/users/bio/42" \
  -H "Authorization: Bearer <your-token>"
```

**Error (user has no bio):**
```json
{
  "detail": "User has not uploaded a self-introduction"
}
```

---

### Delete Self-Introduction

```http
DELETE /users/bio
```

**Response:** `204 No Content` on success

**Example:**
```bash
curl -X DELETE "http://localhost:8000/users/bio" \
  -H "Authorization: Bearer <your-token>"
```

**Error (no bio to delete):**
```json
{
  "detail": "No self-introduction to delete"
}
```

---

## File Storage

### Storage Location

Files are stored in the `uploads/bios/` directory, organized by user ID:

```
uploads/
└── bios/
    ├── 1/
    │   └── a1b2c3d4e5f6.md
    ├── 2/
    │   └── f7e8d9c0b1a2.md
    └── 123/
        └── 3g4h5i6j7k8l.md
```

### Storage Format

- **Relative paths** are stored in the database (e.g., `uploads/bios/123/a1b2c3d4e5f6.md`)
- Files are stored with **unique UUID-based filenames** to prevent conflicts
- Original filenames are preserved in the response for user reference

---

## Validation

### File Type Validation

Only Markdown files are accepted:
- `.md`
- `.markdown`

### File Size Limit

Maximum file size: **1MB**

### Security

- Files are stored with unique names to prevent overwriting
- Users can only delete their own bio files
- Path traversal attacks are prevented through validation

---

## Error Responses

| Status Code | Description |
|-------------|-------------|
| 400 | Invalid file type or file size exceeds limit |
| 401 | Unauthorized (missing/invalid token) |
| 404 | Bio file not found or user has no bio |
| 500 | Server error during file operations |

---

## Example Workflow

### 1. Upload your self-introduction

```bash
# Create your intro.md file
cat > intro.md << EOF
# About Me

Hi! I'm a passionate developer...
EOF

# Upload it
curl -X POST "http://localhost:8000/users/bio" \
  -H "Authorization: Bearer <your-token>" \
  -F "file=@intro.md"
```

### 2. View your self-introduction

```bash
curl -X GET "http://localhost:8000/users/bio" \
  -H "Authorization: Bearer <your-token>"
```

### 3. View another user's self-introduction

```bash
curl -X GET "http://localhost:8000/users/bio/42" \
  -H "Authorization: Bearer <your-token>"
```

### 4. Update your self-introduction

Simply upload a new file (it will replace the old one):

```bash
curl -X POST "http://localhost:8000/users/bio" \
  -H "Authorization: Bearer <your-token>" \
  -F "file=@updated-intro.md"
```

### 5. Delete your self-introduction

```bash
curl -X DELETE "http://localhost:8000/users/bio" \
  -H "Authorization: Bearer <your-token>"
```

---

## Database Schema

### User Table Changes

| Column | Type | Description |
|--------|------|-------------|
| bio_file_path | VARCHAR(255) | Relative path to markdown file (nullable) |

---

## Migration

To add the `bio_file_path` column to an existing database:

```bash
python db_scripts/migrations/002_add_user_bio_file.py
```

To rollback:

```bash
python db_scripts/migrations/002_add_user_bio_file.py --rollback
```

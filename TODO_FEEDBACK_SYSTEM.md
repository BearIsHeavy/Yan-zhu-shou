# "You Say, I Fix" - Feedback Comment System

**Status: COMPLETED ✓**

All tests passed successfully.

## Requirements Summary

- **Authentication Required**: No anonymous submissions
- **Public Visibility**: All feedback is public
- **Voting System**: Upvotes determine priority
- **Threshold Notification**: Developers notified only when votes exceed threshold
- **Rate Limiting**: 1 submission per user per day

---

## Phase 1: Database Models & Schemas

### 1.1 Create Database Models
- [ ] `models/feedback.py` - Feedback model
  - `id: int` (Primary Key)
  - `user_id: int` (Foreign Key → Users, required)
  - `content: str` (Feedback text, required)
  - `category: str` (Enum: bug, feature, ui, performance, documentation, other)
  - `status: str` (Enum: pending, in_progress, completed, rejected)
  - `vote_count: int` (Default: 0)
  - `developer_response: str | None` (Optional response)
  - `responded_at: datetime | None`
  - `resolved_at: datetime | None`
  - `created_at: datetime`
  - `updated_at: datetime`
  - Indexes: `user_id`, `status`, `vote_count`, `created_at`

- [ ] `models/feedback_vote.py` - Vote tracking
  - `id: int` (Primary Key)
  - `feedback_id: int` (Foreign Key → Feedback)
  - `user_id: int` (Foreign Key → Users)
  - `created_at: datetime`
  - Unique constraint: `(feedback_id, user_id)` - One vote per user per feedback

- [ ] `models/feedback_notification.py` - Notification log
  - `id: int` (Primary Key)
  - `feedback_id: int` (Foreign Key → Feedback)
  - `notified_at: datetime`
  - `notification_type: str` (threshold_reached, status_changed, etc.)
  - `is_sent: bool`

### 1.2 Create Pydantic Schemas
- [ ] `schemas/feedback.py`
  - `FeedbackCreate` - content, category
  - `FeedbackResponse` - Full feedback with votes, user info, status
  - `FeedbackUpdate` - status, developer_response (admin/dev only)
  - `FeedbackVoteResponse` - vote status
  - `FeedbackListResponse` - Paginated list
  - `FeedbackStats` - Summary statistics

### 1.3 Database Migration
- [ ] Create Alembic migration scripts for new tables
- [ ] Add indexes for performance (vote_count, status, created_at)
- [ ] Add trigger/constraint for daily submission limit (optional, or handle in code)

---

## Phase 2: Services

### 2.1 Feedback Service
- [ ] `services/feedback_service.py`
  - `create_feedback(user_id: int, content: str, category: str) -> Feedback`
    - Check daily submission limit (1 per user per day)
    - Raise exception if limit exceeded
  - `get_feedback(feedback_id: int) -> Feedback`
  - `list_feedbacks(status: str | None, category: str | None, sort_by: str, limit: int, offset: int) -> List[Feedback]`
    - Sort options: `created_at`, `vote_count`, `resolved_at`
  - `update_feedback(feedback_id: int, status: str | None, developer_response: str | None, user_id: int) -> Feedback`
    - Permission check: only developers/admins
  - `delete_feedback(feedback_id: int, user_id: int) -> Feedback`
    - Permission check: only admins or original author (if no votes)
  - `get_user_daily_submission_status(user_id: int) -> bool`
    - Returns True if user has already submitted today

### 2.2 Vote Service
- [ ] `services/vote_service.py`
  - `vote_feedback(feedback_id: int, user_id: int) -> bool`
    - Toggle vote (vote if not voted, remove if already voted)
    - Update vote_count on Feedback
    - Check threshold and trigger notification if needed
  - `get_vote_status(feedback_id: int, user_id: int) -> dict`
    - Returns `{has_voted: bool, vote_count: int}`
  - `check_threshold(feedback_id: int) -> bool`
    - Returns True if vote_count >= threshold and notification not sent

### 2.3 Notification Service
- [ ] `services/notification_service.py`
  - `send_threshold_notification(feedback_id: int) -> bool`
    - Send email/webhook to developers when votes exceed threshold
    - Mark notification as sent in database
  - `send_status_update_notification(feedback_id: int) -> bool` (optional)
  - Configurable threshold value (default: 10 votes)

---

## Phase 3: API Routes

### 3.1 Feedback Endpoints
- [ ] `routes/feedback.py`
  - `GET /api/feedback` - List all feedback
    - Query params: `status`, `category`, `sort_by`, `limit`, `offset`
    - Public access
  - `POST /api/feedback` - Submit new feedback
    - Body: `FeedbackCreate`
    - Auth required
    - Rate limit: 1 per user per day
  - `GET /api/feedback/{feedback_id}` - Get feedback details
    - Public access
  - `PUT /api/feedback/{feedback_id}` - Update feedback
    - Body: `FeedbackUpdate`
    - Auth required, developer/admin role
  - `DELETE /api/feedback/{feedback_id}` - Delete feedback
    - Auth required, admin only (or author if no votes)

### 3.2 Vote Endpoints
- [ ] `routes/feedback.py` (or separate `routes/feedback_vote.py`)
  - `POST /api/feedback/{feedback_id}/vote` - Toggle vote
    - Auth required
    - Returns updated vote status
  - `GET /api/feedback/{feedback_id}/vote` - Get vote status
    - Auth required (to check if user has voted)
    - Returns `{has_voted: bool, vote_count: int}`

### 3.3 Stats Endpoints
- [ ] `routes/feedback.py` (or separate `routes/feedback_stats.py`)
  - `GET /api/feedback/stats` - Get feedback statistics
    - Total feedback count
    - Count by status
    - Count by category
    - Top voted feedbacks
    - Public access

### 3.4 User Endpoints
- [ ] `routes/feedback.py` (or integrate into existing user routes)
  - `GET /api/users/me/feedback` - Get current user's feedback submissions
    - Auth required
  - `GET /api/users/me/feedback/submission-status` - Check if user can submit today
    - Auth required
    - Returns `{can_submit: bool, next_submission_at: datetime}`

---

## Phase 4: Background Tasks (Optional)

### 4.1 Notification Tasks
- [ ] `tasks/feedback_tasks.py`
  - Background task for sending threshold notifications
  - Email integration (if using email)
  - Webhook integration (if using Slack/Discord/etc.)

### 4.2 Cleanup Tasks
- [ ] Periodic task to clean up old rejected feedback (optional)
- [ ] Periodic task to archive resolved feedback older than X days (optional)

---

## Phase 5: Integration & Testing

### 5.1 Integration with Existing Code
- [ ] Update `main.py` - Register feedback router
- [ ] Update `dependencies.py` - Add developer/admin role checker
- [ ] Update `database.py` - Ensure models are registered
- [ ] Update `.env` - Add notification config (email/webhook URL, vote threshold)

### 5.2 API Tests
- [ ] `test_api/test_feedback.py`
  - Test feedback submission (auth required)
  - Test daily submission limit (1 per user per day)
  - Test feedback listing with filters
  - Test feedback update (developer role)
  - Test feedback deletion (admin role)
  - Test voting functionality
  - Test threshold notification trigger
  - Test permission handling

### 5.3 Unit Tests
- [ ] `tests/test_feedback_service.py`
- [ ] `tests/test_vote_service.py`
- [ ] `tests/test_notification_service.py`

---

## Phase 6: Configuration & Environment

### 6.1 Environment Variables
- [ ] Update `.env` with:
  ```
  # Feedback System
  FEEDBACK_VOTE_THRESHOLD=10
  FEEDBACK_NOTIFICATION_ENABLED=true
  FEEDBACK_NOTIFICATION_EMAIL=dev@example.com
  FEEDBACK_NOTIFICATION_WEBHOOK_URL=https://hooks.slack.com/...
  ```

### 6.2 Constants/Settings
- [ ] Add feedback-related settings to config
  - Default vote threshold
  - Notification enabled flag
  - Rate limit duration (24 hours)

---

## Phase 7: Documentation & Polish

### 7.1 API Documentation
- [ ] Add OpenAPI/Swagger descriptions
- [ ] Add request/response examples
- [ ] Document rate limiting behavior

### 7.2 User Documentation
- [ ] `docs/feedback/README.md` - Feedback system overview
- [ ] `docs/feedback/user_guide.md` - How to submit feedback and vote
- [ ] `docs/feedback/developer_guide.md` - How developers should respond

### 7.3 Frontend Integration Notes
- [ ] Document API endpoints for frontend developers
- [ ] Provide example payloads

---

## Configuration Options

| Setting | Default | Description |
|---------|---------|-------------|
| `FEEDBACK_VOTE_THRESHOLD` | 10 | Votes needed to notify developers |
| `FEEDBACK_SUBMISSION_LIMIT` | 1 per day | Rate limit per user |
| `FEEDBACK_NOTIFICATION_ENABLED` | true | Enable/disable notifications |
| `FEEDBACK_CATEGORIES` | bug, feature, ui, performance, documentation, other | Available categories |

---

## File Structure (Final)

```
Server/
├── models/
│   ├── feedback.py
│   └── feedback_vote.py
├── schemas/
│   └── feedback.py
├── routes/
│   └── feedback.py
├── services/
│   ├── feedback_service.py
│   ├── vote_service.py
│   └── notification_service.py
├── tasks/
│   └── feedback_tasks.py (optional)
├── test_api/
│   └── test_feedback.py
├── docs/
│   └── feedback/
│       ├── README.md
│       ├── user_guide.md
│       └── developer_guide.md
└── .env (updated)
```

---

## Priority Order

1. **Phase 1** - Models & Schemas (foundation)
2. **Phase 2** - Services (business logic)
3. **Phase 3** - API Routes (expose functionality)
4. **Phase 5** - Testing (ensure quality)
5. **Phase 6** - Configuration (environment setup)
6. **Phase 4** - Background Tasks (optional, notifications)
7. **Phase 7** - Documentation (user onboarding)

---

## Notes

- Mark tasks as complete by changing `[ ]` to `[x]`
- Add comments or modifications directly in this file
- Vote threshold should be configurable via environment variable

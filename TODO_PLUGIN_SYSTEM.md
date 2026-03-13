# Creative Workshop & Plugin System - Implementation Plan

## Phase 1: Database Models & Schemas

### 1.1 Create Database Models
- [ ] `models/plugin.py` - Plugin model
  - Fields: id, name, description, version, author_id, downloads, rating, code_hash, manifest_json, created_at, updated_at, is_active
- [ ] `models/user_plugin.py` - User-Plugin relationship
  - Fields: user_id, plugin_id, is_installed, is_enabled, config_json, installed_at
- [ ] `models/plugin_comment.py` - Workshop comment model
  - Fields: id, plugin_id, user_id, content, ai_response, status, created_at

### 1.2 Create Pydantic Schemas
- [ ] `schemas/plugin.py`
  - PluginCreate, PluginResponse, PluginUpdate
  - UserPluginResponse, UserPluginConfig
  - PluginCommentCreate, PluginCommentResponse

### 1.3 Database Migration
- [ ] Create Alembic migration scripts for new tables
- [ ] Add foreign key constraints and indexes

---

## Phase 2: Plugin Runtime & Security

### 2.1 Plugin Sandbox
- [ ] `utils/sandbox.py` - Secure execution environment
  - Restricted imports whitelist
  - Execution timeout control
  - Memory limit enforcement
- [ ] `plugins/runtime/executor.py` - Plugin code executor
  - Safe class instantiation
  - Method invocation with error handling

### 2.2 Plugin Base Class
- [ ] `plugins/runtime/base.py` - PluginBase abstract class
  - `process_comment(comment: str, context: dict) -> str`
  - `on_install(user_id: int) -> bool`
  - `on_uninstall(user_id: int) -> bool`
  - `get_config_schema() -> dict` (optional)

### 2.3 Plugin Storage
- [ ] `plugins/storage/` - Directory for uploaded plugin files
- [ ] `plugins/registry.py` - In-memory plugin registry/cache
  - Load/unload plugins
  - Version management

---

## Phase 3: Services

### 3.1 Plugin Manager Service
- [ ] `services/plugin_manager.py`
  - `upload_plugin(file, manifest, author_id) -> Plugin`
  - `get_plugin(plugin_id) -> Plugin`
  - `list_plugins(filters) -> List[Plugin]`
  - `install_plugin(plugin_id, user_id) -> bool`
  - `uninstall_plugin(plugin_id, user_id) -> bool`
  - `toggle_plugin(plugin_id, user_id, enabled: bool) -> bool`
  - `get_user_plugins(user_id) -> List[UserPlugin]`

### 3.2 Workshop Service
- [ ] `services/workshop.py`
  - `submit_comment(plugin_id, user_id, content) -> PluginComment`
  - `get_comments(plugin_id, limit, offset) -> List[PluginComment]`
  - `get_comment_status(comment_id) -> PluginComment`
  - `queue_comment_for_processing(comment_id)`

### 3.3 AI Processor Service
- [ ] `services/ai_processor.py`
  - Integrate with existing AI service (or create new)
  - `process_comment_request(comment, plugin_context) -> str`
  - Background task queue integration
  - Response caching layer

---

## Phase 4: API Routes

### 4.1 Plugin Endpoints
- [ ] `routes/plugins.py`
  - `GET /api/plugins` - Browse plugins (with search/filter)
  - `GET /api/plugins/{plugin_id}` - Get plugin details
  - `POST /api/plugins` - Upload new plugin (auth required)
  - `POST /api/plugins/{plugin_id}/install` - Install plugin (auth required)
  - `DELETE /api/plugins/{plugin_id}/install` - Uninstall plugin (auth required)
  - `PUT /api/plugins/{plugin_id}/toggle` - Enable/disable (auth required)

### 4.2 Workshop Comment Endpoints
- [ ] `routes/workshop.py`
  - `GET /api/plugins/{plugin_id}/comments` - Get comments
  - `POST /api/plugins/{plugin_id}/comments` - Submit comment (auth required)
  - `GET /api/comments/{comment_id}/status` - Check processing status

### 4.3 User Plugin Endpoints
- [ ] `routes/user_plugins.py`
  - `GET /api/users/me/plugins` - Get user's installed plugins
  - `GET /api/users/me/plugins/{plugin_id}/config` - Get config
  - `PUT /api/users/me/plugins/{plugin_id}/config` - Update config

---

## Phase 5: Background Tasks

### 5.1 Comment Processing Queue
- [ ] `tasks/plugin_tasks.py`
  - Celery/ARQ task for AI comment processing
  - Retry logic for failed processing
  - Status update callbacks

### 5.2 Plugin Validation
- [ ] Background task for plugin code validation
- [ ] Automated security scanning

---

## Phase 6: Integration & Testing

### 6.1 Integration with Existing Code
- [ ] Update `main.py` - Register new routers
- [ ] Update `dependencies.py` - Add plugin-related dependencies
- [ ] Update `database.py` - Ensure models are registered

### 6.2 API Tests
- [ ] `test_api/test_plugins.py`
  - Test plugin upload, install, uninstall
  - Test permission handling
  - Test plugin listing and filtering
- [ ] `test_api/test_workshop.py`
  - Test comment submission
  - Test AI processing flow
  - Test status polling

### 6.3 Unit Tests
- [ ] `tests/test_plugin_manager.py`
- [ ] `tests/test_sandbox.py`
- [ ] `tests/test_ai_processor.py`

---

## Phase 7: Documentation & Polish

### 7.1 API Documentation
- [ ] Add OpenAPI/Swagger descriptions
- [ ] Add request/response examples

### 7.2 User Documentation
- [ ] `docs/plugins/README.md` - Plugin system overview
- [ ] `docs/plugins/creator_guide.md` - How to create plugins
- [ ] `docs/plugins/user_guide.md` - How to use plugins

### 7.3 Example Plugin
- [ ] Create a sample plugin demonstrating the API
- [ ] Include in `plugins/examples/`

---

## Open Questions (To Be Decided)

- [ ] **Plugin Format**: Python code or configuration-based (JSON/YAML with prompts)?
- [ ] **Review Process**: Manual approval before publishing or instant publish?
- [ ] **Payment System**: Support paid plugins or all free?
- [ ] **AI Provider**: Which AI service to integrate (OpenAI, Anthropic, local)?
- [ ] **Execution Model**: Real-time plugin execution or pre-defined responses only?
- [ ] **Storage**: Local file storage or cloud storage (S3, etc.) for plugin files?
- [ ] **Rate Limits**: What limits for AI processing per user?

---

## File Structure (Final)

```
Server/
├── models/
│   ├── plugin.py
│   ├── user_plugin.py
│   └── plugin_comment.py
├── schemas/
│   └── plugin.py
├── routes/
│   ├── plugins.py
│   ├── workshop.py
│   └── user_plugins.py
├── services/
│   ├── plugin_manager.py
│   ├── workshop.py
│   └── ai_processor.py
├── tasks/
│   └── plugin_tasks.py
├── plugins/
│   ├── runtime/
│   │   ├── base.py
│   │   └── executor.py
│   ├── storage/
│   ├── registry.py
│   └── examples/
├── utils/
│   └── sandbox.py
├── test_api/
│   ├── test_plugins.py
│   └── test_workshop.py
└── docs/
    └── plugins/
        ├── README.md
        ├── creator_guide.md
        └── user_guide.md
```

---

## Priority Order

1. **Phase 1** - Models & Schemas (foundation)
2. **Phase 2** - Plugin Runtime & Security (core functionality)
3. **Phase 3** - Services (business logic)
4. **Phase 4** - API Routes (expose functionality)
5. **Phase 5** - Background Tasks (async processing)
6. **Phase 6** - Testing (ensure quality)
7. **Phase 7** - Documentation (user onboarding)

---

## Notes

- Mark tasks as complete by changing `[ ]` to `[x]`
- Add comments or modifications directly in this file
- Move tasks between phases if needed during implementation

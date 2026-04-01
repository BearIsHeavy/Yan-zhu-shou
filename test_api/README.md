# YanZhuShou API Test Suite

自动化 API 测试套件，用于测试 YanZhuShou 后端的所有 API 端点。

---

## 目录结构

```
test_api/
├── main.py              # 主测试入口
├── test_base.py         # 测试基础工具类
├── test_user.py         # 用户 API 测试
├── test_blog.py         # 博客 API 测试
├── test_feedback.py     # 反馈 API 测试
├── test_question.py     # 题库 API 测试
├── test_mistake.py      # 错题本 API 测试
├── test_rag.py          # RAG 模块 API 测试
└── README.md            # 测试文档
```

---

## 前置要求

### 1. 安装依赖

```bash
pip install httpx
```

### 2. 启动服务

确保以下服务正在运行：

```bash
# FastAPI 服务器
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Redis (可选，用于缓存)
redis-server

# PostgreSQL
# 确保数据库已启动并可访问
```

### 3. 准备测试数据

运行测试数据准备脚本：

```bash
# 从项目根目录运行
python test_api/setup_test_data.py

# 或进入 test_api 目录运行
cd test_api
python setup_test_data.py
```

**注意**: 脚本会自动检测并使用 `.env` 中的数据库配置。

### 4. 测试用户

测试使用以下预配置的用户账号：

- **邮箱**: test@example.com
- **密码**: 123456

**注意**: 请确保该用户已存在于数据库中。如不存在，请先手动注册。

---

## 测试数据管理

### 准备测试数据

在运行测试之前，先准备测试数据：

```bash
python test_api/setup_test_data.py
```

这会创建：
- 3 篇博客文章（包含点赞和评论）
- 3 条反馈（包含投票和通知）
- 2 个题库（包含 5 道题目）
- 错题本记录
- 知识点（包含层级关系）
- 学校信息（包含用户映射）
- 测试书籍记录
- 分析报告

### 清理测试数据

测试完成后清理数据：

```bash
python test_api/setup_test_data.py --cleanup
```

### 测试流程

完整的测试流程：

```bash
# 1. 准备测试数据
python test_api/setup_test_data.py

# 2. 运行测试
python -m test_api.main

# 3. 清理测试数据
python test_api/setup_test_data.py --cleanup
```

### 脚本选项

```bash
# 只显示帮助
python test_api/setup_test_data.py --help

# 准备数据
python test_api/setup_test_data.py

# 清理数据
python test_api/setup_test_data.py --cleanup

# 准备后立即清理（用于验证脚本）
python test_api/setup_test_data.py --both
```

---

## 使用方法

### 运行所有测试

```bash
# 方式 1: 从项目根目录运行（推荐）
python -m test_api.main

# 方式 2: 进入 test_api 目录运行
cd test_api
python main.py
```

### 运行特定模块测试

```bash
# 只测试用户 API
python -m test_api.main "User APIs"

# 只测试博客和反馈 API
python -m test_api.main "Blog APIs" "Feedback APIs"

# 只测试 RAG 模块
python -m test_api.main "RAG APIs"
```

### 运行单个测试文件

```bash
python -m test_api.test_user
python -m test_api.test_blog
python -m test_api.test_feedback
python -m test_api.test_question
python -m test_api.test_mistake
python -m test_api.test_rag
```

---

## 测试模块说明

### 1. User APIs (`test_user.py`)

测试用户相关接口：

| 端点 | 方法 | 说明 |
|------|------|------|
| `/users/me` | GET | 获取当前用户信息 |
| `/users/me` | PUT | 更新用户信息 |
| `/users/bio` | GET | 获取用户自我介绍 |
| `/users/bio/{user_id}` | GET | 获取指定用户自我介绍 |

### 2. Blog APIs (`test_blog.py`)

测试博客相关接口：

| 端点 | 方法 | 说明 |
|------|------|------|
| `/blogs` | GET | 获取博客列表 |
| `/blogs/stats` | GET | 获取博客统计 |
| `/blogs/my` | GET | 获取我的博客 |
| `/blogs` | POST | 创建博客 |
| `/blogs/{id}` | GET | 获取博客详情 |
| `/blogs/{id}/like` | POST/GET | 点赞/获取点赞状态 |
| `/blogs/{id}/comments` | GET/POST | 评论列表/发表评论 |
| `/blogs/tags` | GET | 获取标签列表 |
| `/blogs/{id}` | DELETE | 删除博客（清理） |

### 3. Feedback APIs (`test_feedback.py`)

测试反馈相关接口：

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/feedback` | GET | 获取反馈列表 |
| `/api/feedback/stats` | GET | 获取反馈统计 |
| `/api/feedback` | POST | 创建反馈 |
| `/api/feedback/{id}` | GET | 获取反馈详情 |
| `/api/feedback/{id}/vote` | POST/GET | 投票/获取投票状态 |
| `/api/feedback/me/submissions` | GET | 获取我的提交 |
| `/api/feedback/me/submission-status` | GET | 获取提交状态 |
| `/api/feedback/{id}` | DELETE | 删除反馈（清理） |

### 4. Question Bank APIs (`test_question.py`)

测试题库相关接口：

| 端点 | 方法 | 说明 |
|------|------|------|
| `/question_banks` | GET | 获取题库列表 |
| `/question_banks/book` | POST | 创建题库 |
| `/question_banks/{id}` | GET | 获取题库详情 |
| `/question_banks/{id}/questions` | GET | 获取题目列表 |
| `/question_banks/{id}` | DELETE | 删除题库（清理） |

### 5. Mistake Notebook APIs (`test_mistake.py`)

测试错题本相关接口：

| 端点 | 方法 | 说明 |
|------|------|------|
| `/mistake-notebook/categories` | GET | 获取分类列表 |
| `/mistake-notebook/stats` | GET | 获取统计信息 |
| `/mistake-notebook/questions` | GET | 获取错题列表 |
| `/practice/submit-answer` | POST | 提交答案 |
| `/practice/start-session` | POST | 开始练习 |

### 6. RAG APIs (`test_rag.py`)

测试 RAG 模块接口：

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/knowledge/tree` | GET | 获取知识树 |
| `/api/knowledge` | GET | 获取知识点列表 |
| `/api/books` | GET | 获取书籍列表 |
| `/api/books/upload` | POST | 上传书籍 |
| `/api/rag/books/{id}/vectorize` | POST | 向量化书籍 |
| `/api/rag/search` | POST | 语义搜索 |
| `/api/reports` | GET | 获取报告列表 |
| `/api/reports/summary` | GET | 获取报告摘要 |
| `/api/books/{id}` | DELETE | 删除书籍（清理） |

---

## 输出示例

```
======================================================================
                    YanZhuShou API Test Suite
======================================================================
Started at: 2024-01-01 10:00:00
Base URL: http://127.0.0.1:8000
Test User: test@example.com
======================================================================

──────────────────────────────────────────────────────────────────────
  Testing: User APIs
──────────────────────────────────────────────────────────────────────

  ✓ PASS - login: Login successful
  ✓ PASS - test_get_current_user: User: test@example.com
  ✓ PASS - test_update_user: User updated successfully
  ...

======================================================================
                         TEST SUMMARY
======================================================================

  Total Modules: 6
  Passed: 6
  Failed: 0
  Total Time: 15.23s

  Success Rate: 100.0%

  Module Results:
  ──────────────────────────────────────────────────────────────────
    ✓ User APIs                            2.15s
    ✓ Blog APIs                            3.42s
    ✓ Feedback APIs                        2.87s
    ✓ Question Bank APIs                   1.95s
    ✓ Mistake Notebook APIs                1.56s
    ✓ RAG APIs                             3.28s
  ──────────────────────────────────────────────────────────────────
======================================================================
```

---

## 测试规则

1. **登录优先**: 所有测试模块首先尝试登录，登录失败则跳过该模块
2. **自动清理**: 创建的测试数据（博客、反馈等）会在测试结束时删除
3. **错误处理**: 单个测试失败不影响其他测试执行
4. **状态码处理**: 某些端点返回 404 也是可接受的（如获取不存在的资源）

---

## 常见问题

### Q: 测试失败 "Login failed: 401"
**A**: 测试用户不存在或密码错误。请确保 `test@example.com / 123456` 用户已创建。

### Q: 测试失败 "Connection refused"
**A**: FastAPI 服务器未启动。请运行：
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Q: 如何添加新测试模块？
**A**: 
1. 创建新的测试文件 `test_api/test_xxx.py`
2. 继承 `BaseTest` 类
3. 在 `main.py` 中导入并添加到 `TEST_MODULES` 列表

### Q: 如何测试需要管理员权限的接口？
**A**: 修改测试用户的 `role` 字段为 `admin`：
```sql
UPDATE "User" SET role = 'admin' WHERE email = 'test@example.com';
```

---

## 贡献指南

添加新测试时请遵循以下规范：

1. **命名规范**: 测试方法以 `test_` 开头
2. **日志记录**: 使用 `self._log_result(endpoint, success, message)` 记录结果
3. **异常处理**: 每个测试方法都应该捕获异常并记录
4. **资源清理**: 创建的测试数据应在测试结束时删除

示例：
```python
async def test_example(self):
    """Test example endpoint."""
    try:
        response = await self.client.get(
            "/api/example",
            headers=self._get_headers()
        )
        
        if response.status_code == 200:
            self._log_result("GET /api/example", True, "Success")
        else:
            self._log_result("GET /api/example", False, f"Status: {response.status_code}")
    except Exception as e:
        self._log_result("GET /api/example", False, str(e))
```

---

## 许可证

与主项目相同。

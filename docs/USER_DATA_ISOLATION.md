# 用户数据隔离功能 - 使用说明

## 功能概述

实现了用户级别的数据隔离，确保：
- 每个用户只能访问自己的数据
- 重合数据只存储一份（去重）
- 支持数据过滤和查询

## 数据库迁移

### 1. 启动 PostgreSQL

```bash
# 使用 Docker 启动
docker run -d --name postgres \
  -e POSTGRES_USER=api \
  -e POSTGRES_PASSWORD=api \
  -e POSTGRES_DB=fastapi_db \
  -p 5432:5432 \
  postgres:16-alpine
```

### 2. 运行迁移

```bash
cd /Users/quanqing/Repository/YanZhuShou/Server
source .venv/bin/activate

# 运行迁移（会清空现有 school_info 数据）
python db_scripts/migrations/008_add_user_school_mapping.py
```

**注意**：迁移会执行以下操作：
- 清空 `school_info` 表
- 创建 `user_school_mapping` 表
- 添加索引和约束

### 3. 回滚迁移（可选）

```bash
python db_scripts/migrations/008_add_user_school_mapping.py --rollback
```

## 数据处理

### 方式 1：命令行处理（简单模式）

使用 `data_fetcher/process_data.py` 处理数据（无用户映射）：

```bash
cd /Users/quanqing/Repository/YanZhuShou/Server
source .venv/bin/activate

# 处理数据（直接插入 school_info 表）
python data_fetcher/process_data.py Info
```

### 方式 2：使用服务层（带用户映射）

使用 `services/school_info_service.py` 处理数据（推荐）：

```bash
# 为用户 ID=1 处理数据
python -c "
import asyncio
from services import process_school_data
asyncio.run(process_school_data('Info', user_id=1))
"

# 为用户 ID=2 处理数据
python -c "
import asyncio
from services import process_school_data
asyncio.run(process_school_data('Info', user_id=2))
"
```

**说明**：
- `data_fetcher/process_data.py` - 简单脚本，直接插入数据到 `school_info` 表
- `services/school_info_service.py` - 服务层，包含用户映射逻辑（推荐）

### API 调用（待实现）

```bash
# 前端传入 curl 命令，后端自动处理
curl -X POST "http://localhost:8000/school-info/fetch" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "curl_command": "...",
    "mode": "all",
    "pages": 10
  }'
```

## API 端点

所有查询端点现在都返回**当前用户专属的数据**：

| 端点 | 功能 | 用户隔离 |
|------|------|---------|
| `GET /school-info/schools` | 获取学校列表 | ✅ |
| `GET /school-info/schools/{id}` | 获取学校详情 | ✅ |
| `GET /school-info/filters/cities` | 获取城市列表 | ✅ |
| `GET /school-info/filters/schools` | 获取学校列表 | ✅ |
| `GET /school-info/filters/majors` | 获取专业列表 | ✅ |

### 示例

```bash
# 用户 A 查询上海的学校
curl "http://localhost:8000/school-info/schools?city=上海" \
  -H "Authorization: Bearer TOKEN_A"

# 用户 B 查询上海的学校（看到的数据可能不同）
curl "http://localhost:8000/school-info/schools?city=上海" \
  -H "Authorization: Bearer TOKEN_B"
```

## 数据隔离原理

### 数据库表结构

```sql
-- school_info: 共享数据表
CREATE TABLE school_info (
    id VARCHAR(64) PRIMARY KEY,
    school_name VARCHAR(100),
    city VARCHAR(50),
    -- ... 其他字段
);

-- user_school_mapping: 用户映射表
CREATE TABLE user_school_mapping (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    school_id VARCHAR(64) NOT NULL,
    created_at TIMESTAMP DEFAULT now(),
    UNIQUE(user_id, school_id),
    FOREIGN KEY (school_id) REFERENCES school_info(id)
);
```

### 查询逻辑

```sql
-- 用户 A 查询所有学校
SELECT s.* FROM school_info s
JOIN user_school_mapping m ON s.id = m.school_id
WHERE m.user_id = A

-- 用户 A 查询上海的学校
SELECT s.* FROM school_info s
JOIN user_school_mapping m ON s.id = m.school_id
WHERE m.user_id = A AND s.city = '上海'
```

## 数据去重示例

```
用户 A 插入：[学校 1, 学校 2, 学校 3]
用户 B 插入：[学校 2, 学校 3, 学校 4]

school_info 表（实际存储）:
┌──────┬─────────┐
│ id   │ name    │
├──────┼─────────┤
│ 1    │ 学校 1   │ ← A 独有
│ 2    │ 学校 2   │ ← A 和 B 共享
│ 3    │ 学校 3   │ ← A 和 B 共享
│ 4    │ 学校 4   │ ← B 独有
└──────┴─────────┘

user_school_mapping 表:
┌─────────┬───────────┐
│ user_id │ school_id │
├─────────┼───────────┤
│ A       │ 1         │
│ A       │ 2         │
│ A       │ 3         │
│ B       │ 2         │
│ B       │ 3         │
│ B       │ 4         │
└─────────┴───────────┘

查询结果:
- A 查询 → 返回 [学校 1, 学校 2, 学校 3] (3 条)
- B 查询 → 返回 [学校 2, 学校 3, 学校 4] (3 条)
- 物理存储 → 4 条（去重节省 2 条）
```

## 测试步骤

### 1. 准备测试数据

```bash
# 为用户 1 处理数据
python data_fetcher/process_data.py Info --user-id 1

# 为用户 2 处理相同的数据
python data_fetcher/process_data.py Info --user-id 2
```

### 2. 启动应用

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 测试用户隔离

```bash
# 获取用户 1 的 token
TOKEN_1=$(curl -X POST "http://localhost:8000/users/login" \
  -d "username=user1@example.com&password=password" | jq -r '.access_token')

# 获取用户 2 的 token
TOKEN_2=$(curl -X POST "http://localhost:8000/users/login" \
  -d "username=user2@example.com&password=password" | jq -r '.access_token')

# 用户 1 查询学校数量
curl "http://localhost:8000/school-info/schools?page=1&page_size=1" \
  -H "Authorization: Bearer $TOKEN_1" | jq '.total'

# 用户 2 查询学校数量（应该相同）
curl "http://localhost:8000/school-info/schools?page=1&page_size=1" \
  -H "Authorization: Bearer $TOKEN_2" | jq '.total'
```

## 注意事项

1. **用户认证**：所有查询端点都需要有效的 JWT token
2. **数据权限**：用户只能访问自己的数据，无法访问其他用户的数据
3. **数据去重**：相同 ID 的数据只存储一份，多个用户可以共享
4. **孤儿数据**：删除用户映射不会删除 school_info 中的数据（年度归档）

## 故障排除

### 问题：查询返回空数据

**原因**：用户还没有关联任何学校数据

**解决**：
```bash
# 为该用户处理数据
python data_fetcher/process_data.py Info --user-id <USER_ID>
```

### 问题：迁移失败

**原因**：数据库未运行或连接失败

**解决**：
```bash
# 检查 PostgreSQL 是否运行
docker ps | grep postgres

# 重启 PostgreSQL
docker restart postgres
```

### 问题：认证失败

**原因**：Token 过期或无效

**解决**：重新登录获取新 token

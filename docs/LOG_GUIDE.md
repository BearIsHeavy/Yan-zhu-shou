# 日志查看指南

## 日志文件位置

### 1. 用户任务日志

```
logs/fetch/user_{user_id}_{timestamp}.log
```

记录每个任务的完整执行过程。

### 2. Curl 执行日志

```
logs/fetch/fetch_{timestamp}.log
```

记录每次 curl 请求的详细信息。

### 3. 错误日志

```
logs/fetch/user_{user_id}_error.log
```

记录任务失败的详细错误信息。

---

## 日志示例

### 成功任务日志

```log
[2026-03-31 14:30:00] ==========================================
[2026-03-31 14:30:00] 任务开始：user_id=1, mode=all, pages=10
[2026-03-31 14:30:00] 创建任务：mode=all, pages=10
[2026-03-31 14:30:00] ✓ Curl command saved to data_fetcher/curl_command.txt
[2026-03-31 14:30:01] 状态：pending → running
[2026-03-31 14:30:01] Step 1: 执行 get_info.sh mode=all pages=10
[2026-03-31 14:30:15] get_info.sh 返回：exit_code=0
[2026-03-31 14:30:15] ✓ get_info.sh 完成
[2026-03-31 14:30:15] 输出：✓ Page 0 fetched... (共 10 页)
[2026-03-31 14:30:15] Step 2: 执行 process_school_data user_id=1
[2026-03-31 14:30:16] ✓ Database tables initialized.
[2026-03-31 14:30:16] ✓ Found 10 JSON files
[2026-03-31 14:30:18] ✓ process_school_data 完成
[2026-03-31 14:30:18] 结果：inserted=180, updated=20, skipped=0
[2026-03-31 14:30:18] ✓ 任务完成：成功处理 200 条数据
[2026-03-31 14:30:18] 状态：running → success
```

### 失败任务日志

```log
[2026-03-31 14:35:00] ==========================================
[2026-03-31 14:35:00] 任务开始：user_id=1, mode=all, pages=10
[2026-03-31 14:35:00] 创建任务：mode=all, pages=10
[2026-03-31 14:35:00] ✓ Curl command saved to data_fetcher/curl_command.txt
[2026-03-31 14:35:01] 状态：pending → running
[2026-03-31 14:35:01] Step 1: 执行 get_info.sh mode=all pages=10
[2026-03-31 14:35:02] get_info.sh 返回：exit_code=1
[2026-03-31 14:35:02] ✗ 错误：Fetch failed: curl: (6) Could not resolve host: yz.chsi.com.cn
[2026-03-31 14:35:02] ✗ 异常：Exception: Fetch failed: curl: (6) Could not resolve host: yz.chsi.com.cn
[2026-03-31 14:35:02] 状态：running → failed
```

### Curl 执行日志

```log
[2026-03-31 14:30:01] ==========================================
[2026-03-31 14:30:01] Fetch started
[2026-03-31 14:30:01]   Start: 0
[2026-03-31 14:30:01]   Page Size: 20
[2026-03-31 14:30:01]   Output: Info/0.json
[2026-03-31 14:30:01]   Curl command file: data_fetcher/curl_command.txt
[2026-03-31 14:30:01] ✓ Curl command loaded
[2026-03-31 14:30:01] Executing curl command...
[2026-03-31 14:30:01]   URL: https://yz.chsi.com.cn/sytj/stu/tjyxqexxcx.action
[2026-03-31 14:30:02] ✓ Success: HTTP 200
[2026-03-31 14:30:02]   Output saved to: Info/0.json
[2026-03-31 14:30:02]   File size: 5234 bytes
```

---

## 查看日志命令

### 实时查看最新日志

```bash
# 查看用户 1 的最新日志
tail -f logs/fetch/user_1_*.log

# 查看最新 100 行
tail -n 100 logs/fetch/user_1_*.log
```

### 查找特定错误

```bash
# 查找所有错误
grep "✗" logs/fetch/*.log

# 查找特定用户的错误
grep "Exception" logs/fetch/user_1_*.log
```

### 查看今天的日志

```bash
# 查找今天生成的日志
ls -la logs/fetch/$(date +%Y%m%d)*
```

### 统计成功/失败次数

```bash
# 统计成功次数
grep -c "✓ 任务完成" logs/fetch/user_*.log

# 统计失败次数
grep -c "✗ 异常" logs/fetch/user_*.log
```

---

## 常见错误排查

### 错误 1：Curl 命令执行失败

**日志显示**：
```
✗ 错误：Fetch failed: curl exit code 1
✗ 异常：Exception: Fetch failed: curl: (6) Could not resolve host
```

**原因**：网络连接问题或域名无法解析

**解决**：
1. 检查网络连接
2. 检查 Cookie 是否过期
3. 重新从浏览器复制 curl 命令

---

### 错误 2：数据处理失败

**日志显示**：
```
Step 2: 执行 process_school_data user_id=1
✗ 异常：JSONDecodeError: Expecting value: line 1 column 1
```

**原因**：JSON 文件格式不正确

**解决**：
1. 检查 `Info/` 目录下的 JSON 文件
2. 查看 `fetch_*.log` 确认 curl 是否成功
3. 重新获取数据

---

### 错误 3：数据库连接失败

**日志显示**：
```
✗ 异常：OperationalError: could not connect to server
```

**原因**：PostgreSQL 未运行

**解决**：
```bash
# 检查 PostgreSQL 状态
docker ps | grep postgres

# 启动 PostgreSQL
docker start postgres
```

---

## 日志文件管理

### 清理旧日志

```bash
# 删除 7 天前的日志
find logs/fetch -name "*.log" -mtime +7 -delete

# 保留最近 10 个日志文件
cd logs/fetch && ls -t user_1_*.log | tail -n +11 | xargs rm -f
```

### 日志文件大小

```bash
# 查看日志文件总大小
du -sh logs/fetch/

# 查看最大的日志文件
du -ah logs/fetch/*.log | sort -rh | head -10
```

---

## 总结

| 日志类型 | 文件位置 | 用途 |
|---------|---------|------|
| 用户任务日志 | `user_{id}_{timestamp}.log` | 查看任务执行过程 |
| Curl 执行日志 | `fetch_{timestamp}.log` | 查看 curl 请求详情 |
| 错误日志 | `user_{id}_error.log` | 查看失败原因 |

**建议**：
1. 任务失败时首先查看 `user_{id}_error.log`
2. 排查网络问题时查看 `fetch_{timestamp}.log`
3. 监控任务进度时实时查看 `tail -f user_{id}_*.log`

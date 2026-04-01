# data_fetcher 使用说明

## 目录结构

```
data_fetcher/
├── fetch.sh              # 主要脚本（使用）
├── get_info_manual.sh    # 手动参考模板
└── Info/                 # 输出目录
```

## 使用方法

### 1. 通过 API 调用（推荐）

前端传入完整的 curl 命令：

```javascript
const response = await fetch('/school-info/fetch', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    curl_command: "curl 'https://yz.chsi.com.cn/...' -b 'JSESSIONID=xxx; ...'",
    mode: 'all',
    pages: 10
  })
});
```

### 2. 手动调用脚本

```bash
cd data_fetcher

# 获取单页
./fetch.sh "curl 'https://...' -b 'JSESSIONID=xxx; ...'" 0

# 获取所有页（10 页）
./fetch.sh "curl 'https://...' -b 'JSESSIONID=xxx; ...'" all 10
```

## 工作原理

1. **前端传入 curl 命令**：包含完整的 headers 和 Cookie
2. **脚本替换参数**：自动替换 `start` 和 `pageSize` 参数
3. **执行 curl**：获取数据并保存到 `Info/{page_num}.json`
4. **处理数据**：调用 `process_school_data()` 处理 JSON 并入库

## Cookie 说明

**重要**：curl 命令中的 Cookie 会过期，需要定期更新。

### 获取最新 Cookie

1. 打开浏览器访问：https://yz.chsi.com.cn/sytj/tjyx/qecx.action
2. 打开开发者工具（F12）→ Network
3. 找到 `tjyxqexxcx.action` 请求
4. 右键 → Copy → Copy as cURL
5. 复制整个 curl 命令到前端

### Cookie 格式

```bash
-b 'JSESSIONID=ABC123; CHSICLTID=xxx; _gid=xxx; ...'
```

## 输出文件

```
Info/
├── 0.json    # 第 0 页数据
├── 1.json    # 第 1 页数据
└── ...
```

每个 JSON 文件包含 20 条记录（由 `pageSize=20` 决定）。

## 错误处理

### 错误 1：Cookie 过期

**现象**：
```
✗ Page 0 failed (start=0, HTTP 401)
```

**解决**：更新 curl 命令中的 Cookie

### 错误 2：网络超时

**现象**：
```
✗ Page 0 failed (start=0, HTTP 000)
```

**解决**：检查网络连接，稍后重试

### 错误 3：JSON 格式错误

**现象**：
```
✗ Error loading Info/0.json: JSONDecodeError
```

**解决**：检查 JSON 文件内容，确认 curl 是否成功

## 日志文件

```
logs/fetch/
├── user_1_20260331_*.log    # 用户任务日志
├── user_1_error.log         # 错误日志
└── fetch_20260331_*.log     # curl 执行日志
```

查看最新日志：
```bash
tail -f logs/fetch/user_1_*.log
```

## 高级用法

### 自定义页大小

修改脚本中的 `PAGE_SIZE` 变量：

```bash
# 在 fetch.sh 中
PAGE_SIZE=50  # 每页 50 条记录
```

### 并发获取（不推荐）

```bash
# 后台运行多个页面
./fetch.sh "curl ..." 0 &
./fetch.sh "curl ..." 1 &
./fetch.sh "curl ..." 2 &
wait
```

**注意**：可能会被服务器限制，建议顺序执行。

## 故障排查

### 1. 检查脚本权限

```bash
chmod +x fetch.sh
```

### 2. 测试 curl 命令

```bash
# 直接执行 curl 命令（不通过脚本）
curl 'https://yz.chsi.com.cn/...' -b 'JSESSIONID=xxx' --data-raw 'start=0&pageSize=20'
```

### 3. 查看输出文件

```bash
# 检查文件是否存在
ls -lh Info/

# 查看文件内容
head -50 Info/0.json
```

### 4. 检查日志

```bash
# 查看最新错误
cat logs/fetch/user_*_error.log

# 查看任务执行日志
cat logs/fetch/user_1_*.log
```

## 最佳实践

1. **定期更新 Cookie** - 每次使用前从浏览器复制最新 curl 命令
2. **限制页数** - 每次获取不超过 20 页，避免被服务器限制
3. **添加延迟** - 脚本已内置 3 秒延迟，不要移除
4. **错误重试** - 失败后等待 5 分钟再重试
5. **备份数据** - 定期备份 `Info/` 目录和数据库

## 清理命令

```bash
# 清理临时 JSON 文件
rm -rf Info/*.json

# 清理日志文件
rm -rf logs/fetch/*.log

# 保留错误日志
find logs/fetch -name "*_error.log" -prune -o -name "*.log" -delete
```

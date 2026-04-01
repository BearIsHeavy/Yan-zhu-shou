# AI 错题分析功能 - 工作流程详解

本文档详细说明 AI 错题分析功能的完整工作流程，包括用户操作、后端处理、数据流转等。

---

## 目录

1. [系统架构概览](#系统架构概览)
2. [核心功能流程](#核心功能流程)
   - [书籍上传与知识提取](#1-书籍上传与知识提取)
   - [错题分析与薄弱点识别](#2-错题分析与薄弱点识别)
   - [学习推荐生成](#3-学习推荐生成)
3. [数据流转详解](#数据流转详解)
4. [API 调用时序](#api 调用时序)
5. [数据库操作](#数据库操作)

---

## 系统架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│                        前端应用 (Frontend)                       │
│  - 用户上传书籍                                                  │
│  - 查看分析报告                                                  │
│  - 获取学习推荐                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/HTTPS
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI 后端 (Backend)                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    API Routes Layer                      │   │
│  │  /api/books/*    /api/knowledge/*    /api/reports/*     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   Services Layer                         │   │
│  │  BookService  KnowledgeService  ReportService            │   │
│  │  WeakPointAnalyzer  RecommendationEngine                 │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    AI Layer                              │   │
│  │  LLMClient (OpenAI API)  BookParser                     │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ SQL
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      PostgreSQL 数据库                          │
│  - knowledge_points      - question_knowledge                   │
│  - user_books            - analysis_reports                     │
│  - user_question_logs    - qb_questions                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ API Calls
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    OpenAI API (External)                         │
│  - GPT-4 Turbo                                                   │
│  - 知识提取                                                      │
│  - 薄弱点分析                                                    │
│  - 推荐生成                                                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 核心功能流程

### 1. 书籍上传与知识提取

#### 用户操作流程

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  用户    │     │  前端    │     │  后端    │     │  数据库  │
└────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │                │
     │ 1. 选择书籍文件 │                │                │
     │───────────────>│                │                │
     │                │                │                │
     │                │ 2. POST 上传   │                │
     │                │───────────────>│                │
     │                │                │                │
     │                │                │ 3. 保存文件    │
     │                │                │───────────────>│
     │                │                │                │
     │                │                │ 4. 创建记录    │
     │                │                │───────────────>│
     │                │                │                │
     │                │ 5. 返回 book_id │                │
     │                │<───────────────│                │
     │ 6. 显示上传成功 │                │                │
     │<───────────────│                │                │
     │                │                │                │
     │ 7. 触发解析请求 │                │                │
     │───────────────>│                │                │
     │                │                │                │
     │                │ 8. POST 解析   │                │
     │                │───────────────>│                │
     │                │                │                │
     │                │                │ 9. 读取文件    │
     │                │                │───────────────>│
     │                │                │                │
     │                │                │ 10. AI 提取知识 │
     │                │                │───────────────>│
     │                │                │                │
     │                │                │ 11. 更新状态   │
     │                │                │───────────────>│
     │                │                │                │
     │                │ 12. 返回结果   │                │
     │                │<───────────────│                │
     │ 13. 显示知识树 │                │                │
     │<───────────────│                │                │
     │                │                │                │
```

#### 后端处理流程

**步骤 1: 文件上传 (`POST /api/books/upload`)**

```python
# books/routes/books.py
async def upload_book(
    file: UploadFile,
    title: Optional[str],
    db: AsyncSession,
    current_user: models.User
):
    # 1. 读取文件内容
    file_content = await file.read()
    
    # 2. 验证文件
    # - 检查是否为空
    # - 验证文件类型 (PDF/Markdown/DOCX)
    # - 验证文件大小 (< 50MB)
    
    # 3. 创建服务实例
    service = BookUploadService(db, current_user.user_id)
    
    # 4. 保存文件并创建数据库记录
    book = await service.upload_book(
        file_content=file_content,
        original_filename=file.filename,
        title=title
    )
    
    # 5. 返回 book_id
    return {"id": book.id, "status": "pending"}
```

**步骤 2: 书籍解析 (`POST /api/books/{book_id}/parse`)**

```python
# books/routes/books.py
async def parse_book(
    book_id: int,
    subject: Optional[str],
    db: AsyncSession,
    current_user: models.User
):
    # 1. 获取书籍信息
    service = BookUploadService(db, current_user.user_id)
    book = await service.get_book(book_id)
    
    # 2. 更新状态为 processing
    await service.update_book_status(book_id, BookStatusEnum.PROCESSING)
    
    # 3. 解析书籍内容
    parser = BookParserService(db)
    
    # 3.1 读取文件内容
    content = parser.read_file_content(book.file_path)
    
    # 3.2 提取章节结构 (Markdown)
    if book.file_type == 'markdown':
        chapters = parser.extract_chapters_markdown(content)
    
    # 4. AI 提取知识树
    if AIAnalysisConfig.is_available():
        knowledge_tree = await parser.extract_knowledge_tree(
            content=content,
            subject=subject
        )
    
    # 5. 更新状态为 completed
    await service.update_book_status(
        book_id,
        BookStatusEnum.COMPLETED,
        knowledge_tree=knowledge_tree
    )
    
    return {"status": "completed", "knowledge_tree": knowledge_tree}
```

**AI 知识提取详细流程**

```python
# books/services/book_parser_service.py
async def extract_knowledge_tree(
    self,
    content: str,
    subject: Optional[str]
) -> Dict[str, Any]:
    # 1. 准备 Prompt
    system_prompt = """Extract a hierarchical knowledge tree from the educational content.
    Return JSON structure:
    {
        "subject": "subject name",
        "topics": [
            {
                "name": "topic name",
                "subtopics": [...],
                "key_concepts": ["concept1", "concept2"]
            }
        ]
    }"""
    
    # 2. 调用 LLM API
    response = await self.llm.chat([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Extract from: {content[:10000]}..."}
    ])
    
    # 3. 解析 JSON 响应
    knowledge_tree = json.loads(response)
    
    return knowledge_tree
```

**数据库操作**

```python
# 创建书籍记录
book = UserBook(
    user_id=user_id,
    title="Math Textbook",
    file_path="uploads/books/1/abc123.pdf",
    file_type="pdf",
    file_size=1024000,
    status=0,  # PENDING
)
db.add(book)
await db.commit()

# 更新状态
book.status = 2  # COMPLETED
book.knowledge_tree = json.dumps(knowledge_tree)
book.processed_at = datetime.utcnow()
await db.commit()
```

---

### 2. 错题分析与薄弱点识别

#### 用户操作流程

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  用户    │     │  前端    │     │  后端    │     │   AI     │     │  数据库  │
└────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │                │                │
     │ 1. 请求分析    │                │                │                │
     │───────────────>│                │                │                │
     │                │                │                │                │
     │                │ 2. POST        │                │                │
     │                │ /reports/      │                │                │
     │                │ generate/      │                │                │
     │                │ weak-points    │                │                │
     │                │───────────────>│                │                │
     │                │                │                │                │
     │                │                │ 3. 获取错题    │                │
     │                │                │───────────────>│                │
     │                │                │                │                │
     │                │                │ 4. 统计分析    │                │
     │                │                │ - 按类别       │                │
     │                │                │ - 错误模式     │                │
     │                │                │                │                │
     │                │                │ 5. AI 分析     │                │
     │                │                │───────────────>│                │
     │                │                │                │                │
     │                │                │                │ 6. 调用 GPT-4  │
     │                │                │                │───────────────>│
     │                │                │                │                │
     │                │                │ 7. 返回分析结果│                │
     │                │                │<───────────────│                │
     │                │                │                │                │
     │                │                │ 8. 存储报告    │                │
     │                │                │───────────────>│                │
     │                │                │                │                │
     │                │ 9. 返回报告    │                │                │
     │                │<───────────────│                │                │
     │ 10. 显示报告   │                │                │                │
     │<───────────────│                │                │                │
     │                │                │                │                │
```

#### 后端处理流程

**步骤 1: 获取错题数据**

```python
# ai_analysis/analyzers/weak_point.py
async def get_wrong_questions(
    self,
    limit: int = 50,
    category: Optional[str] = None
) -> List[Dict[str, Any]]:
    # 查询用户错题
    query = (
        select(UserQuestionLog, QBQuestion)
        .join(QBQuestion, UserQuestionLog.question_no == QBQuestion.No)
        .where(
            and_(
                UserQuestionLog.user_id == self.user_id,
                UserQuestionLog.is_correct == False
            )
        )
        .order_by(UserQuestionLog.attempt_time.desc())
        .limit(limit)
    )
    
    result = await self.db.execute(query)
    rows = result.all()
    
    # 格式化数据
    questions = []
    for log, question in rows:
        questions.append({
            "question_no": question.No,
            "category": question.category,
            "stem": question.stem,
            "user_answer": log.user_answer,
            "correct_ans_summary": question.correct_ans_summary,
            "attempt_time": log.attempt_time.isoformat(),
        })
    
    return questions
```

**步骤 2: 统计分析**

```python
async def analyze_by_category(self) -> Dict[str, Any]:
    # 按类别统计错误数量
    query = (
        select(
            QBQuestion.category,
            func.count().label('error_count'),
        )
        .join(UserQuestionLog, UserQuestionLog.question_no == QBQuestion.No)
        .where(
            and_(
                UserQuestionLog.user_id == self.user_id,
                UserQuestionLog.is_correct == False,
                UserQuestionLog.is_mastered == False
            )
        )
        .group_by(QBQuestion.category)
    )
    
    result = await self.db.execute(query)
    rows = result.all()
    
    # 计算百分比
    categories = {}
    total_errors = sum(row.error_count for row in rows)
    
    for row in rows:
        categories[row.category] = {
            "error_count": row.error_count,
            "percentage": round(row.error_count / total_errors * 100, 2)
        }
    
    return {
        "total_errors": total_errors,
        "categories": categories,
        "top_weak_category": max(categories.items(), key=lambda x: x[1]["error_count"])[0]
    }
```

**步骤 3: AI 分析**

```python
async def generate_ai_analysis(self) -> Dict[str, Any]:
    # 1. 准备 Prompt
    system_prompt = """You are an expert educational analyst.
    Analyze the student's wrong answers and identify:
    1. Knowledge gaps
    2. Common error patterns
    3. Difficulty areas
    4. Learning recommendations
    
    Respond in JSON format:
    {
        "weak_points": [
            {"knowledge": "name", "error_count": N, "confidence": 0.0-1.0}
        ],
        "error_patterns": ["pattern1", "pattern2"],
        "recommendations": ["recommendation1", "recommendation2"],
        "summary": "brief summary"
    }"""
    
    # 2. 格式化错题数据
    questions_text = "\n".join([
        f"- Q{q['question_no']}: {q['category']} - {q['stem'][:100]}... "
        f"(Your answer: {q['user_answer']}, Correct: {q['correct_ans_summary']})"
        for q in self.questions[:20]
    ])
    
    # 3. 调用 LLM API
    response = await self.llm.chat([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Analyze these:\n{questions_text}"}
    ])
    
    # 4. 解析 JSON 响应
    analysis = json.loads(response)
    
    return analysis
```

**步骤 4: 存储报告**

```python
# reports/services/report_service.py
async def create_report(
    self,
    report_type: str,
    data: Dict[str, Any],
    summary: Optional[str]
) -> AnalysisReport:
    report = AnalysisReport(
        user_id=self.user_id,
        report_type=report_type,
        data=json.dumps(data),
        summary=summary
    )
    
    self.db.add(report)
    await db.flush()
    await db.refresh(report)
    
    return report
```

---

### 3. 学习推荐生成

#### 用户操作流程

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  用户    │     │  前端    │     │  后端    │     │  数据库  │
└────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │                │
     │ 1. 请求推荐    │                │                │
     │───────────────>│                │                │
     │                │                │                │
     │                │ 2. POST        │                │
     │                │ /reports/      │                │
     │                │ generate/      │                │
     │                │ recommendations│                │
     │                │───────────────>│                │
     │                │                │                │
     │                │                │ 3. 评估用户水平│
     │                │                │ - 正确率       │
     │                │                │ - 题目数量     │
     │                │                │───────────────>│
     │                │                │                │
     │                │                │ 4. 获取薄弱点  │
     │                │                │───────────────>│
     │                │                │                │
     │                │                │ 5. 生成推荐    │
     │                │                │ - 练习题       │
     │                │                │ - 复习建议     │
     │                │                │                │
     │                │                │ 6. AI 个性化   │
     │                │                │───────────────>│
     │                │                │                │
     │                │                │ 7. 存储推荐    │
     │                │                │───────────────>│
     │                │                │                │
     │                │ 8. 返回推荐    │                │
     │                │<───────────────│                │
     │ 9. 显示推荐    │                │                │
     │<───────────────│                │                │
     │                │                │                │
```

#### 后端处理流程

**步骤 1: 评估用户水平**

```python
# ai_analysis/analyzers/recommendation.py
async def get_user_level(self) -> str:
    # 查询用户答题统计
    query = (
        select(
            func.count().label('total'),
            func.sum(UserQuestionLog.is_correct.cast(int)).label('correct'),
        )
        .where(UserQuestionLog.user_id == self.user_id)
    )
    
    result = await self.db.execute(query)
    row = result.first()
    
    if not row or row.total == 0:
        return "beginner"
    
    accuracy = row.correct / row.total
    
    if accuracy >= 0.8:
        return "advanced"
    elif accuracy >= 0.6:
        return "intermediate"
    else:
        return "beginner"
```

**步骤 2: 获取薄弱知识点**

```python
async def get_priority_knowledge_points(
    self,
    limit: int = 5
) -> List[Dict[str, Any]]:
    # 按错误数量排序知识点
    query = (
        select(
            QBQuestion.category,
            func.count().label('error_count'),
        )
        .join(UserQuestionLog, UserQuestionLog.question_no == QBQuestion.No)
        .where(
            and_(
                UserQuestionLog.user_id == self.user_id,
                UserQuestionLog.is_correct == False,
                UserQuestionLog.is_mastered == False
            )
        )
        .group_by(QBQuestion.category)
        .order_by(func.count().desc())
        .limit(limit)
    )
    
    result = await self.db.execute(query)
    rows = result.all()
    
    return [
        {
            "knowledge": row.category,
            "error_count": row.error_count,
            "priority": i + 1
        }
        for i, row in enumerate(rows)
    ]
```

**步骤 3: 生成练习推荐**

```python
async def generate_practice_recommendations(
    self,
    weak_points: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    recommendations = []
    
    for point in weak_points[:3]:  # Top 3 薄弱点
        # 查找相关题目
        query = (
            select(QBQuestion)
            .where(
                and_(
                    QBQuestion.category == point["knowledge"],
                    QBQuestion.is_public == True
                )
            )
            .limit(5)
        )
        
        result = await self.db.execute(query)
        questions = result.scalars().all()
        
        if questions:
            recommendations.append({
                "type": "practice",
                "priority": point.get("priority", 5),
                "knowledge": point["knowledge"],
                "action": f"Practice 5 questions on {point['knowledge']}",
                "question_ids": [q.No for q in questions],
                "estimated_time": "20 minutes"
            })
    
    return recommendations
```

**步骤 4: AI 个性化推荐**

```python
async def generate_ai_recommendations(
    self,
    weak_points: List[Dict[str, Any]],
    user_level: str
) -> List[Dict[str, Any]]:
    # 调用 LLM 生成个性化推荐
    recommendations = await self.llm.generate_recommendations(
        weak_points=weak_points,
        user_level=user_level
    )
    
    return recommendations
```

---

## 数据流转详解

### 完整数据流图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           用户操作流程                                   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  1. 上传书籍 → 2. 提取知识 → 3. 答题练习 → 4. 记录错题 → 5. 生成分析    │
│       │              │              │              │              │     │
│       ▼              ▼              ▼              ▼              ▼     │
│  ┌────────┐    ┌──────────┐   ┌──────────┐  ┌──────────┐  ┌──────────┐│
│  │user_   │    │knowledge │   │qb_       │  │user_     │  │analysis_ ││
│  │books   │───▶│_points   │──▶│questions │─▶│question_ │─▶│reports   ││
│  └────────┘    └──────────┘   └──────────┘  │logs      │  └──────────┘│
│                                              └──────────┘              │
│                                                    │                    │
│                                                    ▼                    │
│                                             ┌──────────┐               │
│                                             │WeakPoint │               │
│                                             │Analyzer  │               │
│                                             └──────────┘               │
│                                                    │                    │
│                                                    ▼                    │
│                                             ┌──────────┐               │
│                                             │Recommend │               │
│                                             │Engine    │               │
│                                             └──────────┘               │
└─────────────────────────────────────────────────────────────────────────┘
```

### 数据库表关系

```
┌─────────────────┐
│     User        │
│  - user_id (PK) │
│  - email        │
│  - role         │
└────────┬────────┘
         │
         │ 1:N
         │
    ┌────┴────────────────────────────────────────┐
    │                                            │
    ▼                                            ▼
┌─────────────────┐                     ┌─────────────────┐
│   UserBook      │                     │ UserQuestionLog │
│  - id (PK)      │                     │  - id (PK)      │
│  - user_id (FK) │                     │  - user_id (FK) │
│  - title        │                     │  - question_no  │
│  - file_path    │                     │  - is_correct   │
│  - knowledge_   │                     │  - is_mastered  │
│    tree (JSON)  │                     └────────┬────────┘
└─────────────────┘                              │
                                                 │ N:1
                                                 │
                                                 ▼
                                          ┌─────────────────┐
                                          │   QBQuestion    │
                                          │  - No (PK)      │
                                          │  - category     │
                                          │  - stem         │
                                          │  - correct_ans_ │
                                          │    summary      │
                                          └────────┬────────┘
                                                   │
                                                   │ N:M (through QuestionKnowledge)
                                                   │
                                          ┌────────┴────────┐
                                          │                 │
                                          ▼                 ▼
                                   ┌─────────────────┐ ┌─────────────────┐
                                   │QuestionKnowledge│ │  AnalysisReport │
                                   │  - id (PK)      │ │  - id (PK)      │
                                   │  - question_no  │ │  - user_id (FK) │
                                   │  - knowledge_id │ │  - report_type  │
                                   │  - weight       │ │  - data (JSON)  │
                                   └────────┬────────┘ └─────────────────┘
                                            │
                                            │ N:1
                                            │
                                            ▼
                                   ┌─────────────────┐
                                   │ KnowledgePoint  │
                                   │  - id (PK)      │
                                   │  - name         │
                                   │  - subject      │
                                   │  - parent_id    │
                                   └─────────────────┘
```

---

## API 调用时序

### 完整学习周期时序图

```
用户          前端          后端 API         后端 Service      AI/LLM       数据库
 │             │               │               │               │             │
 │──上传书籍──>│               │               │               │             │
 │             │──POST /books─>│               │               │             │
 │             │               │──保存文件───>│               │             │
 │             │               │               │               │             │
 │             │<──book_id─────│               │               │             │
 │             │               │               │               │             │
 │──触发解析──>│               │               │               │             │
 │             │──POST parse──>│               │               │             │
 │             │               │──读取文件───>│               │             │
 │             │               │               │               │             │
 │             │               │──提取知识───>│──调用 LLM────>│             │
 │             │               │               │               │             │
 │             │               │<──知识树─────│               │             │
 │             │               │               │               │             │
 │             │               │──存储───────>│               │             │
 │             │<──完成───────│               │               │             │
 │             │               │               │               │             │
 │──答题练习──>│               │               │               │             │
 │             │──POST answer>│               │               │             │
 │             │               │──记录错题───>│               │             │
 │             │<──结果───────│               │               │             │
 │             │               │               │               │             │
 │──生成分析──>│               │               │               │             │
 │             │──POST report>│               │               │             │
 │             │               │──获取错题───>│               │             │
 │             │               │               │               │             │
 │             │               │──统计分析───>│               │             │
 │             │               │               │               │             │
 │             │               │──AI 分析────>│──调用 LLM────>│             │
 │             │               │               │               │             │
 │             │               │<──分析结果───│               │             │
 │             │               │               │               │             │
 │             │               │──存储报告───>│               │             │
 │             │<──报告───────│               │               │             │
 │             │               │               │               │             │
 │──获取推荐──>│               │               │               │             │
 │             │──POST recom─>│               │               │             │
 │             │               │──评估水平───>│               │             │
 │             │               │──生成推荐───>│               │             │
 │             │               │               │               │             │
 │             │               │──AI 个性化──>│──调用 LLM────>│             │
 │             │               │               │               │             │
 │             │               │<──推荐列表───│               │             │
 │             │               │               │               │             │
 │             │               │──存储───────>│               │             │
 │             │<──推荐───────│               │               │             │
 │<──显示──────│               │               │               │             │
 │             │               │               │               │             │
```

---

## 数据库操作

### 核心 SQL 操作示例

#### 1. 插入书籍记录

```sql
INSERT INTO user_books (
    user_id, title, file_path, file_type, file_size, status
) VALUES (
    1, 
    'High School Mathematics', 
    'uploads/books/1/abc123.pdf', 
    'pdf', 
    1024000, 
    0  -- PENDING
);
```

#### 2. 更新书籍状态

```sql
UPDATE user_books 
SET 
    status = 2,  -- COMPLETED
    knowledge_tree = '{"subject": "Math", "topics": [...]}',
    processed_at = CURRENT_TIMESTAMP
WHERE id = 1;
```

#### 3. 插入知识点

```sql
INSERT INTO knowledge_points (
    name, subject, parent_id, difficulty, description
) VALUES (
    'Quadratic Equations',
    'Mathematics',
    1,  -- parent_id
    3,  -- difficulty
    'Equations of the form ax² + bx + c = 0'
);
```

#### 4. 关联题目与知识点

```sql
INSERT INTO question_knowledge (
    question_no, knowledge_id, weight
) VALUES (
    123,  -- question_no
    45,   -- knowledge_id
    0.8   -- weight
);
```

#### 5. 插入分析报告

```sql
INSERT INTO analysis_reports (
    user_id, report_type, data, summary
) VALUES (
    1,
    'weak_point',
    '{"weak_points": [...], "error_patterns": [...]}',
    'Student struggles with quadratic equations'
);
```

#### 6. 查询用户薄弱点

```sql
SELECT 
    qb.category,
    COUNT(*) as error_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM user_question_logs uql
JOIN qb_questions qb ON uql.question_no = qb.No
WHERE 
    uql.user_id = 1 
    AND uql.is_correct = FALSE
    AND uql.is_mastered = FALSE
GROUP BY qb.category
ORDER BY error_count DESC;
```

---

## 总结

### 用户操作引起的后端处理

| 用户操作 | 触发的 API | 后端处理 | 数据库操作 |
|----------|-----------|----------|-----------|
| 上传书籍 | `POST /api/books/upload` | 保存文件、验证格式 | INSERT user_books |
| 解析书籍 | `POST /api/books/{id}/parse` | 读取文件、AI 提取知识 | UPDATE user_books |
| 答题练习 | `POST /practice/submit-answer` | 判断正误、记录日志 | INSERT user_question_logs |
| 生成分析 | `POST /api/reports/generate/weak-points` | 统计分析、AI 分析 | INSERT analysis_reports |
| 获取推荐 | `POST /api/reports/generate/recommendations` | 评估水平、生成推荐 | INSERT analysis_reports |

### 关键技术点

1. **文件处理**: 异步读取、格式验证、安全存储
2. **AI 集成**: Prompt 工程、JSON 解析、错误处理
3. **数据分析**: SQL 聚合、统计计算、趋势分析
4. **异步处理**: FastAPI BackgroundTasks、Celery（可选）
5. **缓存优化**: Redis 缓存、报告 TTL

### 性能优化建议

1. **批量处理**: 错题分析时批量获取数据
2. **缓存策略**: 分析报告缓存 1 小时
3. **异步任务**: 书籍解析使用后台任务
4. **分页查询**: 列表接口支持分页
5. **索引优化**: 关键查询字段添加索引

---

**文档版本**: 1.0  
**最后更新**: 2024-01-01  
**维护者**: Development Team

# 研助手

## 核心功能规划
### 1. 必须实现的基础功能 (MVP)
这些是应用的骨架，没有它们无法称为错题本：
* 用户体系：注册/登录，支持多端同步（手机/平板/Web）。
错题录入：
  * 手动输入（题目文本、选项、答案）。
  * 拍照上传（核心）：利用OCR识别题目图片，自动转为文本（2026年标准配置）。
  * 标记来源（试卷名称、日期、科目）。
* 错题分类：按学科、知识点（如“三角函数”、“定语从句”）、题型（选择/填空/解答）归档。
* 错因分析：用户手动选择或输入错误原因（如“计算失误”、“概念不清”、“审题错误”）。
* 复习模式：
  * 列表浏览。
  * 遮挡答案模式：先看题，点击后显示解析。
  * 状态标记：标记为“已掌握”、“需重做”、“移除”。
* 搜索与筛选：按时间、科目、知识点、掌握程度筛选错题。

### 2. 强烈推荐实现的高级功能 (差异化竞争点)

结合2025-2026年的趋势，这些功能能显著提升用户体验：
* 智能去重与归并：如果同一道题在不同试卷出现，系统应自动识别并合并，避免重复刷题。
* 艾宾浩斯遗忘曲线复习计划：系统根据用户录入时间和复习记录，自动计算下次复习时间（如1天后、3天后、7天后），并在首页推送“今日待复习”。
* AI 辅助解析与举一反三：
  * 接入大模型API，为没有解析的错题自动生成解题步骤。
  * 变式题推荐：基于当前错题的知识点，推荐3道类似的练习题进行巩固。
* 学情分析报告：生成周报/月报，展示“高频错误知识点”、“薄弱项雷达图”，帮助用户直观看到进步。
* 导出与打印：支持将错题导出为PDF或Word，格式化为“原题+留白+解析”的试卷模式，方便线下重做。

## MYSQL数据库设计方案

``` mermaid
erDiagram
    %% 用户与错题：1 对 多
    users ||--o{ wrong_questions : "creates/owns"
    users ||--o{ review_records : "performs"

    %% 科目与知识点：1 对 多 (树状结构自引用在知识点内部)
    subjects ||--o{ knowledge_points : "contains"
    
    %% 知识点与错题：多 对 多 (通过中间表)
    knowledge_points ||--o{ question_knowledge_map : "linked via"
    wrong_questions ||--o{ question_knowledge_map : "linked via"

    %% 错题与复习记录：1 对 多
    wrong_questions ||--o{ review_records : "has history of"

    %% 错题与 AI 解析：1 对 1
    wrong_questions ||--|| ai_analyses : "has unique"

    %% 实体定义与关键属性示意
    users {
        BIGINT user_id PK
        VARCHAR username
        VARCHAR password_hash
    }

    subjects {
        INT subject_id PK
        VARCHAR subject_name
    }

    knowledge_points {
        BIGINT kp_id PK
        INT subject_id FK
        BIGINT parent_id FK "Self-ref for Tree"
        VARCHAR kp_name
    }

    wrong_questions {
        BIGINT question_id PK
        BIGINT user_id FK
        INT subject_id FK
        TEXT question_text
        JSON question_images
        ENUM status
        DATE next_review_date
    }

    question_knowledge_map {
        BIGINT id PK
        BIGINT question_id FK
        BIGINT kp_id FK
        FLOAT confidence_score
    }

    review_records {
        BIGINT record_id PK
        BIGINT question_id FK
        BIGINT user_id FK
        ENUM result
        TIMESTAMP review_date
    }

    ai_analyses {
        BIGINT analysis_id PK
        BIGINT question_id FK "Unique"
        TEXT ai_solution
        TEXT ai_reasoning
    }
```

### 1. ER图核心实体关系
* User (用户) 1 : N WrongQuestion (错题)
* Subject (科目) 1 : N KnowledgePoint (知识点)
* WrongQuestion N : 1 KnowledgePoint (一道题可能涉及多个知识点，需中间表)
* WrongQuestion 1 : N ReviewRecord (复习记录)
* WrongQuestion 1 : 1 AIAnalysis (AI解析/扩展)

### 2. 数据表结构定义 (SQL DDL 示例)
``` sql
-- 1. 用户表
CREATE TABLE users (
    user_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. 科目表 (预置：数学、英语、物理等)
CREATE TABLE subjects (
    subject_id INT PRIMARY KEY AUTO_INCREMENT,
    subject_name VARCHAR(50) NOT NULL, -- 如 'Math', 'English'
    icon_url VARCHAR(255),
    sort_order INT DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. 知识点表 (支持树状结构，通过 parent_id 实现)
CREATE TABLE knowledge_points (
    kp_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    subject_id INT NOT NULL,
    parent_id BIGINT DEFAULT NULL, -- 父知识点ID，用于构建知识树
    kp_name VARCHAR(100) NOT NULL, -- 如 '二次函数', '牛顿定律'
    full_path VARCHAR(255), -- 冗余字段，方便搜索，如 '数学>代数>二次函数'
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id),
    FOREIGN KEY (parent_id) REFERENCES knowledge_points(kp_id),
    INDEX idx_subject (subject_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. 错题主表
CREATE TABLE wrong_questions (
    question_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    
    -- 题目内容
    question_text TEXT NOT NULL, -- OCR识别后的文本或手动输入
    question_images JSON, -- 存储图片URL数组 ["url1", "url2"]
    options_json JSON, -- 选择题选项 {"A":"...", "B":"..."}
    correct_answer TEXT, -- 正确答案
    user_answer TEXT, -- 用户当时的错误答案
    
    -- 分类与标签
    subject_id INT NOT NULL,
    question_type ENUM('choice', 'fill', 'solution', 'other') DEFAULT 'choice',
    source_info VARCHAR(255), -- 来源：'2025期中考试卷'
    
    -- 错因分析 (用户填写)
    error_reason_type ENUM('careless', 'concept_gap', 'logic_error', 'time_limit', 'other'),
    error_reason_detail TEXT, -- 具体描述
    
    -- 状态与统计
    status ENUM('new', 'reviewing', 'mastered', 'removed') DEFAULT 'new',
    difficulty_level TINYINT DEFAULT 1, -- 1-5 用户自评难度
    mistake_count INT DEFAULT 1, -- 该题做错次数
    last_reviewed_at TIMESTAMP NULL,
    next_review_date DATE, -- 艾宾浩斯算法计算的下次复习日期
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id),
    INDEX idx_user_status (user_id, status),
    INDEX idx_next_review (user_id, next_review_date) -- 关键索引：用于查询今日待复习
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. 错题 - 知识点 关联表 (多对多)
CREATE TABLE question_knowledge_map (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    question_id BIGINT NOT NULL,
    kp_id BIGINT NOT NULL,
    confidence_score FLOAT DEFAULT 1.0, -- AI判断该知识点的关联度
    UNIQUE KEY uk_q_kp (question_id, kp_id),
    FOREIGN KEY (question_id) REFERENCES wrong_questions(question_id) ON DELETE CASCADE,
    FOREIGN KEY (kp_id) REFERENCES knowledge_points(kp_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. 复习记录表 (用于追踪历史和分析遗忘曲线)
CREATE TABLE review_records (
    record_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    question_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    review_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    result ENUM('correct', 'wrong', 'hint_used'), -- 复习时的表现
    time_spent_seconds INT, -- 耗时
    notes TEXT, -- 本次复习备注
    FOREIGN KEY (question_id) REFERENCES wrong_questions(question_id) ON DELETE CASCADE,
    INDEX idx_user_date (user_id, review_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7. AI 解析与推荐表 (可选，也可存在宽表中，但分开更灵活)
CREATE TABLE ai_analyses (
    analysis_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    question_id BIGINT NOT NULL UNIQUE,
    ai_solution TEXT, -- AI生成的详细解析
    ai_reasoning TEXT, -- 错因深度分析
    similar_questions_json JSON, -- 推荐的变式题ID列表 [{"id":123, "source":"..."}]
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (question_id) REFERENCES wrong_questions(question_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```
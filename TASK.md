# Codex 任务书：ClassWeaver Micro-Agents（Django+DRF 后端 / Vue3 前端 / SiliconFlow 统一平台）

## 0. 项目概述

做一套**不下载本地模型、全走 OpenAI 兼容 API（硅基流动 SiliconFlow）的教育场景微型多智能体系统**：**ClassWeaver Micro-Agents**。
 目标：覆盖**课前（预习包）→测验→个性化复习**闭环，满足“通义千问 + DeepSeek 必须使用”的赛题硬要求，并且**前后端分离**、**可打印**、**可解释（model_trace）**、**可选 RAG（向量库）**。

------

## 1. 技术栈与平台

- **后端**：Django 5 + Django REST framework
- **前端**：Vue3 + Vite + Tailwind（纯静态构建产物）
- **LLM 接入**：**硅基流动（SiliconFlow）单一 base_url**，OpenAI 兼容 SDK（`openai>=1.43`）
- **可选智能体编排**：AgentScope（可选安装，失败自动回退到自研 Pipeline）
- **RAG 向量库**：默认 `faiss-cpu` 零安装；**可选** pgvector（PostgreSQL）

------

## 2. 目录结构（前后端分离）

```
classweaver-microagents/
  manage.py
  requirements.txt
  .env.example
  README.md
  LICENSE
  src/
    config/                # Django 配置
      __init__.py  settings.py  urls.py  wsgi.py
    core/
      apps.py  models.py  admin.py  migrations/
    api/
      urls.py  serializers.py  views.py
    agents/
      prompts.py           # 三Agent提示词模板
      planner.py           # 调 Qwen
      rewriter.py          # 调 DeepSeek
      tutor.py             # 调 Qwen(默认)
      runtime.py           # AgentScope封装与回退 Pipeline
      utils.py             # openai客户端封装、鲁棒JSON、重试、计时、日志
    services/
      pipeline.py          # 串：Planner→Rewriter→(可选)Tutor
      ppt.py               # 提取PPT文本
      scoring.py           # 评分与诊断（题↔知识点映射）
      printable.py         # 可打印HTML渲染
    kb/                    # 向量库与RAG
      __init__.py
      ingest.py            # 解析/切分/去重/入库/建索引
      store.py             # FAISS / pgvector 抽象
      retrieve.py          # 语义检索
    templates/             # 可保留用于本地调试（非必须）
      index.html  take.html  print.html
    static/
      print.css
  webapp/                  # 前端工程（完全独立构建）
    index.html
    package.json
    vite.config.ts
    .env.example
    src/
      main.ts  router.ts
      services/api.ts      # fetch封装（/api/*，含超时/错误）
      types/index.ts
      views/
        HomeView.vue       # 教师端：文本/PPT→预习包+trace
        TakeView.vue       # 学生端：答题与提交
        PrintView.vue      # 打印视图（A4）
      components/
        JsonPreview.vue  QuizCard.vue  TracePanel.vue
      assets/print.css
  tests/
    test_utils.py  test_pipeline.py  test_api.py
  corpus/                  # 知识库原始文件（上传后放这里）
  data/                    # FAISS 索引与元数据
```

------

## 3. 环境变量（后端 `.env.example`）

```
# 统一使用 硅基流动（SiliconFlow）OpenAI兼容端点
BASE_URL=https://api.siliconflow.cn/v1
API_KEY=sk-xxxx

# 模型（按账号可用替换；推荐省钱稳妥组合）
QWEN_MODEL=Qwen/Qwen2.5-14B-Instruct      # Planner / Tutor（通义千问）
DEEPSEEK_MODEL=deepseek-ai/DeepSeek-V3    # Rewriter（DeepSeek）

# Embedding（RAG）
EMBEDDING_MODEL=BAAI/bge-m3               # 或 BAAI/bge-large-zh-v1.5
# EMBEDDING_DIM 可不写，由代码根据embedding返回长度自动推断；若写，需与模型维度一致

REQUEST_TIMEOUT_SECONDS=60
OPENAI_MAX_RETRIES=2

# 向量库（默认faiss零安装；想用pgvector则切换）
VECTOR_BACKEND=faiss
VSTORE_PATH=data/faiss.index
VSTORE_META=data/chunks.jsonl
# 若启用 pgvector：
# VECTOR_BACKEND=pgvector
# DATABASE_URL=postgres://user:pass@host:5432/dbname

# 智能体框架开关（可选）
AGENTSCOPE_ENABLED=false

# RAG 开关与检索参数
RAG_ENABLED=true
RAG_TOPK=5
RAG_MIN_SCORE=0.2
```

------

## 4. 多智能体定义（必须落地“双模型协同”）

- **Planner Agent（Qwen）**：将 PPT/课程大纲转为**严格 JSON**：
   `knowledge_points(3–5, ≤50字摘要)，glossary(5–10术语+定义)，quiz(10题：id,question,options[A-D],answer,explain,difficulty{easy|medium|hard})`
  - 若 `RAG_ENABLED=true`：在生成前，依据正文语义检索 top-k 片段，拼接到提示词 `CONTEXT:`，并在每个知识点/题目中附 `refs:[{doc_id, chunk_id}]`。
- **Rewriter Agent（DeepSeek）**：对 `quiz` **三版改写**与**干扰项优化**，**答案不变**：
   每题新增 `variants:[A版,B版,C版]`。
- **Tutor Agent（Qwen，DeepSeek备选）**：基于学生作答生成**“3分钟复习卡”**（再学提要、关键概念/公式、2道针对性练习）与**追加3–5道弱项题**。
  - 如启用 RAG，可检索错题相关片段，给 `citations`。

> **调用路由**：Planner/Tutor → `model=QWEN_MODEL`；Rewriter → `model=DEEPSEEK_MODEL`。任一模型不可用→自动回退，`model_trace.fallback=true`。

------

## 5. 后端 API 规范（DRF）

- `POST /api/prestudy/from-text/`
   req: `{ "text": "课程大纲..." }`
   resp: `{ id, status, planner_json, final_json, model_trace, duration_ms }`
- `POST /api/prestudy/from-ppt/`（form-data: `file=.pptx`）
   resp 同上（内部调用 `services/ppt.py` 提取文本）
- `POST /api/quiz/start/`
   req: `{ "job_id": <id> }`
   resp: `{ "session_id": "...", "questions":[{id,question,options,difficulty}...] }`（不含答案）
- `POST /api/quiz/submit/`
   req: `{ "session_id":"...", "answers":[{"id":1,"answer":"B"}, ...] }`
   resp: `{ score, detail:[{id,correct,explain}], diagnostics:{kp_stats...}, review_card, extra_questions? }`
- **RAG（向量库）**
  - `POST /api/kb/upload/`（form-data: 多文件，支持 .pptx/.pdf/.docx/.txt）：解析→切分→embedding→入索引；返回 `{docs_created, chunks, backend, dim}`
  - `POST /api/kb/search/`：`{ "query":"...", "top_k":5 }` → 返回 top-k 片段与来源

------

## 6. 关键实现要求

1. **OpenAI 兼容客户端（SiliconFlow）**
   - 后端只初始化**一个** `OpenAI(api_key=API_KEY, base_url=BASE_URL)` 客户端；通过 `model` 切换 Qwen/DeepSeek。
   - `agents/utils.py` 封装：`chat(model, system, user, temperature)`、`embed(model, texts[])`，统一重试/超时/统计。
2. **鲁棒 JSON**
   - 支持 ```json 代码块、去 Markdown 包裹、去注释、尾逗号修复，失败重试一次；最终用 `pydantic` 做 schema 校验。
3. **RAG（向量库）**
   - `kb/ingest.py`：解析（pptx/pdf/docx/txt）→ 清洗 → 固定滑窗切分（默认 800/120）→ 去重 → 调 `EMBEDDING_MODEL` → 入索引。
   - `kb/store.py`：抽象 `faiss`（默认 `IndexFlatIP` + 归一化）与 `pgvector` 两种实现；`VECTOR_BACKEND` 决定。
   - `kb/retrieve.py`：语义检索接口；Planner/Tutor 可调用拼接 `CONTEXT:`。
   - 失败不阻断：检索异常或空结果，继续生成但在 `model_trace.rag.enabled=false`。
4. **评分与诊断**
   - `services/scoring.py`：计算分数；题目可带 `kp_ids`，缺省则用 LLM 粗映射一次；生成 `diagnostics`。
5. **可打印**
   - `services/printable.py` + `webapp/src/assets/print.css`：A4 版式，“预习卡 + 试卷 + 复习卡”，进入 `PrintView` 可打印。
6. **model_trace（可解释）**
   - 记录：`orchestrator{agentscope|pipeline}, step{planner|rewriter|tutor}, provider{qwen|deepseek}, model, base_url, latency_ms, input_chars, output_chars, rag{enabled,backend,k,dim}, fallback`。
7. **AgentScope（可选）**
   - `AGENTSCOPE_ENABLED=true` 且安装成功时，`agents/runtime.py` 用 AgentScope 定义三Agent并路由；否则走自研 Pipeline，**接口与返回一致**。
8. **安全与限制**
   - 限制上传类型/大小（只允许 `.pptx/.pdf/.docx/.txt`）；后端不打印完整 Key；文本输入长度与 `max_tokens` 做限制。
9. **前端（webapp）**
   - `.env.example`：`VITE_API_BASE=http://127.0.0.1:8000`
   - 通过 `services/api.ts` 对接上述后端 API，统一超时/错误；
   - `HomeView`：文本/PPT 触发生成，展示 JSON 与 `model_trace`，提供“打印”入口与“资料库上传/检索”卡片；
   - `TakeView`：答题卡、进度、提交；
   - `PrintView`：A4 打印；
   - 构建：`npm run build` → `webapp/dist/` 作为静态资源（同域 `/app/` 或单独域+CORS）。
10. **数据库**
    - 默认 SQLite（零安装）；**如需企业级**，支持切换 PostgreSQL（含 pgvector）。

------

## 7. 数据模型（Django，简要）

- **PrestudyJob**：`id, source_type, source_excerpt, planner_json, final_json, status, duration_ms, model_trace(JSON), created_at`
- **QuizSession**：`id, job(FK), questions_snapshot(JSON), started_at, ended_at`
- **QuizAnswer**：`id, session(FK), question_id, answer, correct, used_variant, kp_ids(JSON)`
- **LlmCallLog**：`step, provider, model, base_url, latency_ms, input_chars, output_chars, fallback(bool), created_at`
- **Document / Chunk（kb）**：文档元信息与切分片段；faiss 模式向量存外部文件，pgvector 模式存表中向量列。

------

## 8. 测试与验收（DoD）

- 提供 `requirements.txt`、后端 `.env.example`、前端 `.env.example`、README（跑通步骤、示例 curl/截图）。
- 文本或 PPT 可成功生成完整**预习包 JSON**；
- 学生作答→得到分数、诊断与**“3分钟复习卡”**，可追加弱项题；
- **RAG**：能上传至少 1 份资料并检索；Planner 输出含 `refs`，Tutor 输出含 `citations`；
- 打印页 A4 版式正常；
- `model_trace` 清晰展示：`planner(qwen) → rewriter(deepseek) → tutor(qwen)`，含 `base_url/model/latency_ms/provider/fallback` 与 `rag` 字段；
- 未装 AgentScope 也能跑；装后改 `.env` 一键启用，接口不变；
- 基础单测覆盖：鲁棒 JSON 解析、评分逻辑、主要 API（可 mock LLM 与检索）。

------

## 9. 提示词模板（放 `agents/prompts.py`）

- **Planner/Qwen.system**：资深教研员；严格输出 JSON：`knowledge_points/glossary/quiz`；题目难度分层、互斥选项、附解析；如 `CONTEXT:` 存在，优先参考并为条目附 `refs`。
- **Planner.user**：`{TEXT}`（或提取后的 PPT 文本）+（可选）`CONTEXT:\n{TOPK_CHUNKS}`。
- **Rewriter/DeepSeek.system**：测评工程师；对 `quiz` 每题新增 `variants:[A版,B版,C版]`，优化干扰项，但**正确答案不变**；严格 JSON。
- **Rewriter.user**：`{PLANNER_JSON}`（字符串化）。
- **Tutor/Qwen.system**：学习教练；基于错题生成“3分钟复习卡”（再学提要、关键概念/公式、2道针对性练习）与**追加3–5道弱项题**；可接收 `CONTEXT:` 生成 `citations`。
- **Tutor.user**：`{FINAL_QUIZ_JSON}` + `{ANSWERS}` +（可选）`CONTEXT:\n{TOPK_CHUNKS}`。

------

## 10. 运行步骤（写入 README）

- 后端：`pip install -r requirements.txt && python manage.py migrate && python manage.py runserver`
- 前端：`cd webapp && npm i && npm run build` → 将 `dist/` 用 Django **同域托管**（推荐）或独立域+CORS。
- `.env` 填写 SiliconFlow `BASE_URL/API_KEY` 与模型名即可。

------

> 要求：务实清晰，**开箱即跑**；如任一外部依赖或 AgentScope 安装失败，仍能稳定运行（自动回退）。对外不泄露 API Key。


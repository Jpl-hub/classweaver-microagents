# ClassWeaver Micro-Agents

ClassWeaver 是一个基于 Planner / Rewriter / Tutor / Timeline 的学习助手系统，支持课程生成、知识库问答、练习测验、推荐与打印等功能。V3 分支默认使用 MySQL，并补充了登录 / 注册能力。

## 关键特性
- **多智能体流程**：Planner 规划内容，Rewriter 优化表述，Tutor 负责练习与总结。
- **知识库 + RAG**：按“知识库/文件夹”分组上传 PDF/DOCX/PPTX/TXT，检索严格限定在当前用户的当前知识库。
- **学习记录与时间线**：课程、测验、事件写入时间线，可拖拽调整顺序；打印讲义一键生成。
- **账户隔离**：所有业务接口需登录，会话基于 Cookie + CSRF；前端缓存登录态，接口 401 会清空缓存并要求重新登录。
- **前后端联动**：Django REST API + Vue3 前端（含登录/注册/知识库/时间线/打印视图）。

## 目录结构
- `src/agents/`：Planner/Rewrite/Tutor 示例逻辑。
- `src/api/`：Django REST API（知识库、课程、推荐等）。
- `src/services/`：打印、PPT、推荐、评分等服务。
- `webapp/src/views/`：Vue3 前端页面（Home/Knowledge/Coach/Take/Print/History/Login/Register）。
- `webapp/src/services/api.ts`：前端 API 客户端（含 locale、知识库、鉴权等）。
- `docs/`：说明文档。

## 赶快开始
> 默认使用 MySQL 8+，请先准备数据库并配置好环境变量；FAISS 索引与切片文件已在 .gitignore 中。

### 后端
1. 创建 MySQL 数据库（默认名 `classweaver`），在 `.env` 设置 `MYSQL_DATABASE/MYSQL_USER/MYSQL_PASSWORD/MYSQL_HOST/MYSQL_PORT`，或直接使用 `DATABASE_URL=mysql://user:pass@host:3306/dbname`。
2. 安装并启动：
```bash
python -m venv .venv
. .venv/Scripts/activate   # Windows
pip install -r requirements.txt    # 包含 mysqlclient
cp .env.example .env
python manage.py makemigrations core   # 表最小化：未启用 Django admin
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

### 前端
```bash
cd webapp
npm install
cp .env.example .env       # 设置 API base
npm run dev -- --host
npm run build              # 生成 dist 用于部署
```

### 知识库
- 知识库/文件夹：先创建知识库，再向该库上传多个文件；同一用户的库彼此独立。
- API：`GET/POST /api/kb/bases/` 列表/创建库；`DELETE /api/kb/bases/<base_id>/` 删除库（级联文件）。
- 上传：`POST /api/kb/upload/` 携带 `base_id`（若不传自动使用“默认知识库”），上传 TXT/PDF/DOCX/PPTX；后台写入 `KnowledgeBase -> KnowledgeDocument -> KnowledgeChunk`。
- 检索：`POST /api/kb/search/` 必须带 `base_id`，仅在当前用户该库内检索；向量召回后再按库/文档过滤，避免错库。
- 删除：`DELETE /api/kb/documents/` 清空当前用户所有文件；`DELETE /api/kb/documents/<doc_id>?base_id=<id>` 删除指定库的单个文件。

### 登录 / 注册
- API：`POST /api/auth/register/`、`POST /api/auth/login/`、`POST /api/auth/logout/`、`GET /api/auth/me/`
- 前端：`/login`、`/register`；登录后会话 Cookie 自动携带。若接口返回 401，会自动清理前端缓存并跳转登录。

### 前端小提示
- 打印、时间线、知识库等路由都依赖登录态；刷新不会丢失缓存，会话失效时会在下次接口调用时要求重新登录。
- 时间线支持拖拽排序，卡片整块跟随移动；滚动区已放大到便于查看。

## 测试
后端：`pytest -q`（测试已自动使用内存 SQLite，默认无需 MySQL；若想连真实库，可先导出 `DATABASE_URL`）。前端：`npm run build`。

## 其他提示
- 保持 `Accept-Language=zh-CN` 以获得中文输出。
- 前端 fetch 默认 `credentials: include`，跨域时需注意 CORS 与同源策略。

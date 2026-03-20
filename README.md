# ClassWeaver Micro-Agents（V3）

面向中国学生的学习助教：上传资料 → 对话生成学习路线 → 掌握知识点 → 测验 → 陪学助教讲解。时间线可拖拽，讲义一键打印。

## 产品亮点
- 多智能体学习路线：Planner / Rewrite / Tutor 协同输出知识点、练习与测验，给出下一步学习步骤。
- 知识库驱动：按知识库上传 PDF/DOCX/PPTX/TXT，检索只命中当前库，避免答非所问。
- 学习计划时间线：事件与推荐步骤写入时间线，可拖拽调整顺序，陪学助教可直接引用。


## 体验路径
1) 登录/注册后，在“知识库”创建并上传资料。
2) 回到首页选择知识库，对话输入需求或上传 PPT，生成知识点、练习与测验。
3) 在总览页查看学习步骤、测验预览、时间线；可拖拽步骤、发起测验、打印讲义。
4) “课堂教练”按场景陪学，历史页可回顾最近任务，本地缓存可随时清理。

## 快速启动
> 当前开发基线使用 PostgreSQL + Redis；向量检索默认使用 pgvector，FAISS 保留为本地回退方案。

**基础设施**
```bash
docker compose up -d postgres redis
```
如果本机已有 PostgreSQL / Redis 占用默认端口，可在 `.env` 中覆盖 `POSTGRES_HOST_PORT` / `REDIS_HOST_PORT`。

Windows 下可直接执行：
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\ensure-dev-infra.ps1
```
该脚本会尝试拉起 Docker Desktop，并等待 PostgreSQL / Redis 端口就绪。

**后端**
```bash
py -3.11 -m venv .venv
. .venv/Scripts/activate        # Windows
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env            # 配置 PostgreSQL / Redis / API_KEY / 模型
                                # 若改了 POSTGRES_HOST_PORT，也要同步更新 DATABASE_URL / POSTGRES_PORT
                                # 若前端 dev server 自动切到 5176+，请同步维护 FRONTEND_ORIGINS / CSRF_TRUSTED_ORIGINS
                                # 本地 HTTP 开发请保持 SESSION/CSRF_COOKIE_SAMESITE=Lax；只有 HTTPS 反向代理下再改成 None
python manage.py makemigrations core
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

**Celery Worker**
```bash
. .venv/Scripts/activate
celery -A celery_app worker -l info
```

**前端**
```bash
cd webapp
npm install
cp .env.example .env   # 设置 VITE_API_BASE
npm run dev -- --host
npm run build          # 部署使用
```

## 使用要点
- 会话：前端缓存用户信息；任意接口 401 会清空缓存并跳转登录。
- 知识库：上传必须带 base_id，检索/问答只在当前库；默认使用 pgvector，并启用 dense + lexical hybrid retrieval + 轻量 rerank；切换到 FAISS 时索引写入 `data/` 且不会入仓库。
- 时间线：单列滚动区，拖拽即可调整学习顺序，陪学助教可直接引用。
- 预习任务：接口负责入队，实际执行由 Celery worker 处理。

## 文档
- `docs/需求分析.md`：角色与需求
- `docs/详细设计.md`：模块与数据设计
- `docs/用户手册.md`：操作指南与常见问题
- `docs/benchmark/README.md`：检索评测数据集与运行说明

## 测试
后端：`pytest -q`（默认内存 SQLite；如需真实库请设置 `DATABASE_URL`）。  
前端：`npm run build` 验证构建。

## 工程基线
- 推荐 Python `3.11` 与 Node `20`
- 开发依赖见 `requirements-dev.txt`
- GitHub Actions 会在 `main` 上执行后端测试与前端构建

## 状态
V3，当前开发基线为 PostgreSQL + Redis + pgvector。本仓库不包含模型与索引文件，请自行配置 API_KEY 与模型名称。

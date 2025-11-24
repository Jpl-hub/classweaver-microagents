# ClassWeaver Micro-Agents（V3）

面向学生的中文学习助教：上传资料 → 对话生成学习路线 → 掌握知识点 → 测验 → 陪学助教讲解。时间线可拖拽，讲义一键打印。

## 产品亮点
- 多智能体学习路线：Planner / Rewrite / Tutor 协同输出知识点、练习与测验，给出下一步学习步骤。
- 知识库驱动：按知识库上传 PDF/DOCX/PPTX/TXT，检索只命中当前库，避免答非所问。
- 学习计划时间线：事件与推荐步骤写入时间线，可拖拽调整顺序，陪学助教可直接引用。
- 登录与会话：Session + CSRF，前端缓存登录态；接口 401 会清理缓存并要求重新登录。
- 全中文体验：界面与生成结果默认为简体中文。

## 体验路径
1) 登录/注册后，在“知识库”创建并上传资料。
2) 回到首页选择知识库，对话输入需求或上传 PPT，生成知识点、练习与测验。
3) 在总览页查看学习步骤、测验预览、时间线；可拖拽步骤、发起测验、打印讲义。
4) “课堂教练”按场景陪学，历史页可回顾最近任务，本地缓存可随时清理。

## 快速启动
> 默认使用 MySQL 8+ 与本地 FAISS（索引文件已被 .gitignore 排除）。

**后端**
```bash
python -m venv .venv
. .venv/Scripts/activate        # Windows
pip install -r requirements.txt # 含 mysqlclient
cp .env.example .env            # 配置 MySQL / API_KEY / 模型
python manage.py makemigrations core
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
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
- 知识库：上传必须带 base_id，检索/问答只在当前库；FAISS 索引写入 `data/`，不会入仓库。
- 时间线：单列滚动区，拖拽即可调整学习顺序，陪学助教可直接引用。

## 文档
- `docs/需求分析.md`：角色与需求
- `docs/详细设计.md`：模块与数据设计
- `docs/用户手册.md`：操作指南与常见问题

## 测试
后端：`pytest -q`（默认内存 SQLite；如需真实库请设置 `DATABASE_URL`）。  
前端：`npm run build` 验证构建。

## 状态
V3，默认 MySQL + FAISS。本仓库不包含模型与索引文件，请自行配置 API_KEY 与模型名称。***

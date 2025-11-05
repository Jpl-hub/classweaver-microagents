# ClassWeaver Micro-Agents

端到端的课堂预习与练习agent，自动生成预习资料、测验题目与辅导反馈。

## 功能亮点
- Django REST 后端串联 Planner、Rewriter、Tutor 三个agent。
- Vue 3 + Vite 单页应用覆盖教师、学生与打印视图。
- 兼容 SiliconFlow 平台的 OpenAI 客户端（Qwen / DeepSeek）及统一 trace。
- 支持 RAG，默认使用 FAISS 向量库，可按需切换 pgvector。

## 前置条件
- Python 3.11 与 pip（推荐 Windows PowerShell / macOS 终端操作）。
- Node.js 18+ 与 npm。
- SiliconFlow 账户获取 `BASE_URL=https://api.siliconflow.cn/v1` 与个人 `API_KEY`。
- （可选）如启用 RAG，需准备待导入的 `.txt/.pdf/.docx/.pptx` 资料。

## 快速上手步骤

### 1. 初始化后端环境
```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows
pip install -r requirements.txt
cp .env.example .env
```
打开 `.env`，至少配置：
- `BASE_URL=https://api.siliconflow.cn/v1`
- `API_KEY=sk-...`（勿提交到仓库）
- `EMBEDDING_MODEL`、`VECTOR_BACKEND` 如默认即可；若用 pgvector，按注释补充数据库连接。
- `FRONTEND_ORIGIN=http://127.0.0.1:5173`（确保与前端访问端口一致，避免 CORS 拒绝）。

### 2. 准备数据库并启动后端
```bash
python manage.py migrate
python manage.py runserver
```
- `python manage.py migrate` 会同步最新迁移，重复执行是安全的，可确保数据表结构正确。
- `python manage.py runserver` 会阻塞当前终端进行调试，若需继续操作请在新的终端窗口执行其它命令。
- （可选）执行 `python manage.py createsuperuser` 创建管理员账号，方便登录 Django Admin。
后端默认监听 `http://127.0.0.1:8000/`，所有 API 均已挂载在 `/api/`。

### 3. 启动前端
```bash
cd webapp
npm install
cp .env.example .env
npm run dev
```
前端开发服务器默认在 `http://127.0.0.1:5173/`，页面会向后端 `http://127.0.0.1:8000/api/` 请求数据。

### 4. （可选）构建 FAISS 知识库
1. 确保后端正在运行，`.env` 中已配置 SiliconFlow 凭据。
2. 在前端首页底部的“导入资料并检索知识库”模块，选择 `.txt/.pdf/.docx/.pptx` 文件，点击“上传到知识库”，界面会显示切片数量及提醒（若切片为 0，请先 OCR）。
3. 需要脚本化导入时，可在仓库根目录建立 `corpus/` 并使用接口：
```bash
curl -X POST http://127.0.0.1:8000/api/kb/upload/ \
  -F "file=@corpus/你的资料.pdf"
```
请求成功后，向量索引与元数据会写入 `data/faiss.index` 与 `data/chunks.jsonl`。

上传完成后可在同一模块输入关键词检索，确认知识片段是否可用。生成预习资料时系统会自动调用这些上下文。

### 5. 校验与构建
- 后端单元测试：`pytest`
- 前端构建：`cd webapp && npm run build`
首次执行建议在依赖、凭据和（如开启）FAISS 数据准备完成后运行，以确认环境无误。

## 常见问题
- **没有 SiliconFlow Key**：可先在 `.env` 中填占位值，仅使用本地数据与 RAG 会失败，但其余页面可加载。
- **RAG 不需要**：跳过步骤 4 即可，代理将仅基于输入文本/PPT 生成内容。

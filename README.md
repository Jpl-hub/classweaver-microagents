# ClassWeaver Micro-Agents（中文版）

ClassWeaver 是基于 Planner / Rewriter / Tutor / Timeline 的多智能体教学编排系统，提供课程生成、知识库检索、课堂测验、陪学教练、打印讲义等功能。本版本已全面中文化，支持自建知识库的增删改查，并强制生成中文内容。

## 关键特性
- **多智能体流水线**：Planner 拆解知识点与测验大纲，Rewriter 精炼题目，Tutor 生成练习与总结，支持实时状态轮询与模型调用轨迹。
- **知识库 + RAG**：上传 PDF/DOCX/PPTX/TXT 等资料，自动切片向量化；任务可指定 `doc_ids`，知识搜索与生成均可绑定指定库。
- **测验与教练**：随时发起测验（题目/会话持久化），陪学教练按场景导航知识点、练习与行动。
- **讲义打印与行动清单**：打印知识点/术语/测验/练习；行动推荐支持记录状态、写入时间线和教学事件。
- **中文输出与去重提醒**：所有 Agent 提示强制中文；“课程已生成”提示仅对同一任务播报一次并持久化去重。
- **知识库管理**：前端支持删除单个知识库或一键清空（默认库不可删），后端提供 `/api/kb/documents/` `DELETE` 接口。

## 目录结构
- `src/agents/`：Planner/Rewrite/Tutor 逻辑与提示模板。
- `src/api/`：DRF API 视图与序列化，知识库/课程/测验/推荐/时间线接口。
- `src/services/`：流水线、打印、PPT 解析、推荐、评分等服务。
- `webapp/src/views/`：Vue3 前端页面（Home/Knowledge/Coach/Take/Print/History）。
- `webapp/src/services/api.ts`：前端 API 客户端（包含 locale/语言头、知识库删除接口）。
- `docs/`：`用户手册.md`、`需求说明.md`、`详细设计.md`。

## 快速开始
### 后端
```bash
python -m venv .venv
. .venv/Scripts/activate   # Windows
pip install -r requirements.txt
cp .env.example .env       # 配置数据库/模型等
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

### 前端
```bash
cd webapp
npm install
cp .env.example .env       # 配置 API base 等
npm run dev -- --host      # 开发
npm run build              # 生产构建（dist 已使用最新代码）
```

### 知识库操作
- 上传：在“知识库”页选择文件（支持 TXT/PDF/DOCX/PPTX），后台写入 `KnowledgeDocument/Chunk` 与向量库。
- 绑定：在首页下拉选择要使用的知识库，生成任务会携带 `doc_ids`；知识搜索也会过滤到选定库。
- 删除：在“知识库”页可删除单个知识库或“清空全部知识库”（默认库不可删），对应接口 `DELETE /api/kb/documents/<doc_id>/` 与 `DELETE /api/kb/documents/`。

## 测试
当前环境未安装后端依赖（`django`, `djangorestframework`, `openai` 等），`pytest -q` 会因缺依赖报错。安装 `requirements.txt` 后再运行：
```bash
pytest -q              # 后端测试
cd webapp && npm run build   # 前端构建验证
```

## 常见问题
- **生成仍出现英文**：请先清空旧知识库/任务，确保前端已重建，后台加载了最新 Agent 提示；需要模型遵循 `locale=zh-CN` 和中文 prompt。
- **重复“课程已生成”**：已在前端去重并持久化；如仍重复，清空浏览器 sessionStorage 再试。
- **知识库异常或旧数据**：使用“清空全部知识库”后重新上传，再重新生成课程/测验。***

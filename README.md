# ClassWeaver Micro-Agents（V3）

面向中文课堂的AI教学与陪练工具。上传你的资料，系统自动规划课程、生成测验与行动建议，时间线可拖拽，讲义一键打印。

## 产品亮点
- 多智能体流水线：Planner/Rewrite/Tutor 协同生成知识点、测验、练习与总结。
- 知识库严格隔离：按知识库上传 PDF/DOCX/PPTX/TXT，检索只命中当前用户的当前库，向量召回后二次过滤避免错库。
- 课堂时间线与行动：事件、测验、推荐动作写入时间线，可拖拽排序；打印视图随时导出。


## 体验路径
1) 登录/注册后，先在“知识库”创建并上传资料。
2) 回到首页选择知识库，输入意图或上传 PPT，生成课程/测验/练习。
3) 在课程总览查看知识点、测验预览、行动指南与时间线；可发起测验、拖拽事件、打印讲义。
4) “课堂教练”按场景导航，“历史”可查看最近任务。

## 快速启动
> 默认使用 MySQL 8+ 与本地 FAISS，索引文件已被 .gitignore 排除。

**后端**
```bash
python -m venv .venv
. .venv/Scripts/activate        # Windows
pip install -r requirements.txt # 包含 mysqlclient
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
npm run build          # 部署时使用
```


## 测试
后端：`pytest -q`（默认使用内存 SQLite；如需真实库请设置 `DATABASE_URL`）。  
前端：`npm run build` 验证构建。

## 状态
当前为 V3，默认 MySQL + FAISS。本仓库不包含模型与索引文件，请按需配置 API_KEY 与模型名称.
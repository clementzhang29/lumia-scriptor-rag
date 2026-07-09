# Lumia ScriptorRAG 文档索引

生成时间：2026-07-06
作者：张春
说明：AI 根据项目文件、运行状态和迭代过程整理生成。

## 产品定位

**Lumia ScriptorRAG｜序光文枢 RAG** 是一个把 OCR 智能体、Markdown 排版清洗和通用 RAG 知识库融合在一起的本地文档智能系统。当前本地目录名保持为 `ocr-harness-v0.1.0`，但产品名、GitHub 仓库名、界面名称和文档名称统一为 Lumia ScriptorRAG。

核心链路：

```text
PDF / 扫描件 / 本地资料
  → 光棱 OCR：多引擎识别、智能路由、质量评分、失败回退
  → 字炉排版：Markdown 清洗、结构整理、噪声字符移除
  → 文枢 RAG：多文档索引、来源去重、原典优先、可追溯问答
  → WebUI / API / 导出
```

## 核心文档

- `docs/project-introduction.html`：完整项目介绍 HTML，可直接浏览器打开，用于作品集、项目展示和答辩说明。
- `docs/open-source-introduction.en-zh.md`：面向 GitHub 开源发布的中英文项目介绍。
- `docs/deployment-zclum-con.md`：部署到 `zclum.con` 的轻应用上线指南。
- `docs/aliyun-ecs-checklist.md`：阿里云 ECS 信息确认、端口放行和 DNS 记录清单。
- `docs/deployment-paths.md`：Docker Compose、1Panel、宝塔三种上线路径。
- `docs/operations-checklist.md`：DNS、安全组、HTTPS、备份恢复和日志排障清单。
- `docs/local-package-and-healthcheck.md`：本地打包上传和服务器健康检查说明。
- `docs/zclum-agent-integration.md`：zclum / 来客有方接入 OCR-Harness 智能体的 API 和网关说明。
- `docs/detailed_project_introduction.md`：详细项目介绍，覆盖项目定位、技术架构、实现过程、问题解决、最终状态和简历扩展版介绍。
- `docs/resume_project_blurb.md`：简历用项目介绍，可复制到简历或求职平台。
- `docs/ai_handoff.md`：AI / 开发者交接文档，说明架构、模块边界、运行方式和后续路线。
- `docs/agent_build_process.md`：智能体构建关键过程复盘，从 OCR 到排版再到 RAG 的产品化过程。
- `docs/pitfalls_and_solutions.md`：踩坑与解决方案记录，覆盖 Windows 启动、OCR 依赖、前端静态资源、RAG 质量等问题。
- `docs/final_delivery_note.md`：最终交付说明，记录最终版状态和发布前检查清单。
- `docs/frontend_design_system_review.md`：前端设计系统提取、审美方向、层级节奏、交互状态和 polish-pass 记录。
- `docs/knowledge_mounts.md`：外部知识源挂载说明，覆盖 local_dir / WebDAV / AList 与挂载建库流程。
- 前端帮助页：启动后访问 `http://127.0.0.1:8080/help`，面向普通用户说明使用、迁移、RAG 流程和二次开发。

## 快速验证

```powershell
cd C:\Users\35160\Documents\Codex\ocr-harness-v0.1.0
py -3 -B -m uvicorn src.web.app:app --host 127.0.0.1 --port 8080 --log-level info
```

浏览器打开：

- 产品首页：`http://127.0.0.1:8080/`
- API 文档：`http://127.0.0.1:8080/docs`
- 帮助说明：`http://127.0.0.1:8080/help`

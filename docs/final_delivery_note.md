# Lumia ScriptorRAG 最终交付说明

生成时间：2026-07-06
作者：张春
说明：AI 根据项目文件整理生成。

## 最终版状态

- 产品名称：Lumia ScriptorRAG｜序光文枢 RAG。
- 本地目录名：保持 `ocr-harness-v0.1.0` 不变。
- GitHub 仓库：`lumia-scriptor-rag`，私有状态。
- 前端导航：已改为图标 + 2~3 字短文案，避免竖排、拥挤和越界。
- 白屏问题：已修复 FastAPI 静态资源挂载，`/assets/*.js` 正确返回 JavaScript。
- 前端设计：已按 design-system-extract、frontend-aesthetic-direction、hierarchy-rhythm-review、interaction-states-pass、ai-slop-check、polish-pass 完成真实页面优化。
- 知识库挂载：已新增本地目录 / WebDAV / AList 三类知识源挂载、同步缓存与挂载建库入口。
- 模型中心：已接入持久化 Provider、模型目录读取、价格展示与供应商隐藏显示。
- 文档：项目介绍、交接文档、构建过程、踩坑记录、简历介绍和帮助说明已同步。

## 最终架构

```text
光棱 OCR：PDF 上传、多 OCR 引擎路由、质量评分、失败回退
字炉排版：Markdown 清洗、结构修复、噪声字符移除
文枢 RAG：多格式建库、来源去重、原典优先、可追溯问答
星轨模型：OpenAI 兼容 Provider 与多厂商 LLM 配置
WebUI/API：前端交互、导出、帮助说明和二次开发入口
知识源挂载：外部目录与云盘接入、本地缓存同步、挂载建库
```

## 发布前检查

1. 不提交 API Key、上传文件、日志、大模型和临时下载文件。
2. 修改前端后执行 `cd frontend && npm run build`。
3. 启动后访问 `http://127.0.0.1:8080/`，确认首页、帮助页、RAG 页均可打开。
4. 端到端 OCR 可用时执行 `py -3 -B test_e2e.py`。
5. 前端构建与浏览器检查记录见 `docs/frontend_design_system_review.md`。
6. 知识源挂载回归可执行 `py -3 -m unittest tests.test_kb_mounts -v`。

# Lumia ScriptorRAG 前端设计系统审查与最终优化记录

生成时间：2026-07-07
作者：张春
说明：AI 根据项目文件、运行页面和本次前端优化过程整理生成。参考 Trystan-SA/claude-design-system-prompt 的公开设计工作流思想，但不照搬为 Anthropic 官方规范。

## design-system-extract

当前前端采用 Vue3 + Vite + Naive UI，视觉语言已经形成“本地文档工作台”方向：

- **颜色**：暖纸色背景 `#f4f0e8`，高层面板 `#fffdf8`，主色为深青绿色 `#167267 / #11564f`，少量琥珀色 `#b36a14` 用于强调。
- **字体**：中文优先使用 `Noto Sans SC / PingFang SC / Microsoft YaHei UI`，代码与导出内容保留等宽字体栈。
- **间距**：采用 4px 基准的变量体系，常用间距为 12、16、20、24、32、40、48、64。
- **圆角**：整体圆润但克制，卡片 22px，英雄区 30px，按钮 12–16px。
- **阴影**：低对比柔和阴影，强调“纸面浮层”而不是强烈玻璃拟态。
- **组件密度**：中低密度，适合 OCR / RAG 这类长任务工作台，不使用过度营销式大留白。
- **动效语言**：轻微 hover 上浮、颜色变化、阴影增强；使用 `prefers-reduced-motion` 保护低动效偏好。

## frontend-aesthetic-direction

最终审美方向定义为：

> 温润的本地知识工作台：像一张整理文献的书桌，强调可信、清晰、可持续操作，而不是 AI SaaS 落地页式炫技。

设计取舍：

- 保留暖纸色背景和深青主色，强化“文档、古籍、知识库”的质感。
- 不使用廉价紫粉蓝渐变、无意义装饰图形和夸张营销话术。
- 优先优化真实可运行页面：OCR 首页、排版页、RAG 页、模型配置页、结果页、帮助页。

## hierarchy-rhythm-review

已优化：

- 顶部导航压缩为 `OCR / 导览 / 排版 / RAG / 模型 / 帮助`，避免长中文在中等宽度下竖排和越界。
- 页面英雄区统一为“eyebrow + 大标题 + 说明文字 + 操作区域”的节奏。
- 工作卡片保留明确标题、说明、主操作，减少信息堆叠。
- 首页三张状态卡统一为引擎可用性、质量阈值、模型 Provider，形成清晰仪表盘。
- 排版页和 RAG 页采用左右工作区，移动端自动收敛为单列。

## interaction-states-pass

已补齐：

- 导航 hover / active / focus-visible。
- 上传区 hover / active / ready 状态。
- 快捷卡 hover / active / disabled / note 状态。
- 空状态：排版结果、RAG 回答等待区均有明确提示。
- loading：OCR 上传、Markdown 清洗、RAG 建库与检索、Provider 保存。
- disabled：未选择文件、未输入内容、无回答结果时禁用相关操作。
- error：API 异常通过 Naive UI message / alert 反馈。

## ai-slop-check

已清理：

- 修复前端主要页面历史乱码文案。
- 删除“看起来像模板”的无效长导航文案。
- 避免 AI 常见紫粉蓝渐变和无意义装饰。
- 保留产品真实工作流，不新增营销落地页。
- 移除根目录下明显临时调试脚本和历史过程文件。

## polish-pass

验证结果：

- `npm run build` 构建通过。
- 本地服务已启动：`http://127.0.0.1:8080/`。
- 浏览器检查 `/`、`/format`、`/rag`、`/providers`、`/help` 均可正常渲染。
- 控制台未发现 error / warning。
- 桌面端无横向溢出。
- 移动端通过 CSS 响应式规则收敛为单列布局；当前浏览器插件未暴露 viewport 能力，因此未保存移动端截图，但已按断点规则完成布局处理。

## 修改文件

- `frontend/src/App.vue`
- `frontend/src/style.css`
- `frontend/src/views/Home.vue`
- `frontend/src/views/Formatter.vue`
- `frontend/src/views/Rag.vue`
- `frontend/src/views/Providers.vue`
- `frontend/src/views/Result.vue`
- `docs/frontend_design_system_review.md`

## 访问方式

```powershell
cd C:\Users\35160\Documents\Codex\ocr-harness-v0.1.0
py -3 -B -m uvicorn src.web.app:app --host 127.0.0.1 --port 8080 --log-level info
```

浏览器打开：

- 首页：`http://127.0.0.1:8080/`
- 排版：`http://127.0.0.1:8080/format`
- RAG：`http://127.0.0.1:8080/rag`
- 模型：`http://127.0.0.1:8080/providers`
- 帮助：`http://127.0.0.1:8080/help`

# Lumia ScriptorRAG 智能体构建关键过程

生成时间：2026-07-06
作者：张春
说明：AI 根据项目文件与迭代过程整理生成。

## 初始目标

项目最初定位为 OCR-Harness：一个多模型智能编排的 PDF → Markdown 转换系统。目标不是简单调用一个 OCR 引擎，而是让系统根据文档类型自动选择引擎、评估质量、必要时回退，并把结果整理成可读 Markdown。

## 能力融合

在 OCR 主链路跑通后，项目继续融合两个能力：

1. **字炉排版**：对 OCR Markdown 进行清洗、标题修复、段落整理、噪声字符去除。
2. **文枢 RAG**：把清洗后的 Markdown、PDF、HTML、EPUB、DOCX 等资料统一导入索引，形成可追溯问答系统。

最终形成：

```text
OCR 智能体路由 → Markdown 排版优化 → 通用 RAG 建库与问答
```

三个子模块都可以独立使用，也可以串联成完整产品。

## 关键实现

- 使用 FastAPI 提供 OCR、排版、RAG、LLM Provider 管理 API。
- 使用 Vue3 + Vite + Naive UI 构建本地 WebUI。
- 使用 `src/orchestrator/` 管理文档分析和 OCR Pipeline。
- 使用 `src/engines/` 封装 Surya、MinerU、Docling、Marker、PaddleOCR、Nougat。
- 使用 `src/formatter/` 做 Markdown 清洗。
- 使用 `src/ingest/` 与 `src/rag/` 实现通用文档导入和 BM25 检索。
- 使用 `src/llm/` 抽象 OpenAI 兼容和多厂商 Provider。

## 产品化过程

1. 验证 Surya OCR 端到端工作流。
2. 补充 MinerU、Docling 等引擎适配与依赖处理。
3. 将 OCR 输出整理为 Markdown，并加入质量评分。
4. 将已整理文档导入 RAG，要求一个问题至少返回多个不同文档来源。
5. 增加前端 RAG 检索、导出、复制、Provider 设置和帮助说明。
6. 品牌重命名为 Lumia ScriptorRAG｜序光文枢 RAG。
7. 修复 Windows 启动、前端白屏、静态资源挂载和导航拥挤问题。

## 当前最终版

最终版保留 OCR 智能体作为入口，RAG 作为下游知识应用；界面采用精简顶部导航，栏目包括 OCR、导览、排版、RAG、模型、帮助，避免文字拥挤和越界。

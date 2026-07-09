# 简历项目介绍：Lumia ScriptorRAG

Lumia ScriptorRAG（序光文枢 RAG）是一个多模型智能编排的本地文档数字化与知识库系统，围绕“光棱 OCR → 字炉排版 → 文枢 RAG”的完整链路设计。项目集成 Surya、MinerU、Docling、Marker、PaddleOCR、Nougat 等 OCR 引擎，支持文档类型分析、自动路由、质量评分、失败回退、LLM 增强校正和 Markdown 导出；同时扩展通用 RAG 能力，支持 md/txt/html/pdf/epub/docx 多格式建库、来源去重、原典权重提升、至少 5 条不同文档引用返回，以及检索结果复制与多格式导出。

本人负责项目整体架构设计、FastAPI 后端接口、OCR Pipeline 编排、LLM Provider 抽象、多格式文档导入、BM25 检索模块、Vue3 + Naive UI 前端产品化、本地启动脚本与项目交付文档建设。实现过程中解决了 Windows 本地 Python 启动兼容、OCR 引擎 GPU/DLL 依赖冲突、Vue History 路由刷新、FastAPI 静态资源白屏、RAG 检索来源去重、OCR 噪声清洗、前后端 API 串联和 GitHub 私有仓库交付等问题。该项目可作为本地文档数字化、古籍/行业资料知识库构建和可追溯问答系统的通用底座。

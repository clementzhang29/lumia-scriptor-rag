# Lumia ScriptorRAG 产品融合架构

## 产品定位

Lumia ScriptorRAG（序光文枢 RAG）的主产品定位是“文档智能体与知识中枢”。光棱 OCR 是入口，字炉排版是中段整理，文枢 RAG 是文档清晰整理后的下游知识应用能力，不替代 OCR 主线。

## 总体流水线

```text
文件/文件夹输入
  ↓
光棱 OCR 路由
  - 文档分析
  - Surya / MinerU / Docling / Marker / PaddleOCR / Nougat 路由
  - 质量评分与失败回退
  ↓
字炉排版
  - Markdown 清洗
  - 表格 / 公式 / 顺序校正
  - 噪声字符、水印、异常空行清理
  ↓
文枢 RAG
  - 支持 md/txt/html/pdf/epub/docx 建库
  - 至少返回 5 条不同文档来源
  - 优先提升古籍/原典权重，近现代资料作为补充
  ↓
WebUI / API / 导出
  - OCR 结果下载
  - 检索答案复制与导出
  - Provider / 引擎 / 索引路径配置
```

## 模块边界

- `src/orchestrator/`：光棱 OCR 主调度，负责文档分析、引擎选择、质量回退。
- `src/engines/`：OCR 引擎适配层，各引擎可单独调用。
- `src/formatter/`：字炉排版与 Markdown 清洗，可作为独立接口使用。
- `src/ingest/`：通用文档导入层，将 md/txt/html/pdf/epub/docx 转成统一文档对象。
- `src/rag/`：文枢 RAG 检索层，独立建库、检索、来源去重与排序。
- `src/llm/`：OpenAI 兼容与多厂商 Provider，供 OCR 校正和 RAG 综合回答复用。
- `src/web/`：统一 FastAPI API，对外暴露光棱 OCR、字炉排版、文枢 RAG、星轨模型管理。

## 当前已接入 API

- `POST /api/convert`：上传文件并执行光棱 OCR 流水线。
- `POST /api/format/markdown`：独立字炉 Markdown 排版。
- `POST /api/rag/rebuild`：从资料目录重建文枢 RAG 索引。
- `POST /api/rag/query`：基于当前索引问答，返回答案与引用来源。
- `GET /api/rag/status`：查看 RAG 索引数量与存储目录。
- `POST /api/providers`：注册 LLM Provider，供 OCR 校正和 RAG 回答复用。

## 发布形态建议

第一版发布应保留三个独立入口：

1. 光棱工作台：上传 PDF，选择自动路由或指定引擎，输出 Markdown。
2. 字炉整理台：粘贴或导入 Markdown，清洗排版并导出。
3. 文枢 RAG：选择清洗后的文档目录，重建索引，问答并导出结果。

这样既能串成完整产品链路，也能让每个子模块单独使用。

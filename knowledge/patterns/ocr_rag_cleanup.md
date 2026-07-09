# OCR Markdown 清洗与 RAG 接入修复

## 背景
- `pdf_ocr` 新产出的 Markdown 已覆盖全部 PDF，但存在图片占位、水印、孤立符号行和残缺目录表。
- WebUI 文案存在乱码，`/rag/query` 在外部 LLM 不可用时会直接 500。

## 处理策略
- 对 `pdf_ocr/*.md` 做保守源文档清洗：移除 `<!-- image -->`、`A-PDF MERGER DEMO`、纯符号噪声行，统一 `# #` 标题。
- 在 `DocumentParser` 再做一次读取期清洗，避免残余噪声进入索引。
- `RAGEngine` 增加标题归一化、去重和 LLM 失败回退，保证检索问答至少可返回本地出处摘要。
- `server.py` 增加 `/rag/rebuild`，并优先索引 `pdf_ocr`。
- `outputs/chatbox.html` 改成无乱码的简洁本地问答界面。

## 经验
- OCR 修复优先做确定性的减法，先清除外来水印、目录残片和孤立符号，不轻易自动改正文实词。
- 对中医古籍这类长文档，索引入口做二次清洗比只修源文件更稳。
- 依赖外部 LLM 的 RAG 接口必须有本地回退，否则验收经常被第三方接口状态拖住。

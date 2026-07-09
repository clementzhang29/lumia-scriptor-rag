# TCM PDF Batch OCR Pipeline — OpenSpec Proposal

## Background
46 本中医古籍 PDF 需要 OCR 提取为 Markdown。部分已有 PaddleOCR 提取版（43 个 MD）和纯文本版（69 个 TXT）。
当前 PaddleOCR 提取存在明显错误（错字、粘连），Docling/Surya 引擎质量更高。

## Goals
1. 批量 OCR 所有 PDF（跳过已处理过的，或重新处理以提升质量）
2. 与已有 MD/TXT 做质量比对，选择最优版本
3. 输出标准化 Markdown，适合 RAG 向量化

## Design Decisions
- 引擎优先级：Docling → Surya → PaddleOCR（Docling 在之前测试中表现最好 0.78 质量分）
- 质量门槛 0.85：超阈值直接使用，否则回退其他引擎
- 已有 TXT 作为 baseline 参考
- 输出到 pdf_ocr 目录，以 {书名}_docling.md 命名
- 对比逻辑：提取后再评分，高于现有的就覆盖

## Tasks
1. 创建 batch_process.py 批量扫描 + 调度引擎
2. 创建 quality_compare.py 比对已有输出（TXT/MD）择优
3. 运行完整批处理
4. 记录知识沉淀

# Lumia Graph-RAG Core：书籍知识图谱与信号图谱搜索 PRD / 技术路线

生成时间：2026-07-08  
作者：张春  
整理说明：AI 根据 Lumia ScriptorRAG 当前项目方向、Karpathy LLM Wiki / 大规模 RAG 思路、信号图谱检索设想、Gradio 实验台需求与 Harness 规格化工作流整理生成。本文档作为后续开发灵感备忘与技术立项草案。

---

## 1. 项目背景

当前 Lumia ScriptorRAG 已具备 OCR、Markdown 清洗、基础 RAG 检索和前端工作台能力。下一阶段希望把系统升级为更通用的 **Graph-RAG Core**：

1. 对 **一万本 Markdown 电子书** 建立类似 Wiki / 目录 / 章节 / 概念 / 引用关系的知识图谱，使大规模 RAG 检索仍然精准、可解释、可追溯。
2. 对 **信号、特征图或单个信号片段** 建立类似“章节目录”的信号图谱，把原始信号编码成多尺度结构、局部模式、频谱关系和相似边，从而实现更省算力、更精准的相似卷积搜索匹配。

核心灵感：

> 书籍可以被组织成“书 → 卷 → 章 → 段落 → 概念 → 引用关系”；  
> 信号也可以被组织成“信号 → 时间窗口 → 局部模式 → 频谱结构 → 相似关系”。

---

## 2. 产品目标

### 2.1 书籍知识图谱目标

面向 1 万本已转 Markdown、已做格式优化的电子书，构建可检索、可追溯、可解释的知识图谱与 RAG 索引。

目标能力：

- 支持 1 万本级别 Markdown 文档导入。
- 自动识别书名、作者、年代、类别、目录、章节。
- 生成书籍卡片、章节摘要、主题页、概念页。
- 支持“精准 / 平衡 / 综述 / 考据”四种检索模式。
- 综述模式下尽量覆盖 20 本左右素材。
- 回答必须保留出处，支持回到原始章节与段落。
- 支持后续 Neo4j / SQLite / DuckDB / Qdrant / LanceDB 等多种存储形态。

### 2.2 信号图谱目标

面向信号数据、时序数据、频谱图、CNN 特征图或单个信号片段，构建结构化信号图谱，用于相似模式检索、异常定位、故障模式匹配和局部卷积精排。

目标能力：

- 将长信号切分为多尺度片段。
- 提取时域、频域、时频域、小波、特征图 embedding。
- 构建 SignalNode、SegmentNode、PatternNode、SpectralNode、EmbeddingNode。
- 通过向量召回 + 图谱过滤 + 局部卷积 / DTW / cross-correlation 精排降低算力。
- 支持相似片段检索、跨样本对齐、异常模式召回。
- 可解释输出：命中了哪个历史信号、哪个片段、哪类模式、相似依据是什么。

---

## 3. 非目标

第一阶段不做：

- 不直接训练大型基础模型。
- 不一次性上生产级分布式集群。
- 不把图数据库作为第一阶段强依赖。
- 不对全部 1 万本书做昂贵 LLM 全量重写。
- 不对信号全库做暴力卷积匹配。

第一阶段重点是：

- 建立统一数据结构。
- 跑通小规模 MVP。
- 验证“图谱召回 + 局部精排”是否比纯全量搜索更准、更省算力。

---

## 4. 用户场景

### 4.1 书籍知识图谱场景

#### 场景 A：多书综述

用户提问：

> “脾胃理论在不同医书中如何演变？请尽量覆盖多本文献。”

系统行为：

1. 识别主题：脾胃、中焦、胃气、后天之本、升清降浊。
2. 从 Wiki / 图谱层定位相关书籍和主题页。
3. 从原典、注解、现代研究中分层召回。
4. 控制单书引用数量，覆盖约 20 本。
5. 输出按来源分组的引用式综述。

#### 场景 B：精准考据

用户提问：

> “‘胃气’一词最早在哪些原典中出现？”

系统行为：

1. 优先查原典层。
2. 限制现代解释权重。
3. 返回精确条文、章节、出处。
4. 不足时说明资料不足。

### 4.2 信号图谱场景

#### 场景 C：相似故障模式检索

用户输入一段振动信号。

系统行为：

1. 预处理：去噪、归一化、重采样。
2. 切分为多尺度片段。
3. 提取频谱峰、能量带、局部突变、embedding。
4. 在向量库中召回候选片段。
5. 通过信号图谱过滤同设备、同频段、同工况候选。
6. 对 Top 100 做局部卷积 / DTW 精排。
7. 返回最相似历史模式及故障标签。

#### 场景 D：CNN 特征图模式检索

用户输入一个特征图 patch。

系统行为：

1. 提取 channel group、spatial patch、activation peak。
2. 检索相似 activation pattern。
3. 找到历史缺陷区域、类别原型或异常模式。
4. 返回可视化匹配区域。

---

## 5. 核心架构

```text
Lumia Graph-RAG Core
├── Book Graph-RAG
│   ├── Raw Markdown Corpus
│   ├── Book / Chapter / Chunk Parser
│   ├── LLM Wiki Compiler
│   ├── Entity & Relation Extractor
│   ├── Hybrid Retriever
│   ├── Reranker
│   ├── Diversity Selector
│   └── Citation Answer Builder
│
├── Signal Graph Search
│   ├── Signal Preprocessor
│   ├── Multi-scale Segmenter
│   ├── Feature Extractor
│   ├── Signal Encoder
│   ├── Pattern Miner
│   ├── Graph Store
│   ├── Vector Store
│   ├── Candidate Retriever
│   └── Local Matcher
│
└── Gradio Lab
    ├── Index Builder UI
    ├── Retrieval Debugger
    ├── Parameter Tuning
    ├── Evaluation Dashboard
    └── Export Report
```

---

## 6. 书籍知识图谱技术路线

### 6.1 分层数据结构

```text
BookNode
  id
  title
  author
  dynasty_or_year
  category
  source_path
  source_type: classic / commentary / modern / unknown

ChapterNode
  id
  book_id
  title
  chapter_path
  order
  summary

ChunkNode
  id
  chapter_id
  book_id
  content
  token_count
  page_or_line_range
  embedding_id

EntityNode
  id
  name
  type: concept / person / formula / herb / disease / method / school
  aliases
  description

WikiPageNode
  id
  slug
  title
  body
  entity_ids
  citation_ids
```

### 6.2 关系设计

```text
BOOK_CONTAINS_CHAPTER
CHAPTER_CONTAINS_CHUNK
CHUNK_MENTIONS_ENTITY
ENTITY_RELATED_TO_ENTITY
ENTITY_HAS_ALIAS
WIKI_PAGE_SUMMARIZES_ENTITY
WIKI_PAGE_CITES_CHUNK
BOOK_INFLUENCES_BOOK
PERSON_AUTHORED_BOOK
FORMULA_CONTAINS_HERB
DISEASE_TREATED_BY_FORMULA
```

### 6.3 索引策略

```text
Raw text index:
  SQLite FTS5 / Tantivy / OpenSearch

Vector index:
  Qdrant / LanceDB / FAISS

Metadata index:
  SQLite / DuckDB

Graph index:
  SQLite edge table first
  Neo4j / FalkorDB later
```

### 6.4 检索流程

```text
Query
  → Query Rewrite
  → Entity Linking
  → Wiki Page Recall
  → Book-level Recall Top 200
  → Chapter-level Recall Top 500
  → Chunk-level Hybrid Recall Top 1000
  → Rerank Top 100
  → Diversity Selection: target 20 books
  → Context Compression
  → Citation Answer
```

### 6.5 检索模式

| 模式 | 覆盖书籍 | 使用场景 |
|---|---:|---|
| 精准 | 5–8 本 | 具体条文、定义、出处 |
| 平衡 | 8–12 本 | 普通问答 |
| 综述 | 15–25 本 | 多书比较、主题演变 |
| 考据 | 20–30 本 | 原典优先、年代分层 |

---

## 7. 信号图谱技术路线

### 7.1 信号分层数据结构

```text
SignalNode
  id
  source_path
  sample_rate
  duration
  channel_count
  domain: vibration / ecg / eeg / radar / feature_map / other
  label
  metadata

SegmentNode
  id
  signal_id
  start_time
  end_time
  scale
  channel
  embedding_id

PatternNode
  id
  segment_id
  pattern_type: peak / valley / impulse / periodic / decay / burst / texture / edge
  parameters
  confidence

SpectralNode
  id
  segment_id
  main_frequency
  harmonics
  band_energy
  spectral_centroid
  bandwidth

FeatureMapNode
  id
  source_model
  layer_name
  shape
  sample_id

PatchNode
  id
  feature_map_id
  channel_range
  x
  y
  width
  height
  embedding_id
```

### 7.2 信号关系设计

```text
SIGNAL_CONTAINS_SEGMENT
SEGMENT_CONTAINS_PATTERN
SEGMENT_HAS_SPECTRUM
SEGMENT_SIMILAR_TO_SEGMENT
PATTERN_SIMILAR_TO_PATTERN
PATTERN_CO_OCCURS_WITH_PATTERN
SEGMENT_NEXT_TO_SEGMENT
PATTERN_PRECEDES_PATTERN
FEATUREMAP_CONTAINS_PATCH
PATCH_SIMILAR_TO_PATCH
PATCH_ACTIVATES_CLASS
```

### 7.3 特征提取

#### 时域特征

- 均值、方差、峰度、偏度
- RMS
- 峰峰值
- 零交叉率
- 自相关
- 局部极值分布

#### 频域特征

- FFT 主频
- 谐波结构
- 频带能量
- 频谱质心
- 频谱带宽

#### 时频特征

- STFT
- CWT
- 小波包能量
- Mel / Log Spectrogram（视场景）

#### 深度特征

- 1D CNN embedding
- 2D CNN feature map patch embedding
- AutoEncoder latent
- SimCLR / BYOL 式自监督 embedding

### 7.4 相似搜索流程

```text
Query Signal
  → Preprocess
  → Segment
  → Extract Features
  → Encode Embeddings
  → ANN Recall Top 1000
  → Graph / Metadata Filter Top 300
  → Local Matching Top 100
       - cross-correlation
       - depthwise convolution
       - DTW
       - small CNN classifier
  → Score Fusion
  → Return Top 20 Similar Patterns
```

### 7.5 融合评分

```text
score =
  0.30 * vector_similarity
+ 0.25 * spectral_similarity
+ 0.20 * local_conv_match
+ 0.15 * graph_context_score
+ 0.10 * metadata_match
```

权重应在 Gradio Lab 中可调。

---

## 8. Gradio Lab 实验台设计

Gradio 不替代正式 Vue 前端，而是作为研发实验台。

### 8.1 Book Graph-RAG Lab

功能：

- 选择资料目录。
- 构建小规模索引。
- 调整 top_k、rerank_k、target_books。
- 对比 BM25 / vector / hybrid / wiki recall。
- 展示命中的书籍、章节、chunk。
- 人工标注是否相关。
- 导出评测报告。

建议组件：

```text
gr.Textbox: 资料目录 / 问题输入
gr.Slider: top_k / rerank_k / target_books
gr.Radio: 检索模式
gr.Checkbox: 是否启用 LLM / 是否原典优先
gr.Dataframe: 命中结果表
gr.Markdown: 答案预览
gr.File: 导出报告
```

### 8.2 Signal Graph Search Lab

功能：

- 上传信号文件或特征图。
- 选择信号类型。
- 配置窗口长度、overlap、召回数量、精排数量。
- 展示波形、频谱、相似片段。
- 对比纯向量、纯卷积、图谱过滤 + 局部卷积。
- 输出耗时、召回率、Top-k 命中率。

建议组件：

```text
gr.File: 上传信号文件
gr.Dropdown: 信号类型
gr.Slider: window_size / overlap / recall_k / rerank_k
gr.Button: 构建索引 / 开始检索
gr.Plot or gr.Image: 波形和频谱
gr.Dataframe: 相似片段结果
gr.Markdown: 匹配解释
```

---

## 9. 建议目录结构

```text
src/graph_rag/
  schema.py
  stores/
    sqlite_store.py
    vector_store.py
    graph_store.py
  book/
    markdown_loader.py
    chapter_parser.py
    entity_extractor.py
    wiki_compiler.py
    hybrid_retriever.py
    reranker.py
    diversity_selector.py
    citation_builder.py
  signal/
    preprocess.py
    segmenter.py
    feature_extractors.py
    encoder.py
    pattern_miner.py
    signal_graph_builder.py
    retriever.py
    matcher.py
    evaluator.py
  eval/
    metrics.py
    benchmark.py

src/gradio_lab/
  app.py
  book_rag_lab.py
  signal_graph_lab.py
```

---

## 10. MVP 计划

### MVP-1：书籍图谱检索

数据规模：

- 100 本 Markdown。
- 每本按章节和 chunk 切分。

实现：

- SQLite 存 books / chapters / chunks。
- SQLite FTS5 做关键词检索。
- FAISS 或 LanceDB 做向量检索。
- 简单 rerank。
- Diversity selector 保证至少 10 本来源。

验收指标：

- 构建成功率 ≥ 95%。
- 单问题返回 ≥ 5 本不同来源。
- 综述模式返回 ≥ 15 本不同来源。
- 每条引用可定位到书名和章节。

### MVP-2：信号图谱搜索

数据规模：

- 1000 条信号样本。
- 每条切分为固定窗口。

实现：

- 提取时域 / 频域特征。
- 建立 segment embedding。
- 构建 similarity edge。
- ANN 召回 Top 500。
- 对 Top 100 做 cross-correlation / DTW 精排。

验收指标：

- 相比全库卷积搜索，耗时下降 ≥ 70%。
- Top-10 命中率不低于 baseline。
- 每个结果能返回原始信号、时间范围、相似得分和匹配解释。

### MVP-3：Gradio Lab

实现：

- Book Graph-RAG 调参页面。
- Signal Graph Search 调参页面。
- 结果表格、匹配解释、导出报告。

验收指标：

- 非开发人员能通过 UI 调参。
- 能导出 Markdown / CSV 评估结果。

---

## 11. 技术风险

| 风险 | 说明 | 缓解 |
|---|---|---|
| 文档噪声 | OCR 或 Markdown 仍有乱码 | 建库前清洗、抽样评估 |
| 实体抽取错误 | LLM 或规则误抽实体 | 人工校正高频实体、保留置信度 |
| 1 万本索引过慢 | 单机一次性建库耗时长 | 增量索引、批处理、断点续跑 |
| 向量召回漂移 | embedding 对古籍或信号不稳定 | Hybrid 检索 + rerank |
| 20 本覆盖牺牲精度 | 多样性过强可能引入弱相关来源 | 分模式控制 target_books |
| 信号尺度不一致 | 采样率、窗口长度不同 | 重采样和多尺度索引 |
| 图谱膨胀 | similarity edge 过多 | 只保留 Top-N 相似边和高置信关系 |

---

## 12. Harness 开发流程建议

### Step 1：OpenSpec 规格化

为后续正式开发建立 change：

```powershell
openspec propose "add graph-rag core for book knowledge graph and signal graph search"
```

输出：

- proposal.md
- design.md
- tasks.md
- specs/

### Step 2：分模块开发

优先顺序：

1. `schema.py`
2. `book.markdown_loader`
3. `book.chapter_parser`
4. `book.hybrid_retriever`
5. `book.diversity_selector`
6. `signal.preprocess`
7. `signal.segmenter`
8. `signal.feature_extractors`
9. `signal.retriever`
10. `signal.matcher`
11. `gradio_lab`

### Step 3：多角色审查

建议审查角色：

- correctness-reviewer：检索逻辑是否正确。
- performance-reviewer：索引构建和查询是否可扩展。
- architecture-strategist：模块边界是否干净。
- testing-reviewer：是否有可重复 benchmark。

### Step 4：知识沉淀

将最终实践沉淀到：

```text
knowledge/patterns/graph_rag_core.md
knowledge/patterns/signal_graph_search.md
knowledge/decisions/book_graph_vs_signal_graph.md
```

---

## 13. 推荐下一步

短期：

1. 新建 `src/graph_rag/` 骨架。
2. 先实现书籍图谱 MVP。
3. 再实现信号图谱 MVP。
4. 用 Gradio Lab 做实验台。

中期：

1. 加入向量库。
2. 加入 reranker。
3. 加入图谱存储。
4. 加入 benchmark 和可视化。

长期：

1. 从工具升级为“多模态知识 / 信号图谱平台”。
2. 支持文本、图像、信号、特征图统一检索。
3. 将 Lumia ScriptorRAG 扩展为 Lumia Graph-RAG Studio。


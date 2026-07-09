<script setup>
import { NAlert, NCard, NCollapse, NCollapseItem, NCode, NGi, NGrid, NIcon, NTag, NTimeline, NTimelineItem } from "naive-ui"
import { Archive, Book, CloudDownload, CodeSlash, FolderOpen, Library, Move, Rocket, Settings } from "@vicons/ionicons5"

const ragSteps = [
  ["整理资料", "先用光棱 OCR 把 PDF / 扫描件转成 Markdown，或直接准备 md、txt、html、pdf、epub、docx。"],
  ["字炉排版", "将 OCR 草稿送入字炉，清理标题、空行、列表、噪声字符，得到更适合建库的文本。"],
  ["挂载知识源", "如资料位于本地目录、WebDAV 或 AList，可在知识源页面统一挂载并同步到本地缓存。"],
  ["选择建库入口", "可直接指定本地资料目录，也可从已挂载知识源发起建库。"],
  ["重建索引", "系统解析文档、切分片段、建立 BM25 索引，并记录来源、标题、章节和文档层级。"],
  ["提问检索", "每个问题尽量返回不少于 5 条不同文档来源，并按相关度排序，古籍原典优先。"],
  ["复制导出", "结果可一键复制，也可导出 Markdown、HTML 或 PNG 长图，方便沉淀和分享。"],
]

const devModules = [
  ["后端入口", "src/web/app.py", "FastAPI API、SPA 托管、OCR / RAG / Provider / 挂载路由。"],
  ["知识源挂载", "src/kb_mounts/manager.py", "本地目录 / WebDAV / AList 挂载、本地缓存与同步逻辑。"],
  ["OCR 编排", "src/orchestrator/pipeline.py", "光棱 OCR 主流程、引擎回退、校正、质量评分。"],
  ["引擎封装", "src/engines/", "Surya、MinerU、Docling、Marker、PaddleOCR、Nougat 适配层。"],
  ["字炉排版", "src/formatter/markdown_cleaner.py", "Markdown 清洗、格式规范化、噪声处理。"],
  ["文枢 RAG", "src/rag/engine.py", "建库、BM25 检索、来源去重、原典加权、fallback answer。"],
  ["前端页面", "frontend/src/views/", "OCR、导览、排版、知识源、RAG、模型、帮助说明入口。"],
]
</script>

<template>
  <div class="help-page">
    <section class="hero-panel">
      <div class="hero-eyebrow">Help Center</div>
      <h1 class="hero-title">从本机使用，到换电脑迁移，再到二次开发。</h1>
      <p class="hero-subtitle">
        这里是 ZCLUM 光棱 OCR 的内置说明书：适合普通用户照着完成 OCR、排版、知识源挂载与 RAG 建库，也方便开发者理解项目结构并继续扩展智能体能力。
      </p>
    </section>

    <NAlert type="info" :bordered="false" class="card-shadow">
      当前本地目录名可以继续保持 <strong>C:\Users\35160\Documents\Codex\ocr-harness-v0.1.0</strong>，
      产品名称和发布名称统一为 <strong>ZCLUM 光棱 OCR｜ZCLUM Prism OCR</strong>。
    </NAlert>

    <NGrid :cols="3" :x-gap="16" :y-gap="16" responsive="screen">
      <NGi>
        <NCard class="card-shadow quick-help">
          <NIcon size="30"><Rocket /></NIcon>
          <h3>普通使用</h3>
          <p>启动服务，上传 PDF，等待光棱 OCR 输出 Markdown，再进入字炉排版和文枢 RAG。</p>
        </NCard>
      </NGi>
      <NGi>
        <NCard class="card-shadow quick-help">
          <NIcon size="30"><Move /></NIcon>
          <h3>换电脑迁移</h3>
          <p>复制源码、资料目录和本地数据目录，重新安装 Python / Node 依赖后启动即可。</p>
        </NCard>
      </NGi>
      <NGi>
        <NCard class="card-shadow quick-help">
          <NIcon size="30"><CodeSlash /></NIcon>
          <h3>继续开发</h3>
          <p>优先从 FastAPI、挂载管理器、OCR Pipeline、RAG Engine 和 Vue 页面五个入口理解项目。</p>
        </NCard>
      </NGi>
    </NGrid>

    <NCard class="card-shadow">
      <template #header>
        <div>
          <h2 class="section-title">一、日常使用流程</h2>
          <p class="muted" style="margin:0">适合第一次使用或给他人演示时照着走。</p>
        </div>
      </template>
      <NTimeline>
        <NTimelineItem type="success" title="启动本地服务">
          在项目目录双击 <NCode code="start.bat" />，或运行 <NCode code="py -3 -B -m uvicorn src.web.app:app --host 127.0.0.1 --port 8080" />。
        </NTimelineItem>
        <NTimelineItem type="info" title="进入光棱 OCR">
          打开 <NCode code="http://127.0.0.1:8080/" />，上传 PDF，选择智能路由或指定 OCR 引擎。
        </NTimelineItem>
        <NTimelineItem type="warning" title="进入字炉排版">
          OCR 完成后可以下载 Markdown，也可以一键送入字炉，清洗后再导出 MD / HTML。
        </NTimelineItem>
        <NTimelineItem type="info" title="挂载外部知识源">
          如资料分布在本地目录、WebDAV 或 AList 云盘，可进入 <NCode code="/sources" /> 挂载、同步并统一纳入知识库。
        </NTimelineItem>
        <NTimelineItem type="success" title="进入文枢 RAG">
          在文枢 RAG 页面填写资料目录，或直接从挂载知识源重建索引，然后提问并查看引用来源。
        </NTimelineItem>
        <NTimelineItem type="info" title="配置星轨模型">
          如需 LLM 校正或综合回答，在星轨模型页面添加 Provider；没有 Key 时系统仍可返回本地检索摘要。
        </NTimelineItem>
      </NTimeline>
    </NCard>

    <NCard class="card-shadow">
      <template #header>
        <div>
          <h2 class="section-title">二、换电脑后怎么继续用</h2>
          <p class="muted" style="margin:0">建议按“源码 / 资料 / 本地数据 / 依赖 / 启动”五步迁移。</p>
        </div>
      </template>
      <div class="migration-grid migration-grid-wide">
        <div class="migration-card">
          <NIcon><Archive /></NIcon>
          <strong>1. 复制项目源码</strong>
          <p>复制整个项目目录，或从 GitHub 私有仓库重新拉取。</p>
        </div>
        <div class="migration-card">
          <NIcon><Book /></NIcon>
          <strong>2. 复制原始资料</strong>
          <p>把 PDF、Markdown、txt、docx、epub 等资料目录一起复制；文枢 RAG 可重新建库。</p>
        </div>
        <div class="migration-card">
          <NIcon><Library /></NIcon>
          <strong>3. 复制本地数据</strong>
          <p>如需保留上传记录与索引，可复制 <NCode code="%LOCALAPPDATA%\\ZCLUM Prism OCR" />。</p>
        </div>
        <div class="migration-card">
          <NIcon><CloudDownload /></NIcon>
          <strong>4. 恢复挂载缓存</strong>
          <p>如使用知识源挂载，可复制 <NCode code="%LOCALAPPDATA%\\ZCLUM Prism OCR\\kb_mounts" />，或在新电脑重新挂载。</p>
        </div>
        <div class="migration-card">
          <NIcon><Settings /></NIcon>
          <strong>5. 重新安装依赖</strong>
          <p>安装 Python、Node.js，然后运行后端依赖和 <NCode code="cd frontend && npm install && npm run build" />。</p>
        </div>
      </div>

      <NCollapse style="margin-top:18px">
        <NCollapseItem title="推荐迁移清单" name="move-list">
          <ul class="help-list">
            <li>必须复制：项目源码、资料目录、需要处理的 PDF。</li>
            <li>建议复制：已经清洗好的 Markdown、RAG 语料目录。</li>
            <li>可选复制：<NCode code="%LOCALAPPDATA%\\ZCLUM Prism OCR\\rag_db" /> 与 <NCode code="%LOCALAPPDATA%\\ZCLUM Prism OCR\\kb_mounts" />。</li>
            <li>不要复制到仓库：API Key、模型大文件、上传临时文件、安装包、日志。</li>
            <li>Provider 的 API Key 当前主要保存在运行内存中，换电脑或重启后通常需要重新配置。</li>
          </ul>
        </NCollapseItem>
      </NCollapse>
    </NCard>

    <NCard class="card-shadow">
      <template #header>
        <div>
          <h2 class="section-title">三、知识源挂载怎么用</h2>
          <p class="muted" style="margin:0">把外部目录和云盘知识库接入当前产品，统一走“同步缓存 → 建库 → 检索”。</p>
        </div>
      </template>
      <div class="migration-grid mount-grid">
        <div class="migration-card">
          <NIcon><FolderOpen /></NIcon>
          <strong>本地目录</strong>
          <p>最适合已经完成 OCR 或排版的资料目录，速度最快，维护最简单。</p>
        </div>
        <div class="migration-card">
          <NIcon><CloudDownload /></NIcon>
          <strong>WebDAV / AList</strong>
          <p>适合远程云盘或 NAS，把外部知识库同步到本地缓存后再建立索引。</p>
        </div>
        <div class="migration-card">
          <NIcon><Library /></NIcon>
          <strong>挂载建库</strong>
          <p>在知识源页面选中多个源后一键建库，适合持续扩容和多资料池并行维护。</p>
        </div>
      </div>
      <NCollapse style="margin-top:18px">
        <NCollapseItem title="知识源推荐操作顺序" name="mount-roadmap">
          <ol class="help-list">
            <li>进入 <NCode code="http://127.0.0.1:8080/sources" />。</li>
            <li>新增一个知识源，优先选择本地目录，其次是 WebDAV 或 AList。</li>
            <li>完成配置后点击“同步”，让远程文件落到本地缓存。</li>
            <li>在知识源页或文枢 RAG 页点击“从挂载知识源建库”。</li>
            <li>回到文枢 RAG 页面提问，系统会基于同步后的缓存索引检索。</li>
          </ol>
        </NCollapseItem>
      </NCollapse>
    </NCard>

    <NCard class="card-shadow">
      <template #header>
        <div>
          <h2 class="section-title">四、文枢 RAG 是怎样工作的</h2>
          <p class="muted" style="margin:0">RAG 的重点不是“聊天”，而是“带出处的检索增强回答”。</p>
        </div>
      </template>
      <div class="rag-steps">
        <div v-for="(step, index) in ragSteps" :key="step[0]" class="rag-step">
          <span>{{ String(index + 1).padStart(2, "0") }}</span>
          <strong>{{ step[0] }}</strong>
          <p>{{ step[1] }}</p>
        </div>
      </div>
      <NAlert type="warning" :bordered="false" style="margin-top:18px">
        如果你觉得回答“知识宽度不够”，优先检查资料目录是否完整、是否已重建索引、引用数量是否大于等于 5、不同文档来源是否足够丰富。
      </NAlert>
    </NCard>

    <NCard class="card-shadow">
      <template #header>
        <div>
          <h2 class="section-title">五、二次开发入口</h2>
          <p class="muted" style="margin:0">如果要继续开发智能体、换检索算法或扩展工具，从这些文件开始。</p>
        </div>
      </template>
      <div class="dev-table">
        <div v-for="item in devModules" :key="item[1]" class="dev-row">
          <NTag :bordered="false" type="success">{{ item[0] }}</NTag>
          <NCode :code="item[1]" />
          <span>{{ item[2] }}</span>
        </div>
      </div>
      <NCollapse style="margin-top:18px">
        <NCollapseItem title="建议的开发路线" name="dev-roadmap">
          <ol class="help-list">
            <li>先阅读 <NCode code="docs/ai_handoff.md" />，了解当前状态和模块边界。</li>
            <li>再阅读 <NCode code="docs/knowledge_mounts.md" />，理解外部知识源挂载与缓存策略。</li>
            <li>扩展云盘协议时，优先在 <NCode code="src/kb_mounts/manager.py" /> 中新增 provider。</li>
            <li>升级 RAG 时，可在 <NCode code="src/rag/engine.py" /> 中加入 embedding、rerank 或向量数据库。</li>
            <li>修改前端后必须运行 <NCode code="npm run build" />，否则本地 FastAPI 页面不会更新。</li>
          </ol>
        </NCollapseItem>
      </NCollapse>
    </NCard>
  </div>
</template>

<style scoped>
.help-page {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.quick-help {
  min-height: 176px;
}

.quick-help :deep(.n-icon) {
  color: #0f766e;
}

.quick-help h3,
.migration-card strong,
.rag-step strong {
  display: block;
  margin: 10px 0 8px;
  font-size: 18px;
}

.quick-help p,
.migration-card p,
.rag-step p {
  margin: 0;
  color: #71807a;
  line-height: 1.75;
}

.migration-grid {
  display: grid;
  gap: 14px;
}

.migration-grid-wide {
  grid-template-columns: repeat(5, minmax(0, 1fr));
}

.mount-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.migration-card {
  padding: 16px;
  border-radius: 20px;
  background: #fbfaf6;
  border: 1px solid rgba(15, 118, 110, 0.12);
}

.migration-card :deep(.n-icon) {
  color: #b45309;
  font-size: 24px;
}

.rag-steps {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.rag-step {
  padding: 16px;
  border-radius: 20px;
  background: linear-gradient(180deg, rgba(15, 118, 110, 0.06), rgba(255, 255, 255, 0.72));
  border: 1px solid rgba(15, 118, 110, 0.12);
}

.rag-step span {
  color: #0f766e;
  font-weight: 800;
  letter-spacing: 0.12em;
}

.dev-table {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.dev-row {
  display: grid;
  grid-template-columns: 120px 280px minmax(0, 1fr);
  gap: 12px;
  align-items: center;
  padding: 12px;
  border-radius: 16px;
  background: #fbfaf6;
}

.help-list {
  margin: 0;
  padding-left: 20px;
  color: #52605b;
  line-height: 1.9;
}

@media (max-width: 980px) {
  .migration-grid-wide,
  .mount-grid,
  .rag-steps {
    grid-template-columns: 1fr;
  }

  .dev-row {
    grid-template-columns: 1fr;
  }
}
</style>

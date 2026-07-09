<script setup>
import { computed, onMounted, ref } from "vue"
import { marked } from "marked"
import {
  useMessage,
  NButton,
  NCard,
  NCheckbox,
  NCheckboxGroup,
  NInput,
  NInputNumber,
  NIcon,
  NSpace,
  NTag,
  NSwitch,
  NCollapse,
  NCollapseItem,
} from "naive-ui"
import { Library, Search, Copy, Download, Refresh, Image, CodeDownload } from "@vicons/ionicons5"
import api from "../api"

const message = useMessage()
const corpusDir = ref("C:\\Users\\35160\\Desktop\\中医RAG系统\\data\\books")
const question = ref("《黄帝内经》中如何理解脾胃？请尽量引用不同文档来源。")
const topK = ref(8)
const useLlm = ref(true)
const status = ref(null)
const mountedSources = ref([])
const mountedSelection = ref([])
const answer = ref("")
const references = ref([])
const rebuilding = ref(false)
const querying = ref(false)
const answerCardRef = ref(null)

const answerHtml = computed(() => (answer.value ? marked(answer.value, { breaks: true, gfm: true }) : ""))

async function loadStatus() {
  try {
    const { data } = await api.rag.status()
    status.value = data
  } catch (error) {
    message.error("无法连接 RAG 服务：" + (error.message || "未知错误"))
  }
}

async function loadMountedSources() {
  try {
    const { data } = await api.kbSources.list()
    mountedSources.value = data.sources || []
    if (!mountedSelection.value.length) {
      mountedSelection.value = mountedSources.value.filter((item) => item.enabled).map((item) => item.id)
    }
  } catch (error) {
    mountedSources.value = []
  }
}

async function rebuild() {
  if (!corpusDir.value.trim()) {
    message.warning("请填写资料目录")
    return
  }
  rebuilding.value = true
  try {
    const { data } = await api.rag.rebuild(corpusDir.value)
    status.value = data
    message.success(`建库完成：${data.chunks} 个片段，${data.documents} 个文档`)
  } catch (error) {
    message.error(error.response?.data?.detail || error.message || "建库失败")
  } finally {
    rebuilding.value = false
  }
}

async function rebuildMounted() {
  rebuilding.value = true
  try {
    const { data } = await api.rag.rebuildMounted(mountedSelection.value, true)
    status.value = data
    message.success(`挂载建库完成：${data.chunks} 个片段，${data.documents} 个文档`)
  } catch (error) {
    message.error(error.response?.data?.detail || error.message || "挂载建库失败")
  } finally {
    rebuilding.value = false
  }
}

async function query() {
  if (!question.value.trim()) {
    message.warning("请输入问题")
    return
  }
  querying.value = true
  try {
    const { data } = await api.rag.query(question.value, topK.value, useLlm.value)
    answer.value = data.answer || ""
    references.value = data.references || []
    status.value = data.stats || status.value
    message.success(`检索到 ${references.value.length} 条引用来源`)
  } catch (error) {
    message.error(error.response?.data?.detail || error.message || "检索失败")
  } finally {
    querying.value = false
  }
}

async function copyAnswer() {
  const refs = references.value
    .map((ref, index) => `${index + 1}. 《${ref.title}》${ref.chapter || ""}\n${ref.content}`)
    .join("\n\n")
  await navigator.clipboard.writeText(`${answer.value}\n\n## 引用来源\n\n${refs}`)
  message.success("已复制答案和引用")
}

function exportMarkdown() {
  const refs = references.value.map((ref, index) => `### ${index + 1}. 《${ref.title}》\n\n${ref.content}`).join("\n\n")
  const blob = new Blob([`# 文档 RAG 检索结果\n\n${answer.value}\n\n## 引用来源\n\n${refs}`], {
    type: "text/markdown;charset=utf-8",
  })
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = "scriptor-rag-result.md"
  a.click()
  URL.revokeObjectURL(url)
}

function buildExportHtml() {
  const refs = references.value
    .map(
      (ref, index) => `
    <section class="ref">
      <h3>${index + 1}. 《${escapeHtml(ref.title || "未知文档")}》</h3>
      <p class="meta">${escapeHtml(ref.chapter || ref.source || "")} · ${escapeHtml(ref.source_tier || "")} · score ${escapeHtml(String(ref.score ?? ""))}</p>
      <p>${escapeHtml(ref.content || "").replace(/\n/g, "<br>")}</p>
    </section>
  `,
    )
    .join("")
  return `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>文档 RAG 检索结果</title>
  <style>
    body{margin:0;background:#f4f0e8;color:#162320;font-family:"Noto Sans SC","PingFang SC","Microsoft YaHei",sans-serif;line-height:1.85}
    main{max-width:920px;margin:0 auto;padding:56px 24px}
    article,.ref{background:#fffdf8;border:1px solid #eee4d2;border-radius:24px;padding:30px;box-shadow:0 24px 80px rgba(31,41,55,.08)}
    h1,h2,h3{letter-spacing:-.03em;color:#11564f}.meta{color:#71807a;font-size:14px}.refs{display:grid;gap:16px;margin-top:18px}
  </style>
</head>
<body>
  <main>
    <article><h1>文档 RAG 检索结果</h1>${answerHtml.value}</article>
    <h2>引用来源</h2>
    <div class="refs">${refs}</div>
  </main>
</body>
</html>`
}

function exportHtml() {
  const blob = new Blob([buildExportHtml()], { type: "text/html;charset=utf-8" })
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = "scriptor-rag-result.html"
  a.click()
  URL.revokeObjectURL(url)
}

async function exportPng() {
  if (!answerCardRef.value || !answer.value) return
  const node = answerCardRef.value
  const width = node.offsetWidth
  const height = node.offsetHeight
  const clone = node.cloneNode(true)
  clone.setAttribute("xmlns", "http://www.w3.org/1999/xhtml")
  clone.style.width = `${width}px`
  clone.style.background = "#fffdf8"
  clone.style.padding = "24px"
  clone.style.boxSizing = "border-box"
  const serialized = new XMLSerializer().serializeToString(clone)
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height + 48}">
    <foreignObject width="100%" height="100%">${serialized}</foreignObject>
  </svg>`
  const img = new window.Image()
  const url = URL.createObjectURL(new Blob([svg], { type: "image/svg+xml;charset=utf-8" }))
  img.onload = () => {
    const canvas = document.createElement("canvas")
    canvas.width = width
    canvas.height = height + 48
    const ctx = canvas.getContext("2d")
    ctx.fillStyle = "#f4f0e8"
    ctx.fillRect(0, 0, canvas.width, canvas.height)
    ctx.drawImage(img, 0, 0)
    URL.revokeObjectURL(url)
    const a = document.createElement("a")
    a.href = canvas.toDataURL("image/png")
    a.download = "scriptor-rag-result.png"
    a.click()
  }
  img.onerror = () => {
    URL.revokeObjectURL(url)
    message.error("PNG 导出失败，可先使用 HTML / Markdown 导出")
  }
  img.src = url
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;")
}

onMounted(async () => {
  await loadStatus()
  await loadMountedSources()
})
</script>

<template>
  <div class="page-stack">
    <section class="hero-panel">
      <div class="hero-eyebrow">Local RAG</div>
      <h1 class="hero-title">把整理好的文档沉淀成可引用、可导出、可复核的本地知识库。</h1>
      <p class="hero-subtitle">
        支持多种文档格式建库。检索时尽量返回来自不同文档来源的引用片段，再把结果汇总为可复制答案。
      </p>
    </section>

    <NCard class="card-shadow">
      <template #header>
        <div>
          <h2 class="section-title">文档建库</h2>
          <p class="section-lead">推荐选择 OCR 与排版整理之后的资料目录，减少噪声进入索引。</p>
        </div>
      </template>
      <div class="rag-config">
        <NInput v-model:value="corpusDir" placeholder="资料目录，例如 C:\...\data\books" />
        <NButton type="primary" :loading="rebuilding" :disabled="!corpusDir.trim()" @click="rebuild">
          <template #icon><NIcon><Refresh /></NIcon></template>
          重建索引
        </NButton>
      </div>
      <NSpace class="rag-status">
        <NTag type="success">Chunks：{{ status?.chunks ?? 0 }}</NTag>
        <NTag type="info">Documents：{{ status?.documents ?? 0 }}</NTag>
        <NTag>{{ status?.db_path || "尚未加载索引" }}</NTag>
      </NSpace>
      <div class="mount-rebuild-panel">
        <div>
          <h3 class="mount-title">或使用已挂载知识源</h3>
          <p class="section-lead">选中的知识源会先同步缓存，再统一重建本地索引。</p>
        </div>
        <NCheckboxGroup v-model:value="mountedSelection">
          <NSpace wrap>
            <NCheckbox v-for="source in mountedSources" :key="source.id" :value="source.id" :label="source.name" />
          </NSpace>
        </NCheckboxGroup>
        <NSpace>
          <NButton secondary @click="loadMountedSources">刷新知识源</NButton>
          <NButton type="primary" :loading="rebuilding" :disabled="!mountedSources.length" @click="rebuildMounted">
            从挂载知识源建库
          </NButton>
        </NSpace>
      </div>
    </NCard>

    <div class="rag-grid">
      <NCard class="card-shadow">
        <template #header>
          <div>
            <h2 class="section-title">提问与检索</h2>
            <p class="section-lead">宽度优先拉取更多来源，再根据相关性和原典权重排序。</p>
          </div>
        </template>
        <NInput v-model:value="question" type="textarea" :autosize="{ minRows: 6, maxRows: 12 }" placeholder="输入你的问题..." />
        <div class="query-controls">
          <div>
            <span class="muted">引用数量</span>
            <NInputNumber v-model:value="topK" :min="5" :max="20" />
          </div>
          <div>
            <span class="muted">启用 LLM 综合</span>
            <NSwitch v-model:value="useLlm" />
          </div>
          <NButton type="primary" size="large" :loading="querying" :disabled="!question.trim()" @click="query">
            <template #icon><NIcon><Search /></NIcon></template>
            开始检索
          </NButton>
        </div>
      </NCard>

      <NCard class="card-shadow">
        <template #header>
          <div>
            <h2 class="section-title">回答结果</h2>
            <p class="section-lead">可复制结果，也可以导出 Markdown、HTML 或 PNG 截图。</p>
          </div>
        </template>
        <template #header-extra>
          <NSpace>
            <NButton size="small" :disabled="!answer" @click="copyAnswer">
              <template #icon><NIcon><Copy /></NIcon></template>
              复制
            </NButton>
            <NButton size="small" :disabled="!answer" @click="exportMarkdown">
              <template #icon><NIcon><Download /></NIcon></template>
              MD
            </NButton>
            <NButton size="small" :disabled="!answer" @click="exportHtml">
              <template #icon><NIcon><CodeDownload /></NIcon></template>
              HTML
            </NButton>
            <NButton size="small" :disabled="!answer" @click="exportPng">
              <template #icon><NIcon><Image /></NIcon></template>
              PNG
            </NButton>
          </NSpace>
        </template>
        <div v-if="answerHtml" ref="answerCardRef" class="markdown-preview answer-pane" v-html="answerHtml"></div>
        <div v-else class="answer-empty">
          <strong>等待检索结果</strong>
          <span>输入问题后点击“开始检索”，答案和引用会显示在这里。</span>
        </div>
      </NCard>
    </div>

    <NCard v-if="references.length" class="card-shadow">
      <template #header>
        <div>
          <h2 class="section-title">引用来源</h2>
          <p class="section-lead">每条结果都保留文档来源与章节线索，便于复核。</p>
        </div>
      </template>
      <NCollapse accordion>
        <NCollapseItem
          v-for="(ref, index) in references"
          :key="index"
          :title="`${index + 1}. 《${ref.title}》 · ${ref.source_tier || 'source'} · score ${ref.score}`"
        >
          <p class="muted reference-meta">{{ ref.chapter || ref.source }}</p>
          <div class="ref-content">{{ ref.content }}</div>
        </NCollapseItem>
      </NCollapse>
    </NCard>
  </div>
</template>

<style scoped>
.rag-config {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 12px;
}

.rag-status {
  margin-top: 14px;
}

.mount-rebuild-panel {
  margin-top: 18px;
  padding-top: 18px;
  border-top: 1px solid rgba(22, 114, 103, 0.1);
  display: grid;
  gap: 12px;
}

.mount-title {
  margin: 0 0 6px;
  font-size: 16px;
  color: var(--text-strong);
}

.rag-grid {
  display: grid;
  grid-template-columns: minmax(0, 0.9fr) minmax(0, 1.1fr);
  gap: 18px;
}

.query-controls {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 14px;
  margin-top: 16px;
  flex-wrap: wrap;
}

.query-controls > div {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.answer-pane,
.answer-empty {
  min-height: 310px;
}

.answer-empty {
  gap: 6px;
  text-align: center;
}

.answer-empty span {
  color: var(--text-muted);
}

.reference-meta {
  margin-top: 0;
}

.ref-content {
  white-space: pre-wrap;
  line-height: 1.8;
  padding: 14px;
  border-radius: 14px;
  background: var(--bg-panel-soft);
}

@media (max-width: 980px) {
  .rag-grid,
  .rag-config {
    grid-template-columns: 1fr;
  }
}
</style>

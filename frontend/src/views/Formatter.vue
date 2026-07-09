<script setup>
import { computed, onMounted, ref } from "vue"
import { marked } from "marked"
import {
  useMessage,
  NAlert,
  NButton,
  NCard,
  NCheckbox,
  NCheckboxGroup,
  NDivider,
  NEmpty,
  NGrid,
  NGridItem,
  NIcon,
  NInput,
  NRadioButton,
  NRadioGroup,
  NSpace,
  NStatistic,
  NTag,
} from "naive-ui"
import {
  Sparkles,
  Copy,
  Download,
  CodeDownload,
  Trash,
  StatsChart,
  Eye,
  DocumentText,
  Layers,
} from "@vicons/ionicons5"
import api from "../api"

const message = useMessage()
const source = ref("")
const cleaned = ref("")
const loading = ref(false)
const filename = ref("formatted-document.md")
const previewMode = ref("result")
const preset = ref("balanced")
const stats = ref(null)

const optionLabels = {
  fix_headings: "标题补空格",
  fix_lists: "列表补空格",
  merge_paragraphs: "段落合并",
  remove_noise: "去噪符号",
  normalize_punctuation: "标点整理",
  preserve_tables: "保留表格",
}

const presetOptions = {
  balanced: ["fix_headings", "fix_lists", "merge_paragraphs", "remove_noise", "normalize_punctuation", "preserve_tables"],
  gentle: ["fix_headings", "fix_lists", "preserve_tables"],
  ocr: ["fix_headings", "fix_lists", "merge_paragraphs", "remove_noise", "normalize_punctuation", "preserve_tables"],
  publish: ["fix_headings", "fix_lists", "merge_paragraphs", "remove_noise", "normalize_punctuation", "preserve_tables"],
}

const selectedOptions = ref([...presetOptions.balanced])

const presetCards = [
  { key: "balanced", title: "均衡整理", desc: "适合大多数 OCR 草稿，兼顾安全与可读性。" },
  { key: "gentle", title: "轻修校对", desc: "只做基础结构整理，方便人工二次校对。" },
  { key: "ocr", title: "OCR 强清理", desc: "更积极地合并断行、移除噪声符号。" },
  { key: "publish", title: "建库发布", desc: "适合进入 RAG 或导出 HTML 前的最终清洁。" },
]

const previewHtml = computed(() => (cleaned.value ? marked(cleaned.value, { breaks: true, gfm: true }) : ""))
const sourceHtml = computed(() => (source.value ? marked(source.value, { breaks: true, gfm: true }) : ""))
const selectedSummary = computed(() => selectedOptions.value.map((key) => optionLabels[key]).join(" · "))
const sourceMetrics = computed(() => analyzeText(source.value))
const resultMetrics = computed(() => analyzeText(cleaned.value))
const diffMetrics = computed(() => {
  if (!stats.value) return []
  return [
    { label: "合并段落", value: stats.value.paragraphs_merged || 0 },
    { label: "去噪次数", value: stats.value.noise_removed || 0 },
    { label: "删符号行", value: stats.value.symbol_only_lines_removed || 0 },
    { label: "修标题", value: stats.value.heading_fixed || 0 },
    { label: "修列表", value: stats.value.list_fixed || 0 },
    { label: "修标点", value: stats.value.punctuation_fixed || 0 },
  ]
})

function analyzeText(text) {
  const lines = text ? text.split("\n") : []
  const paragraphs = lines.filter((line) => line.trim()).length
  return {
    chars: text.length,
    lines: lines.length,
    paragraphs,
  }
}

function syncPreset(nextPreset) {
  preset.value = nextPreset
  selectedOptions.value = [...presetOptions[nextPreset]]
}

function buildPayload() {
  return {
    markdown: source.value,
    fix_headings: selectedOptions.value.includes("fix_headings"),
    fix_lists: selectedOptions.value.includes("fix_lists"),
    merge_paragraphs: selectedOptions.value.includes("merge_paragraphs"),
    remove_noise: selectedOptions.value.includes("remove_noise"),
    normalize_punctuation: selectedOptions.value.includes("normalize_punctuation"),
    preserve_tables: selectedOptions.value.includes("preserve_tables"),
  }
}

async function cleanMarkdown() {
  if (!source.value.trim()) {
    message.warning("请先粘贴需要整理的 Markdown 或 OCR 输出")
    return
  }
  loading.value = true
  try {
    const { data } = await api.format.markdown(buildPayload())
    cleaned.value = data.markdown || ""
    stats.value = data.stats || null
    previewMode.value = "result"
    message.success("字炉排版完成")
  } catch (error) {
    message.error(error.response?.data?.detail || error.message || "排版整理失败")
  } finally {
    loading.value = false
  }
}

async function copyResult() {
  if (!cleaned.value) return
  await navigator.clipboard.writeText(cleaned.value)
  message.success("已复制整理后的 Markdown")
}

function downloadResult() {
  if (!cleaned.value) return
  const blob = new Blob([cleaned.value], { type: "text/markdown;charset=utf-8" })
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = filename.value.replace(/\.[^.]+$/, "") + "_formatted.md"
  a.click()
  URL.revokeObjectURL(url)
}

function exportHtml() {
  if (!cleaned.value) return
  const safeTitle = filename.value.replace(/</g, "&lt;")
  const html = `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>${safeTitle}</title>
  <style>
    :root{color-scheme:light}
    body{margin:0;background:#f4f0e8;color:#162320;font-family:"Noto Sans SC","PingFang SC","Microsoft YaHei",sans-serif;line-height:1.92}
    main{max-width:920px;margin:0 auto;padding:48px 20px}
    article{background:#fffdf8;border:1px solid rgba(22,114,103,.12);border-radius:28px;padding:36px;box-shadow:0 24px 80px rgba(31,41,55,.08)}
    h1,h2,h3{letter-spacing:-.03em;color:#11564f}
    blockquote{margin:1.2em 0;padding:1em 1.2em;border-left:4px solid #1f8a7d;background:#eef8f4;border-radius:16px}
    table{border-collapse:collapse;width:100%;margin:1em 0}td,th{border:1px solid #e2d8c9;padding:8px 12px}
    pre{background:#17211f;color:#f8fafc;padding:16px;border-radius:14px;overflow:auto}
  </style>
</head>
<body><main><article>${previewHtml.value}</article></main></body>
</html>`
  const blob = new Blob([html], { type: "text/html;charset=utf-8" })
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = filename.value.replace(/\.[^.]+$/, "") + "_formatted.html"
  a.click()
  URL.revokeObjectURL(url)
}

function clearAll() {
  source.value = ""
  cleaned.value = ""
  stats.value = null
  filename.value = "formatted-document.md"
}

onMounted(() => {
  const pending = localStorage.getItem("scriptor_rag_formatter_source")
  const pendingName = localStorage.getItem("scriptor_rag_formatter_filename")
  if (pending) {
    source.value = pending
    filename.value = pendingName || filename.value
    localStorage.removeItem("scriptor_rag_formatter_source")
    localStorage.removeItem("scriptor_rag_formatter_filename")
    message.info("已接收 OCR 结果，可直接继续排版整理")
  }
})
</script>

<template>
  <div class="page-stack">
    <section class="hero-panel">
      <div class="hero-eyebrow">Formatter Workbench</div>
      <h1 class="hero-title">字炉排版：把 OCR 草稿整理成可阅读、可建库、可发布的 Markdown。</h1>
      <p class="hero-subtitle">
        这里既能独立处理 Markdown，也能承接 OCR 输出继续清理。重点解决断行、噪声符号、标题列表结构、中文标点与导出可用性。
      </p>
      <div class="feature-grid formatter-hero-grid">
        <div class="feature-tile">
          <strong>独立可用</strong>
          <p>用户只做排版时，也能直接在这里完成清理、对照、复制与导出。</p>
        </div>
        <div class="feature-tile">
          <strong>适配 OCR 文稿</strong>
          <p>保留表格和代码块，优先修正常见 OCR 断句、符号噪声与结构杂乱。</p>
        </div>
        <div class="feature-tile">
          <strong>面向 RAG</strong>
          <p>整理后的文本更适合进入知识库索引，也更便于后续人工复核。</p>
        </div>
      </div>
    </section>

    <NGrid :cols="24" :x-gap="18" :y-gap="18" responsive="screen">
      <NGridItem :span="24" :l-span="8">
        <NCard class="card-shadow">
          <template #header>
            <div>
              <h2 class="section-title">整理策略</h2>
              <p class="section-lead">先选预设，再按文稿情况微调细项。</p>
            </div>
          </template>

          <div class="preset-grid">
            <button
              v-for="item in presetCards"
              :key="item.key"
              type="button"
              class="preset-card"
              :class="{ active: preset === item.key }"
              @click="syncPreset(item.key)"
            >
              <strong>{{ item.title }}</strong>
              <span>{{ item.desc }}</span>
            </button>
          </div>

          <NDivider />

          <div class="tool-block">
            <span class="field-label">当前预设</span>
            <NRadioGroup :value="preset" @update:value="syncPreset">
              <NSpace wrap>
                <NRadioButton value="balanced">均衡</NRadioButton>
                <NRadioButton value="gentle">轻修</NRadioButton>
                <NRadioButton value="ocr">OCR 强清理</NRadioButton>
                <NRadioButton value="publish">建库发布</NRadioButton>
              </NSpace>
            </NRadioGroup>
          </div>

          <div class="tool-block">
            <span class="field-label">细项开关</span>
            <NCheckboxGroup v-model:value="selectedOptions">
              <div class="option-grid">
                <NCheckbox value="fix_headings" label="标题补空格" />
                <NCheckbox value="fix_lists" label="列表补空格" />
                <NCheckbox value="merge_paragraphs" label="段落合并" />
                <NCheckbox value="remove_noise" label="去噪符号" />
                <NCheckbox value="normalize_punctuation" label="标点整理" />
                <NCheckbox value="preserve_tables" label="保留表格" />
              </div>
            </NCheckboxGroup>
          </div>

          <NAlert type="info" class="formatter-alert">
            当前启用：{{ selectedSummary || "未启用任何整理项" }}
          </NAlert>

          <NSpace class="formatter-side-actions" vertical>
            <NButton type="primary" block :loading="loading" :disabled="!source.trim()" @click="cleanMarkdown">
              <template #icon><NIcon><Sparkles /></NIcon></template>
              开始排版
            </NButton>
            <NButton secondary block :disabled="!source && !cleaned" @click="clearAll">
              <template #icon><NIcon><Trash /></NIcon></template>
              清空工作台
            </NButton>
          </NSpace>
        </NCard>

        <NCard class="card-shadow">
          <template #header>
            <div>
              <h2 class="section-title">整理统计</h2>
              <p class="section-lead">帮助判断这次排版到底改了什么。</p>
            </div>
          </template>

          <div class="stats-grid">
            <div class="stat-chip">
              <span>原文字符</span>
              <strong>{{ sourceMetrics.chars }}</strong>
            </div>
            <div class="stat-chip">
              <span>结果字符</span>
              <strong>{{ resultMetrics.chars }}</strong>
            </div>
            <div class="stat-chip">
              <span>原文行数</span>
              <strong>{{ sourceMetrics.lines }}</strong>
            </div>
            <div class="stat-chip">
              <span>结果行数</span>
              <strong>{{ resultMetrics.lines }}</strong>
            </div>
          </div>

          <div v-if="stats" class="diff-grid">
            <div v-for="item in diffMetrics" :key="item.label" class="diff-chip">
              <span>{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
            </div>
          </div>
          <NEmpty v-else description="整理完成后这里会展示统计摘要" />
        </NCard>
      </NGridItem>

      <NGridItem :span="24" :l-span="16">
        <NCard class="card-shadow">
          <template #header>
            <div>
              <h2 class="section-title">原文输入</h2>
              <p class="section-lead">粘贴 OCR 结果、旧版 Markdown 或待修正文稿。</p>
            </div>
          </template>
          <template #header-extra>
            <NTag type="success">{{ sourceMetrics.chars }} 字符</NTag>
          </template>

          <NInput
            v-model:value="filename"
            class="filename-input"
            placeholder="文稿文件名，例如 黄帝内经-clean.md"
          />
          <NInput
            v-model:value="source"
            type="textarea"
            placeholder="把 OCR 输出或 Markdown 文稿粘贴到这里..."
            :autosize="{ minRows: 16, maxRows: 28 }"
          />
        </NCard>

        <NCard class="card-shadow">
          <template #header>
            <div>
              <h2 class="section-title">结果与对照</h2>
              <p class="section-lead">支持结果预览、原文对照、复制和导出。</p>
            </div>
          </template>
          <template #header-extra>
            <NSpace>
              <NButton size="small" :type="previewMode === 'result' ? 'primary' : 'default'" @click="previewMode = 'result'">
                <template #icon><NIcon><Eye /></NIcon></template>
                结果
              </NButton>
              <NButton size="small" :type="previewMode === 'compare' ? 'primary' : 'default'" @click="previewMode = 'compare'">
                <template #icon><NIcon><Layers /></NIcon></template>
                对照
              </NButton>
              <NButton size="small" :disabled="!cleaned" @click="copyResult">
                <template #icon><NIcon><Copy /></NIcon></template>
                复制
              </NButton>
              <NButton size="small" :disabled="!cleaned" @click="downloadResult">
                <template #icon><NIcon><Download /></NIcon></template>
                MD
              </NButton>
              <NButton size="small" :disabled="!cleaned" @click="exportHtml">
                <template #icon><NIcon><CodeDownload /></NIcon></template>
                HTML
              </NButton>
            </NSpace>
          </template>

          <div v-if="previewMode === 'result'">
            <div v-if="previewHtml" class="markdown-preview formatter-preview" v-html="previewHtml"></div>
            <div v-else class="empty-pane formatter-empty">
              <strong>等待整理结果</strong>
              <span>左侧粘贴文稿并点击“开始排版”，这里会显示整理后的可读预览。</span>
            </div>
          </div>

          <div v-else class="compare-grid">
            <div class="compare-pane">
              <div class="compare-head">
                <NIcon><DocumentText /></NIcon>
                <strong>原文</strong>
              </div>
              <div v-if="sourceHtml" class="markdown-preview formatter-preview" v-html="sourceHtml"></div>
              <div v-else class="empty-pane formatter-empty">
                <strong>暂无原文</strong>
              </div>
            </div>
            <div class="compare-pane">
              <div class="compare-head">
                <NIcon><StatsChart /></NIcon>
                <strong>整理后</strong>
              </div>
              <div v-if="previewHtml" class="markdown-preview formatter-preview" v-html="previewHtml"></div>
              <div v-else class="empty-pane formatter-empty">
                <strong>暂无结果</strong>
              </div>
            </div>
          </div>
        </NCard>
      </NGridItem>
    </NGrid>
  </div>
</template>

<style scoped>
.formatter-hero-grid {
  margin-top: 22px;
}

.preset-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.preset-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 16px;
  border: 1px solid rgba(22, 114, 103, 0.12);
  border-radius: 18px;
  background: rgba(255, 253, 248, 0.9);
  color: var(--text-body);
  text-align: left;
  cursor: pointer;
}

.preset-card:hover {
  transform: translateY(-1px);
  border-color: rgba(22, 114, 103, 0.24);
  box-shadow: 0 16px 32px rgba(27, 41, 39, 0.08);
}

.preset-card.active {
  color: var(--brand-700);
  background: var(--brand-050);
  border-color: rgba(22, 114, 103, 0.28);
  box-shadow: inset 0 0 0 1px rgba(22, 114, 103, 0.1);
}

.preset-card strong {
  font-size: 15px;
}

.preset-card span {
  color: var(--text-muted);
  line-height: 1.7;
  font-size: 13px;
}

.tool-block + .tool-block {
  margin-top: 18px;
}

.option-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px 14px;
}

.formatter-alert {
  margin-top: 18px;
}

.formatter-side-actions {
  margin-top: 18px;
}

.stats-grid,
.diff-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.diff-grid {
  margin-top: 14px;
}

.stat-chip,
.diff-chip {
  padding: 14px 16px;
  border-radius: 16px;
  background: var(--bg-panel-soft);
  border: 1px solid rgba(22, 114, 103, 0.1);
}

.stat-chip span,
.diff-chip span {
  display: block;
  color: var(--text-muted);
  font-size: 12px;
}

.stat-chip strong,
.diff-chip strong {
  display: block;
  margin-top: 8px;
  font-size: 24px;
  letter-spacing: -0.04em;
}

.filename-input {
  margin-bottom: 12px;
}

.formatter-preview,
.formatter-empty {
  min-height: 420px;
  max-height: 720px;
  overflow: auto;
}

.formatter-empty {
  gap: 6px;
  text-align: center;
}

.formatter-empty span {
  color: var(--text-muted);
}

.compare-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.compare-pane {
  min-width: 0;
}

.compare-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  color: var(--brand-700);
}

@media (max-width: 980px) {
  .preset-grid,
  .option-grid,
  .stats-grid,
  .diff-grid,
  .compare-grid {
    grid-template-columns: 1fr;
  }
}
</style>

<script setup>
import { ref, onMounted, onUnmounted } from "vue"
import { useRoute, useRouter } from "vue-router"
import api from "../api"
import { marked } from "marked"
import {
  useMessage,
  NButton,
  NCard,
  NSpace,
  NTag,
  NProgress,
  NIcon,
  NSkeleton,
  NText,
  NAlert,
  NEmpty,
} from "naive-ui"
import {
  CheckmarkCircle,
  CloseCircle,
  Download,
  Time,
  Copy,
  Sparkles,
  RefreshCircle,
} from "@vicons/ionicons5"

const route = useRoute()
const router = useRouter()
const message = useMessage()
const taskId = route.params.id
const task = ref(null)
const error = ref("")
const polling = ref(true)
const markdownHtml = ref("")

async function poll() {
  if (taskId === "demo") {
    router.replace("/")
    return
  }
  while (polling.value) {
    try {
      const { data } = await api.status(taskId)
      task.value = data
      if (data.status === "completed") {
        polling.value = false
        const result = await api.result(taskId)
        task.value = { ...task.value, ...result.data }
        markdownHtml.value = task.value.markdown ? marked(task.value.markdown, { breaks: true, gfm: true }) : ""
      } else if (data.status === "failed") {
        polling.value = false
      }
    } catch (err) {
      error.value = err.response?.data?.detail || err.message
      polling.value = false
    }
    if (polling.value) await new Promise((resolve) => setTimeout(resolve, 2000))
  }
}

function download() {
  window.open(api.download(taskId), "_blank")
}

async function copyMarkdown() {
  await navigator.clipboard.writeText(task.value?.markdown || "")
  message.success("Markdown 已复制")
}

function goFormat() {
  if (task.value?.markdown) {
    localStorage.setItem("scriptor_rag_formatter_source", task.value.markdown)
    localStorage.setItem("scriptor_rag_formatter_filename", task.value.filename || "scriptor-rag-result.md")
  }
  router.push("/format")
}

function formatPercent(value) {
  return `${((value || 0) * 100).toFixed(0)}/100`
}

onMounted(poll)
onUnmounted(() => {
  polling.value = false
})
</script>

<template>
  <div class="result-page">
    <div v-if="!task && !error" class="result-loading">
      <NSkeleton height="38px" width="260px" />
      <NSkeleton height="18px" width="360px" />
      <NSkeleton height="260px" />
    </div>

    <NAlert v-else-if="error" type="error" title="无法读取任务状态">
      {{ error }}
    </NAlert>

    <NCard v-else-if="['queued', 'analyzing', 'converting'].includes(task.status)" class="card-shadow progress-card">
      <NIcon size="52" color="var(--brand-600)" class="result-status-icon"><Time /></NIcon>
      <h2 class="result-status-title">
        {{
          task.status === "analyzing"
            ? "正在分析文档结构..."
            : task.status === "converting"
              ? "OCR 正在提取文本..."
              : "任务已排队，等待处理..."
        }}
      </h2>
      <p class="section-lead result-status-copy">请保持当前页面打开，系统会自动轮询状态并在完成后展示结果。</p>
      <NProgress :percentage="task.progress || 20" :height="9" processing class="result-progress" />
      <NText depth="3">{{ task.status }} · {{ task.progress || 20 }}%</NText>
    </NCard>

    <NCard v-else-if="task.status === 'failed'" class="card-shadow progress-card">
      <NIcon size="52" color="var(--danger-600)" class="result-status-icon"><CloseCircle /></NIcon>
      <h2 class="result-failed-title">转换失败</h2>
      <NAlert type="error" :bordered="false">{{ task.error || "未知错误" }}</NAlert>
      <NSpace justify="center" class="result-actions">
        <NButton type="primary" @click="router.push('/')">
          <template #icon><NIcon><RefreshCircle /></NIcon></template>
          返回重新上传
        </NButton>
      </NSpace>
    </NCard>

    <template v-else>
      <section class="hero-panel">
        <div class="hero-eyebrow">OCR Result</div>
        <h1 class="hero-title">转换完成，结果已整理为可继续处理的 Markdown。</h1>
        <p class="hero-subtitle">
          你可以直接下载 Markdown，或继续送入排版整理页面，把结构与可读性再向前推进一步。
        </p>
      </section>

      <NCard class="card-shadow">
        <div class="result-toolbar">
          <div class="result-title">
            <NIcon size="26" color="var(--success-600)"><CheckmarkCircle /></NIcon>
            <strong>{{ task.filename || "OCR 结果" }}</strong>
          </div>
          <NSpace>
            <NTag :type="task.quality_score >= 0.85 ? 'success' : 'warning'">
              质量 {{ formatPercent(task.quality_score) }}
            </NTag>
            <NTag>{{ task.engine_used || "unknown" }}</NTag>
            <NTag>{{ task.processing_time?.toFixed?.(1) || "-" }}s</NTag>
            <NButton size="small" :disabled="!task.markdown" @click="copyMarkdown">
              <template #icon><NIcon><Copy /></NIcon></template>
              复制
            </NButton>
            <NButton size="small" :disabled="!task.markdown" @click="goFormat">
              <template #icon><NIcon><Sparkles /></NIcon></template>
              继续排版
            </NButton>
            <NButton type="primary" size="small" :disabled="!task.markdown" @click="download">
              <template #icon><NIcon><Download /></NIcon></template>
              下载 MD
            </NButton>
          </NSpace>
        </div>
      </NCard>

      <NCard v-if="task.analysis" class="card-shadow">
        <template #header>
          <div>
            <h2 class="section-title">文档分析摘要</h2>
            <p class="section-lead">用于理解本次路由与识别策略。</p>
          </div>
        </template>
        <div class="analysis-grid">
          <span>文档类型：<strong>{{ task.analysis.doc_type }}</strong></span>
          <span>页数：<strong>{{ task.analysis.page_count }}</strong></span>
          <span>语言：<strong>{{ task.analysis.language_hint === "zh" ? "中文" : "英文 / 混合" }}</strong></span>
          <span>扫描件：<strong>{{ task.analysis.is_scanned ? "是" : "否" }}</strong></span>
        </div>
      </NCard>

      <NCard class="card-shadow">
        <template #header>
          <div>
            <h2 class="section-title">Markdown 预览</h2>
            <p class="section-lead">用于快速检查提取结果、段落结构和表格可读性。</p>
          </div>
        </template>
        <template #header-extra>
          <NText depth="3" class="result-char-count">{{ task.markdown?.length || 0 }} 字符</NText>
        </template>
        <div v-if="markdownHtml" class="markdown-preview" v-html="markdownHtml"></div>
        <NEmpty v-else description="当前结果暂无可预览内容" />
      </NCard>
    </template>
  </div>
</template>

<style scoped>
.result-page {
  max-width: 1080px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.result-loading {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 40px 0;
}

.result-status-icon {
  margin-bottom: 12px;
}

.result-status-title {
  margin: 0 0 8px;
}

.result-status-copy {
  max-width: 460px;
  margin: 0 auto;
}

.result-progress {
  max-width: 460px;
  margin: 18px auto;
}

.result-failed-title {
  margin: 0 0 12px;
  color: var(--danger-600);
}

.result-actions {
  margin-top: 18px;
}

.result-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 14px;
}

.result-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 18px;
}

.analysis-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  color: var(--text-muted);
  line-height: 1.7;
}

.result-char-count {
  font-size: 12px;
}

@media (max-width: 860px) {
  .analysis-grid {
    grid-template-columns: 1fr 1fr;
  }
}
</style>

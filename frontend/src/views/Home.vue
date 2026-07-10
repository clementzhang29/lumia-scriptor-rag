<script setup>
import { computed, ref } from "vue"
import { useRouter } from "vue-router"
import { useAppStore } from "../stores/app"
import api from "../api"
import {
  useMessage,
  NButton,
  NCard,
  NSelect,
  NRadioGroup,
  NRadio,
  NSpace,
  NProgress,
  NIcon,
  NTag,
  NText,
  NGrid,
  NGi,
} from "naive-ui"
import {
  CloudUpload,
  DocumentAttach,
  Flash,
  CheckmarkCircle,
  Analytics,
  Sparkles,
  Library,
  CheckmarkDoneCircle,
} from "@vicons/ionicons5"

const router = useRouter()
const store = useAppStore()
const message = useMessage()

const fileInput = ref(null)
const folderInput = ref(null)
const files = ref([])
const uploading = ref(false)
const uploadProgress = ref(0)
const strategy = ref("auto")
const preferredEngine = ref("")

const availableCount = computed(() => store.engines.filter((engine) => engine.available).length)
const providerCount = computed(() => store.providers.length)
const recommendedEngine = computed(() => store.engines.find((engine) => engine.available)?.name || "等待检测")
const engineOptions = computed(() => [
  { label: "自动选择最优引擎", value: "" },
  ...store.engines.map((engine) => ({
    label: `${engine.name}${engine.available ? "" : "（当前不可用）"}`,
    value: engine.name,
    disabled: !engine.available,
  })),
])

const selectedCount = computed(() => files.value.length)
const firstFile = computed(() => files.value[0] || null)
const batchMode = computed(() => files.value.length > 1)

function normalizeFiles(selected) {
  const list = Array.from(selected || []).filter((item) => item && item.name)
  files.value = list
}

function openFilePicker() {
  fileInput.value?.click()
}

function openFolderPicker() {
  folderInput.value?.click()
}

function handleInputChange(event) {
  normalizeFiles(event.target.files)
}

function clearSelection() {
  files.value = []
  if (fileInput.value) fileInput.value.value = ""
  if (folderInput.value) folderInput.value.value = ""
}

async function submit() {
  if (uploading.value) return
  if (!files.value.length) {
    message.error("请先选择一个或多个 PDF 文件")
    return
  }

  uploading.value = true
  uploadProgress.value = 0

  try {
    const uploadFn = batchMode.value ? api.convertBatch : api.convert
    const payload = batchMode.value ? files.value : files.value[0]
    const { data } = await uploadFn(payload, strategy.value, preferredEngine.value, (progress) => {
      uploadProgress.value = progress
    })

    if (data.batch_id) {
      message.success(`批量任务已创建，共 ${data.count} 个文件`)
      router.push(`/result/${data.task_ids?.[0] || data.batch_id}`)
      return
    }

    message.success("任务已加入 OCR 队列")
    router.push(`/result/${data.task_id}`)
  } catch (error) {
    message.error(error.response?.data?.detail || error.message || "上传失败")
  } finally {
    uploading.value = false
  }
}
</script>

<template>
  <div class="page-stack">
    <section class="hero-panel">
      <div class="hero-eyebrow">OCR / Formatter / RAG</div>
      <h1 class="hero-title">先识文，再成章，最终进入可追溯的本地知识库。</h1>
      <p class="hero-subtitle">
        ZCLUM 光棱 OCR 面向真实 PDF 提取场景：自动分析文档特征，路由到合适的 OCR 引擎，输出可读 Markdown，
        并继续进入排版清洗与文档 RAG 检索流程。
      </p>
      <div class="feature-grid hero-features">
        <div class="feature-tile">
          <strong>01 · 智能引擎路由</strong>
          <p>根据扫描属性、语言与版式选择 Surya、MinerU、Docling、Marker 或 PaddleOCR。</p>
        </div>
        <div class="feature-tile">
          <strong>02 · 结构化排版整理</strong>
          <p>把 OCR 草稿清理成更稳定的 Markdown，减少标题、空行、列表和表格噪声。</p>
        </div>
        <div class="feature-tile">
          <strong>03 · 本地文档检索增强</strong>
          <p>把整理后的文本沉淀到知识库，支持引用来源、导出结果和复核原文片段。</p>
        </div>
      </div>
    </section>

    <NGrid :cols="3" :x-gap="16" :y-gap="16" responsive="screen" class="status-grid">
      <NGi>
        <NCard class="card-shadow status-card">
          <template #header><span class="section-title">引擎可用性</span></template>
          <div class="stat-number text-brand">{{ availableCount }}/{{ store.engines.length || 0 }}</div>
          <p class="section-lead">当前已检测到可用的 OCR 引擎数量。</p>
          <div class="surface-note">推荐优先使用：{{ recommendedEngine }}</div>
        </NCard>
      </NGi>
      <NGi>
        <NCard class="card-shadow status-card">
          <template #header><span class="section-title">质量阈值</span></template>
          <div class="stat-number text-accent">0.85</div>
          <p class="section-lead">当结果评分偏低时，系统会尝试其他引擎补充识别。</p>
          <div class="surface-note">重点关注表格、公式和阅读顺序完整性。</div>
        </NCard>
      </NGi>
      <NGi>
        <NCard class="card-shadow status-card">
          <template #header><span class="section-title">模型 Provider</span></template>
          <div class="stat-number">{{ providerCount }}</div>
          <p class="section-lead">可用于校正 OCR 结果与增强 RAG 问答的外部模型数量。</p>
          <div class="surface-note">未配置也可继续使用本地 OCR 与本地检索。</div>
        </NCard>
      </NGi>
    </NGrid>

    <NCard class="card-shadow">
      <template #header>
        <div>
          <h2 class="section-title">OCR 工作台</h2>
          <p class="section-lead">支持单个文件、多个文件，以及整个文件夹批量提取。</p>
        </div>
      </template>

      <input ref="fileInput" class="hidden-input" type="file" accept="application/pdf" multiple @change="handleInputChange">
      <input
        ref="folderInput"
        class="hidden-input"
        type="file"
        accept="application/pdf"
        multiple
        webkitdirectory
        directory
        @change="handleInputChange"
      >

      <div class="upload-actions">
        <NButton secondary @click="openFilePicker">选择多个文件</NButton>
        <NButton secondary @click="openFolderPicker">选择文件夹</NButton>
        <NButton v-if="files.length" tertiary @click="clearSelection">清空</NButton>
      </div>

      <div class="upload-zone" :class="{ ready: !!firstFile }" role="button" tabindex="0" @click="openFilePicker">
        <NIcon size="56" color="var(--brand-600)"><CloudUpload /></NIcon>
        <NText v-if="!firstFile" depth="3">点击选择多个 PDF，或选择文件夹批量提取</NText>
        <div v-else class="selected-file">
          <NIcon size="24" color="var(--success-600)"><DocumentAttach /></NIcon>
          <strong>{{ firstFile.name }}</strong>
          <span class="muted">({{ selectedCount }} 个文件，首个 {{ (firstFile.size / 1024 / 1024).toFixed(1) }} MB)</span>
        </div>
        <NButton type="primary" ghost>{{ firstFile ? "重新选择" : "选择文件" }}</NButton>
      </div>

      <div class="home-control-grid">
        <div>
          <NText depth="2" class="field-label">转换策略</NText>
          <NRadioGroup v-model:value="strategy">
            <NSpace>
              <NRadio value="auto">智能路由</NRadio>
              <NRadio value="single">单引擎模式</NRadio>
            </NSpace>
          </NRadioGroup>
        </div>
        <div>
          <NText depth="2" class="field-label">首选引擎</NText>
          <NSelect v-model:value="preferredEngine" :options="engineOptions" placeholder="自动选择最优引擎" />
        </div>
        <div class="submit-area">
          <NButton
            type="primary"
            size="large"
            :disabled="!files.length || uploading"
            :loading="uploading"
            @click="submit"
          >
            <template #icon>
              <NIcon><Flash v-if="!uploading" /><CheckmarkCircle v-else /></NIcon>
            </template>
            {{ uploading ? `上传中 ${uploadProgress}%` : batchMode ? "开始批量 OCR" : "开始 OCR 转换" }}
          </NButton>
        </div>
      </div>

      <NProgress v-if="uploading" :percentage="uploadProgress" :height="8" processing class="mt-18" />
    </NCard>

    <NGrid :cols="3" :x-gap="16" :y-gap="16" responsive="screen">
      <NGi>
        <div class="quick-card is-note" aria-disabled="true">
          <NIcon><Analytics /></NIcon>
          <span>结果页会展示进度、质量评分、引擎记录与 Markdown 下载。</span>
        </div>
      </NGi>
      <NGi>
        <router-link to="/format" class="quick-card">
          <NIcon><Sparkles /></NIcon>
          <span>已有 Markdown 时，可进入排版整理并导出 HTML。</span>
        </router-link>
      </NGi>
      <NGi>
        <router-link to="/rag" class="quick-card">
          <NIcon><Library /></NIcon>
          <span>整理完成后可进入文枢 RAG，构建可追溯的本地知识库。</span>
        </router-link>
      </NGi>
    </NGrid>

    <NCard class="card-shadow">
      <template #header>
        <div>
          <h2 class="section-title">当前工作流</h2>
          <p class="section-lead">适合真实文档处理，不是演示型落地页。</p>
        </div>
      </template>
      <NSpace wrap>
        <NTag :bordered="false" type="success"><NIcon size="14"><CheckmarkDoneCircle /></NIcon>&nbsp;上传 PDF</NTag>
        <NTag :bordered="false" type="success"><NIcon size="14"><CheckmarkDoneCircle /></NIcon>&nbsp;自动分析文档</NTag>
        <NTag :bordered="false" type="success"><NIcon size="14"><CheckmarkDoneCircle /></NIcon>&nbsp;OCR 转 Markdown</NTag>
        <NTag :bordered="false" type="warning"><NIcon size="14"><CheckmarkDoneCircle /></NIcon>&nbsp;排版清洗</NTag>
        <NTag :bordered="false" type="info"><NIcon size="14"><CheckmarkDoneCircle /></NIcon>&nbsp;知识库检索与引用</NTag>
      </NSpace>
    </NCard>
  </div>
</template>

<style scoped>
.hero-features {
  margin-top: 24px;
}

.text-brand {
  color: var(--brand-700);
}

.text-accent {
  color: var(--accent-600);
}

.mt-18 {
  margin-top: 18px;
}

.home-control-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) auto;
  gap: 18px;
  align-items: end;
  margin-top: 22px;
}

.submit-area {
  display: flex;
  justify-content: flex-end;
}

.upload-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 16px;
}

.hidden-input {
  display: none;
}

.upload-zone {
  cursor: pointer;
}

@media (max-width: 860px) {
  .home-control-grid {
    grid-template-columns: 1fr;
  }

  .submit-area {
    justify-content: stretch;
  }
}
</style>

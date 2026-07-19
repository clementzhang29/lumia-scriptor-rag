<script setup>
import { computed, ref } from "vue"
import { useRouter } from "vue-router"
import { useAppStore } from "../stores/app"
import api from "../api"
import {
  useMessage,
  NButton,
  NCard,
  NUpload,
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

const file = ref(null)
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

function handleFileSelect(files) {
  if (files?.length) file.value = files[0]
}

async function submit() {
  if (uploading.value) return
  if (!file.value) {
    message.error("请先选择 PDF 文件")
    return
  }
  uploading.value = true
  try {
    const { data } = await api.convert(file.value, strategy.value, preferredEngine.value, (progress) => {
      uploadProgress.value = progress
    })
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
      <h1 class="hero-title">先识文，再成章，最后进入可追溯的本地知识库。</h1>
      <p class="hero-subtitle">
        Lumia ScriptorRAG 面向真实 PDF 提取场景：自动分析文档特征，路由到合适的 OCR 引擎，输出可读 Markdown，
        并继续进入排版清洗与文档 RAG 检索流程。
      </p>
      <div class="feature-grid hero-features">
        <div class="feature-tile">
          <strong>01 · 智能引擎路由</strong>
          <p>根据扫描属性、语言与版式选择 Surya、MinerU、Docling、Marker 或 PaddleOCR。</p>
        </div>
        <div class="feature-tile">
          <strong>02 · 结构化排版整理</strong>
          <p>把 OCR 草稿清成更稳定的 Markdown，减少标题、空行、列表与表格噪声。</p>
        </div>
        <div class="feature-tile">
          <strong>03 · 本地文档检索增强</strong>
          <p>将整理后的文本沉淀到知识库，支持引用来源、导出结果和复核原文片段。</p>
        </div>
      </div>
    </section>

    <NGrid :cols="3" :x-gap="16" :y-gap="16" responsive="screen" class="status-grid">
      <NGi>
        <NCard class="card-shadow status-card">
          <template #header><span class="section-title">引擎可用性</span></template>
          <div class="stat-number text-brand">{{ availableCount }}/{{ store.engines.length || 0 }}</div>
          <p class="section-lead">当前已检测可用的 OCR 引擎数量。</p>
          <div class="surface-note">推荐优先使用：{{ recommendedEngine }}</div>
        </NCard>
      </NGi>
      <NGi>
        <NCard class="card-shadow status-card">
          <template #header><span class="section-title">质量回退阈值</span></template>
          <div class="stat-number text-accent">0.85</div>
          <p class="section-lead">当结果评分偏低时，系统会尝试其他引擎补充识别。</p>
          <div class="surface-note">重点关注表格、公式和阅读顺序完整性。</div>
        </NCard>
      </NGi>
      <NGi>
        <NCard class="card-shadow status-card">
          <template #header><span class="section-title">模型 Provider</span></template>
          <div class="stat-number">{{ providerCount }}</div>
          <p class="section-lead">可用于校正 OCR 结果与增强 RAG 回答的外部模型数量。</p>
          <div class="surface-note">未配置也可继续使用本地 OCR 与本地检索。</div>
        </NCard>
      </NGi>
    </NGrid>

    <NCard class="card-shadow">
      <template #header>
        <div>
          <h2 class="section-title">OCR 工作台</h2>
          <p class="section-lead">上传 PDF，选择策略与引擎偏好，然后进入转换结果页。</p>
        </div>
      </template>

      <NUpload
        :multiple="false"
        accept="application/pdf"
        :custom-request="() => {}"
        :default-upload="false"
        @change="({ file: selected }) => handleFileSelect(selected.file ? [selected.file] : [])"
      >
        <div class="upload-zone" :class="{ ready: !!file }">
          <NIcon size="56" color="var(--brand-600)"><CloudUpload /></NIcon>
          <NText v-if="!file" depth="3">点击选择 PDF，或把文件拖到这里</NText>
          <div v-else class="selected-file">
            <NIcon size="24" color="var(--success-600)"><DocumentAttach /></NIcon>
            <strong>{{ file.name }}</strong>
            <span class="muted">({{ (file.size / 1024 / 1024).toFixed(1) }} MB)</span>
          </div>
          <NButton type="primary" ghost>{{ file ? "重新选择文件" : "选择文件" }}</NButton>
        </div>
      </NUpload>

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
            :disabled="!file || uploading"
            :loading="uploading"
            @click="submit"
          >
            <template #icon>
              <NIcon><Flash v-if="!uploading" /><CheckmarkCircle v-else /></NIcon>
            </template>
            {{ uploading ? `上传中 ${uploadProgress}%` : "启动 OCR 转换" }}
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
          <span>已有 Markdown？可直接进入排版整理并导出 HTML。</span>
        </router-link>
      </NGi>
      <NGi>
        <router-link to="/rag" class="quick-card">
          <NIcon><Library /></NIcon>
          <span>整理完成后进入文档 RAG，构建引用可追溯的本地知识库。</span>
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
        <NTag :bordered="false" type="info"><NIcon size="14"><CheckmarkDoneCircle /></NIcon>&nbsp;文档建库与检索</NTag>
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

@media (max-width: 860px) {
  .home-control-grid {
    grid-template-columns: 1fr;
  }

  .submit-area {
    justify-content: stretch;
  }
}
</style>

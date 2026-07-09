<script setup>
import { computed, onMounted, ref } from "vue"
import api from "../api"
import { useAppStore } from "../stores/app"
import {
  useMessage,
  useDialog,
  NAlert,
  NButton,
  NCard,
  NCollapse,
  NCollapseItem,
  NDataTable,
  NEmpty,
  NForm,
  NFormItem,
  NIcon,
  NInput,
  NModal,
  NSelect,
  NSpace,
  NSwitch,
  NTag,
} from "naive-ui"
import { Add, Eye, EyeOff, Refresh, Server, ShieldCheckmark, Trash } from "@vicons/ionicons5"

const store = useAppStore()
const message = useMessage()
const dialog = useDialog()

const providers = ref([])
const catalogs = ref({})
const showForm = ref(false)
const loading = ref(false)
const loadingCatalogs = ref([])
const showKey = ref(false)
const testResults = ref(null)

const form = ref({
  name: "",
  base_url: "",
  api_key: "",
  model: "",
  route_group: "default",
  visible_provider: false,
  preferred_for: ["ocr_correction", "rag_answer"],
})

const scenarioOptions = [
  { label: "OCR 校正", value: "ocr_correction" },
  { label: "RAG 问答", value: "rag_answer" },
  { label: "表格修复", value: "table_fix" },
  { label: "公式修复", value: "formula_fix" },
  { label: "顺序修复", value: "ordering_fix" },
]

const providerTemplates = [
  { label: "主力模型入口", base: "https://ai.example.com/v1", model: "gpt-5.5" },
  { label: "通用兼容入口", base: "https://api.example.com/v1", model: "gpt-4o-mini" },
  { label: "备用问答入口", base: "https://backup.example.com/v1", model: "deepseek-chat" },
]

const modelColumns = computed(() => [
  { title: "模型", key: "id", minWidth: 240 },
  { title: "计费", key: "price_type", width: 96, render: (row) => (row.price_type === 1 ? "固定价" : "倍率") },
  { title: "输入", key: "input_ratio", width: 92, render: (row) => row.input_ratio ?? "-" },
  { title: "输出", key: "output_ratio", width: 92, render: (row) => row.output_ratio ?? "-" },
  { title: "固定价", key: "fixed_price", width: 100, render: (row) => row.fixed_price ?? "-" },
  { title: "能力", key: "endpoints", minWidth: 140, render: (row) => (row.endpoints?.length ? row.endpoints.join(" / ") : "-") },
])

async function load() {
  const { data } = await api.providers.list()
  providers.value = data.providers || []
}

async function loadCatalog(name) {
  if (loadingCatalogs.value.includes(name)) return
  loadingCatalogs.value = [...loadingCatalogs.value, name]
  try {
    const { data } = await api.providers.catalog(name)
    catalogs.value = { ...catalogs.value, [name]: data }
  } catch (error) {
    catalogs.value = {
      ...catalogs.value,
      [name]: {
        models: [],
        error: error.response?.data?.detail || error.message || "模型目录读取失败",
      },
    }
  } finally {
    loadingCatalogs.value = loadingCatalogs.value.filter((item) => item !== name)
  }
}

function useTemplate(template) {
  form.value.base_url = template.base
  form.value.model = template.model
}

async function addProvider() {
  if (!form.value.name || !form.value.base_url || !form.value.api_key) {
    message.warning("请填写入口名称、API 地址和 API Key")
    return
  }
  loading.value = true
  try {
    await api.providers.register(form.value)
    message.success("模型入口已保存")
    form.value = {
      name: "",
      base_url: "",
      api_key: "",
      model: "",
      route_group: "default",
      visible_provider: false,
      preferred_for: ["ocr_correction", "rag_answer"],
    }
    showForm.value = false
    await load()
    await store.fetchProviders()
  } catch (error) {
    message.error(error.response?.data?.detail || error.message || "保存失败")
  } finally {
    loading.value = false
  }
}

function confirmRemove(name) {
  dialog.warning({
    title: "确认删除",
    content: `确定删除 ${name} 吗？`,
    positiveText: "删除",
    negativeText: "取消",
    onPositiveClick: async () => {
      await api.providers.delete(name)
      delete catalogs.value[name]
      message.success("已删除")
      await load()
      await store.fetchProviders()
    },
  })
}

async function verifyAll() {
  const { data } = await api.providers.verify()
  testResults.value = data.results || {}
  const ok = Object.values(testResults.value).filter(Boolean).length
  message.success(`检测完成：${ok}/${Object.keys(testResults.value).length} 个入口可用`)
}

function preferredText(provider) {
  return provider.preferred_for?.length ? provider.preferred_for.join(" / ") : "未指定"
}

function routeGroupText(provider) {
  return provider.route_group || "default"
}

onMounted(load)
</script>

<template>
  <div class="page-stack">
    <section class="hero-panel">
      <div class="hero-eyebrow">Model Hub</div>
      <h1 class="hero-title">模型中心：统一管理 OCR 校正与 RAG 问答入口</h1>
      <p class="hero-subtitle">
        页面默认隐藏供应商地址，只展示入口名称、模型、用途与价格目录。嵌入 zclum 后可由平台统一代理用户 Token 与额度。
      </p>
    </section>

    <NCard class="card-shadow">
      <template #header>
        <div>
          <h2 class="section-title">已配置模型入口</h2>
          <p class="section-lead">连接信息本地持久化保存，前端展示层不暴露真实供应商地址。</p>
        </div>
      </template>
      <template #header-extra>
        <NSpace>
          <NButton secondary :disabled="providers.length === 0" @click="verifyAll">
            <template #icon><NIcon><Refresh /></NIcon></template>
            检查连接
          </NButton>
          <NButton type="primary" @click="showForm = true">
            <template #icon><NIcon><Add /></NIcon></template>
            添加入口
          </NButton>
        </NSpace>
      </template>

      <NAlert v-if="testResults" type="info" class="provider-alert">
        <div v-for="(ok, name) in testResults" :key="name">
          {{ ok ? "可用" : "失败" }} · {{ name }}
        </div>
      </NAlert>

      <NEmpty v-if="providers.length === 0" description="暂未配置模型入口" />
      <NCollapse v-else>
        <NCollapseItem
          v-for="provider in providers"
          :key="provider.name"
          :title="provider.name"
          @click="loadCatalog(provider.name)"
        >
          <template #header-extra>
            <NSpace>
              <NTag type="success">{{ provider.model || "未设默认模型" }}</NTag>
              <NTag>{{ preferredText(provider) }}</NTag>
            </NSpace>
          </template>

          <div class="provider-card-top">
            <div>
              <div class="provider-title">
                <NIcon><Server /></NIcon>
                <strong>{{ provider.name }}</strong>
              </div>
              <p class="muted provider-meta">路由组：{{ routeGroupText(provider) }} · 场景：{{ preferredText(provider) }}</p>
              <div class="provider-badges">
                <NTag size="small" :bordered="false" type="warning">地址已隐藏</NTag>
                <NTag size="small" :bordered="false" type="default">
                  {{ provider.provider ? "显示供应商名" : "隐藏供应商名" }}
                </NTag>
              </div>
            </div>
            <NButton quaternary type="error" @click.stop="confirmRemove(provider.name)">
              <template #icon><NIcon><Trash /></NIcon></template>
            </NButton>
          </div>

          <NAlert v-if="catalogs[provider.name]?.error" type="warning" class="provider-alert">
            {{ catalogs[provider.name].error }}
          </NAlert>

          <NButton secondary :loading="loadingCatalogs.includes(provider.name)" @click="loadCatalog(provider.name)">
            刷新模型目录
          </NButton>

          <NDataTable
            v-if="catalogs[provider.name]?.models?.length"
            class="catalog-table"
            :columns="modelColumns"
            :data="catalogs[provider.name].models"
            :pagination="{ pageSize: 8 }"
            :scroll-x="980"
          />
          <NEmpty v-else class="catalog-empty" description="暂未读取到模型目录，或当前接口不支持列出模型。" />
        </NCollapseItem>
      </NCollapse>
    </NCard>

    <NModal v-model:show="showForm" preset="card" title="添加模型入口" class="provider-modal">
      <NAlert type="info" class="provider-alert">
        建议由 zclum 平台统一保存密钥并通过网关转发；独立运行时也可在本地配置自有兼容接口。
      </NAlert>

      <div class="template-area">
        <div class="muted template-label">快速模板</div>
        <NSpace>
          <NTag
            v-for="template in providerTemplates"
            :key="template.label"
            :bordered="false"
            class="template-tag"
            tabindex="0"
            @click="useTemplate(template)"
          >
            {{ template.label }}
          </NTag>
        </NSpace>
      </div>

      <NForm label-placement="top">
        <NFormItem label="入口名称">
          <NInput v-model:value="form.name" placeholder="例如 main-ocr / rag-answer" />
        </NFormItem>
        <NFormItem label="API 地址">
          <NInput v-model:value="form.base_url" placeholder="例如 https://api.example.com/v1" />
        </NFormItem>
        <NFormItem label="API Key">
          <NInput v-model:value="form.api_key" :type="showKey ? 'text' : 'password'" placeholder="sk-...">
            <template #suffix>
              <NIcon class="key-toggle" @click="showKey = !showKey">
                <Eye v-if="showKey" />
                <EyeOff v-else />
              </NIcon>
            </template>
          </NInput>
        </NFormItem>
        <NFormItem label="默认模型">
          <NInput v-model:value="form.model" placeholder="例如 gpt-5.5 / gpt-4o-mini" />
        </NFormItem>
        <NFormItem label="路由用途">
          <NSelect v-model:value="form.preferred_for" multiple :options="scenarioOptions" />
        </NFormItem>
        <NFormItem label="显示供应商名称">
          <NSpace align="center">
            <NSwitch v-model:value="form.visible_provider" />
            <span class="muted">关闭后，页面只展示自定义入口名称。</span>
          </NSpace>
        </NFormItem>
        <NAlert type="success">
          <template #icon><NIcon><ShieldCheckmark /></NIcon></template>
          保存后 API 地址不会在模型中心列表页展示。
        </NAlert>
      </NForm>

      <NSpace justify="end" class="modal-actions">
        <NButton @click="showForm = false">取消</NButton>
        <NButton type="primary" :loading="loading" @click="addProvider">保存</NButton>
      </NSpace>
    </NModal>
  </div>
</template>

<style scoped>
.provider-alert {
  margin-bottom: 16px;
}

.provider-card-top,
.provider-title {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.provider-card-top {
  justify-content: space-between;
  margin-bottom: 12px;
}

.provider-meta {
  margin: 8px 0 0;
}

.provider-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.catalog-table {
  margin-top: 16px;
}

.catalog-empty {
  margin-top: 14px;
}

.provider-modal {
  width: 760px;
  max-width: calc(100vw - 32px);
}

.template-area {
  margin-bottom: 16px;
}

.template-label {
  margin-bottom: 10px;
}

.key-toggle {
  cursor: pointer;
}

.modal-actions {
  margin-top: 22px;
}
</style>

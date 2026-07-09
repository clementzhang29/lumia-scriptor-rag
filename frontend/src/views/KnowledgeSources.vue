<script setup>
import { computed, onMounted, ref } from "vue"
import {
  NAlert,
  NButton,
  NCard,
  NEmpty,
  NForm,
  NFormItem,
  NGrid,
  NGi,
  NIcon,
  NInput,
  NModal,
  NPopconfirm,
  NSelect,
  NSpace,
  NSwitch,
  NTag,
  useMessage,
} from "naive-ui"
import { Add, CloudDownload, FolderOpen, Layers, Pencil, Refresh, Trash } from "@vicons/ionicons5"
import api from "../api"

const message = useMessage()
const loading = ref(false)
const syncingAll = ref(false)
const rebuildingMounted = ref(false)
const syncingIds = ref([])
const sources = ref([])
const supportedTypes = ref([])
const showModal = ref(false)
const editingId = ref("")
const selectedIds = ref([])

const form = ref(defaultForm())

function defaultForm() {
  return {
    name: "",
    type: "local_dir",
    enabled: true,
    config: {
      root_path: "",
      base_url: "",
      username: "",
      password: "",
      token: "",
    },
  }
}

const typeMap = computed(() =>
  supportedTypes.value.reduce((acc, item) => {
    acc[item.type] = item
    return acc
  }, {}),
)

const sourceTypeOptions = computed(() =>
  supportedTypes.value.map((item) => ({
    label: item.label,
    value: item.type,
  })),
)

async function loadSources() {
  loading.value = true
  try {
    const { data } = await api.kbSources.list()
    sources.value = data.sources || []
    supportedTypes.value = data.supported_types || []
    selectedIds.value = selectedIds.value.filter((id) => sources.value.some((item) => item.id === id))
  } catch (error) {
    message.error(error.response?.data?.detail || error.message || "知识源加载失败")
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingId.value = ""
  form.value = defaultForm()
  showModal.value = true
}

function toggleSelectEnabled() {
  const enabledIds = sources.value.filter((item) => item.enabled).map((item) => item.id)
  selectedIds.value = selectedIds.value.length === enabledIds.length ? [] : enabledIds
}

function openEdit(source) {
  editingId.value = source.id
  form.value = {
    name: source.name,
    type: source.type,
    enabled: !!source.enabled,
    config: {
      root_path: source.config?.root_path || "",
      base_url: source.config?.base_url || "",
      username: source.config?.username || "",
      password: "",
      token: "",
    },
  }
  showModal.value = true
}

function buildPayload() {
  const payload = {
    name: form.value.name.trim(),
    type: form.value.type,
    enabled: form.value.enabled,
    config: {},
  }
  for (const [key, value] of Object.entries(form.value.config)) {
    if (String(value || "").trim()) {
      payload.config[key] = value
    }
  }
  return payload
}

async function submitForm() {
  const payload = buildPayload()
  if (!payload.name) {
    message.warning("请填写知识源名称")
    return
  }
  if (payload.type === "local_dir" && !payload.config.root_path) {
    message.warning("请填写本地目录路径")
    return
  }
  if (payload.type !== "local_dir" && !payload.config.base_url) {
    message.warning("请填写服务地址")
    return
  }
  try {
    if (editingId.value) {
      await api.kbSources.update(editingId.value, payload)
      message.success("知识源已更新")
    } else {
      await api.kbSources.create(payload)
      message.success("知识源已创建")
    }
    showModal.value = false
    await loadSources()
  } catch (error) {
    message.error(error.response?.data?.detail || error.message || "保存失败")
  }
}

async function syncSource(source) {
  syncingIds.value = [...syncingIds.value, source.id]
  try {
    await api.kbSources.sync(source.id)
    message.success(`已同步：${source.name}`)
    await loadSources()
  } catch (error) {
    message.error(error.response?.data?.detail || error.message || "同步失败")
  } finally {
    syncingIds.value = syncingIds.value.filter((id) => id !== source.id)
  }
}

async function syncAll() {
  syncingAll.value = true
  try {
    const { data } = await api.kbSources.syncAll()
    const okCount = (data.results || []).filter((item) => !item.error).length
    message.success(`批量同步完成：${okCount} 个知识源成功`)
    await loadSources()
  } catch (error) {
    message.error(error.response?.data?.detail || error.message || "批量同步失败")
  } finally {
    syncingAll.value = false
  }
}

async function deleteSource(source) {
  try {
    await api.kbSources.delete(source.id)
    sources.value = sources.value.filter((item) => item.id !== source.id)
    selectedIds.value = selectedIds.value.filter((id) => id !== source.id)
    message.success(`已删除：${source.name}`)
  } catch (error) {
    message.error(error.response?.data?.detail || error.message || "删除失败")
  }
}

async function rebuildMounted() {
  const effectiveIds = selectedIds.value.length ? selectedIds.value : sources.value.filter((item) => item.enabled).map((item) => item.id)
  if (!effectiveIds.length) {
    message.warning("请至少启用或选择一个知识源")
    return
  }
  rebuildingMounted.value = true
  try {
    const { data } = await api.rag.rebuildMounted(effectiveIds, true)
    message.success(`挂载建库完成：${data.documents} 个文档，${data.chunks} 个片段`)
  } catch (error) {
    message.error(error.response?.data?.detail || error.message || "挂载建库失败")
  } finally {
    rebuildingMounted.value = false
  }
}

function visibleFields(type) {
  return typeMap.value[type]?.fields || []
}

function statusType(source) {
  if (source.last_sync_status === "ok") return "success"
  if (source.last_sync_status === "error") return "error"
  return "warning"
}

function statusText(source) {
  if (source.last_sync_status === "ok") return "同步完成"
  if (source.last_sync_status === "error") return "同步失败"
  return "未同步"
}

onMounted(loadSources)
</script>

<template>
  <div class="page-stack">
    <section class="hero-panel">
      <div class="hero-eyebrow">Knowledge Mount</div>
      <h1 class="hero-title">把本地目录、WebDAV 与 AList 云盘接成可维护的知识源。</h1>
      <p class="hero-subtitle">
        先挂载与同步，再把缓存资料送进文枢 RAG。这样用户后续换电脑、换盘或扩容知识库时，流程仍然保持一致。
      </p>
    </section>

    <NCard class="card-shadow">
      <template #header>
        <div>
          <h2 class="section-title">知识源控制台</h2>
          <p class="section-lead">支持独立维护外部语料，也支持一键同步后重建本地索引。</p>
        </div>
      </template>
      <template #header-extra>
        <NSpace>
          <NButton secondary :disabled="!sources.length" @click="toggleSelectEnabled">
            选择启用项
          </NButton>
          <NButton secondary @click="loadSources">
            <template #icon><NIcon><Refresh /></NIcon></template>
            刷新
          </NButton>
          <NButton :loading="syncingAll" @click="syncAll">
            <template #icon><NIcon><CloudDownload /></NIcon></template>
            同步全部
          </NButton>
          <NButton type="primary" @click="openCreate">
            <template #icon><NIcon><Add /></NIcon></template>
            新建知识源
          </NButton>
        </NSpace>
      </template>

      <NAlert type="info" class="surface-note" :show-icon="false">
        推荐工作流：新增知识源 → 同步缓存 → 选择需要参与索引的知识源 → 重建挂载索引。
      </NAlert>

      <div v-if="!sources.length && !loading" class="source-empty">
        <NEmpty description="暂时还没有知识源">
          <template #extra>
            <NButton type="primary" @click="openCreate">先添加一个</NButton>
          </template>
        </NEmpty>
      </div>

      <NGrid v-else cols="1 s:1 m:2 l:2" responsive="screen" :x-gap="16" :y-gap="16" class="source-grid">
        <NGi v-for="source in sources" :key="source.id">
          <NCard size="small" class="source-card" :bordered="false">
            <div class="source-top">
              <div class="source-meta">
                <label class="source-pick">
                  <input v-model="selectedIds" type="checkbox" :value="source.id" />
                  <span />
                </label>
                <div>
                  <div class="source-title-row">
                    <strong>{{ source.name }}</strong>
                    <NTag size="small" :type="statusType(source)">{{ statusText(source) }}</NTag>
                    <NTag size="small" type="info">{{ source.type }}</NTag>
                    <NTag v-if="!source.enabled" size="small">已停用</NTag>
                  </div>
                  <p class="source-path">{{ source.local_cache_dir }}</p>
                </div>
              </div>
              <NSpace size="small">
                <NButton size="small" secondary @click="openEdit(source)">
                  <template #icon><NIcon><Pencil /></NIcon></template>
                  编辑
                </NButton>
                <NButton size="small" secondary :loading="syncingIds.includes(source.id)" @click="syncSource(source)">
                  <template #icon><NIcon><CloudDownload /></NIcon></template>
                  同步
                </NButton>
                <NPopconfirm @positive-click="deleteSource(source)">
                  <template #trigger>
                    <NButton size="small" tertiary type="error">
                      <template #icon><NIcon><Trash /></NIcon></template>
                      删除
                    </NButton>
                  </template>
                  删除后会清理本地缓存，确认继续？
                </NPopconfirm>
              </NSpace>
            </div>

            <div class="source-stats">
              <div class="stat-chip">
                <span>已同步文件</span>
                <strong>{{ source.synced_files || 0 }}</strong>
              </div>
              <div class="stat-chip">
                <span>最近同步</span>
                <strong>{{ source.last_sync_at || "尚未同步" }}</strong>
              </div>
            </div>

            <div class="source-config">
              <div v-for="(value, key) in source.config" :key="key" class="config-item">
                <span>{{ key }}</span>
                <code>{{ value }}</code>
              </div>
            </div>

            <p v-if="source.last_error" class="error-note">{{ source.last_error }}</p>
          </NCard>
        </NGi>
      </NGrid>

      <div class="mount-actions">
        <div class="surface-note mount-summary">
          <strong>已选知识源：</strong>{{ selectedIds.length }} 个
          <span>如不手动勾选，将默认使用所有已启用知识源建库。</span>
        </div>
        <NButton type="primary" size="large" :loading="rebuildingMounted" :disabled="!sources.length" @click="rebuildMounted">
          <template #icon><NIcon><Layers /></NIcon></template>
          从挂载知识源重建 RAG
        </NButton>
      </div>
    </NCard>

    <NCard class="card-shadow">
      <template #header>
        <div>
          <h2 class="section-title">接入说明</h2>
          <p class="section-lead">先做兼容最广的三类挂载，后续再往上扩充更多商业云盘适配器。</p>
        </div>
      </template>
      <div class="feature-grid mount-feature-grid">
        <div class="surface-note">
          <strong>本地目录</strong>
          <p>适合已完成 OCR/排版的本机资料夹，最快速，几乎零额外维护。</p>
        </div>
        <div class="surface-note">
          <strong>WebDAV</strong>
          <p>适合坚果云、Nextcloud、群晖、S3 网关等标准协议服务。</p>
        </div>
        <div class="surface-note">
          <strong>AList</strong>
          <p>适合作为聚合层，把多个网盘统一映射成一个可维护知识库入口。</p>
        </div>
      </div>
    </NCard>

    <NModal v-model:show="showModal" preset="card" class="source-modal" :title="editingId ? '编辑知识源' : '新增知识源'">
      <NForm label-placement="top">
        <NFormItem label="名称">
          <NInput v-model:value="form.name" placeholder="例如：中医古籍本地库 / 坚果云公共库" />
        </NFormItem>
        <NGrid cols="1 s:2" responsive="screen" :x-gap="16">
          <NGi>
            <NFormItem label="类型">
              <NSelect v-model:value="form.type" :options="sourceTypeOptions" />
            </NFormItem>
          </NGi>
          <NGi>
            <NFormItem label="启用">
              <NSwitch v-model:value="form.enabled" />
            </NFormItem>
          </NGi>
        </NGrid>

        <NFormItem v-if="visibleFields(form.type).includes('root_path')" label="根目录 / 挂载路径">
          <NInput v-model:value="form.config.root_path" placeholder="例如 C:\资料库 或 /books" />
        </NFormItem>
        <NFormItem v-if="visibleFields(form.type).includes('base_url')" label="服务地址">
          <NInput v-model:value="form.config.base_url" placeholder="例如 https://dav.example.com 或 https://alist.example.com" />
        </NFormItem>
        <NGrid v-if="visibleFields(form.type).includes('username') || visibleFields(form.type).includes('password')" cols="1 s:2" responsive="screen" :x-gap="16">
          <NGi v-if="visibleFields(form.type).includes('username')">
            <NFormItem label="用户名">
              <NInput v-model:value="form.config.username" placeholder="WebDAV 用户名" />
            </NFormItem>
          </NGi>
          <NGi v-if="visibleFields(form.type).includes('password')">
            <NFormItem label="密码">
              <NInput v-model:value="form.config.password" type="password" show-password-on="click" placeholder="留空则沿用已有密码" />
            </NFormItem>
          </NGi>
        </NGrid>
        <NFormItem v-if="visibleFields(form.type).includes('token')" label="访问 Token">
          <NInput v-model:value="form.config.token" type="password" show-password-on="click" placeholder="AList Token，留空则沿用已有值" />
        </NFormItem>
      </NForm>

      <template #action>
        <NSpace justify="end">
          <NButton @click="showModal = false">取消</NButton>
          <NButton type="primary" @click="submitForm">
            <template #icon><NIcon><FolderOpen /></NIcon></template>
            保存知识源
          </NButton>
        </NSpace>
      </template>
    </NModal>
  </div>
</template>

<style scoped>
.source-grid {
  margin-top: 18px;
}

.source-empty {
  padding: 30px 0 10px;
}

.source-card {
  min-height: 240px;
  border-radius: 20px;
  background: rgba(255, 253, 248, 0.94);
  box-shadow: var(--shadow-card);
}

.source-top {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.source-meta {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  min-width: 0;
}

.source-pick {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  margin-top: 4px;
}

.source-pick input {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
}

.source-pick span {
  width: 18px;
  height: 18px;
  border-radius: 6px;
  border: 1px solid rgba(22, 114, 103, 0.28);
  background: white;
}

.source-pick input:checked + span {
  background: var(--brand-600);
  border-color: var(--brand-600);
  box-shadow: inset 0 0 0 4px rgba(255, 255, 255, 0.9);
}

.source-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.source-title-row strong {
  font-size: 18px;
}

.source-path {
  margin: 8px 0 0;
  font-size: 12px;
  color: var(--text-faint);
  word-break: break-all;
}

.source-stats {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin: 18px 0;
}

.stat-chip {
  padding: 12px 14px;
  border-radius: 14px;
  background: var(--bg-panel-soft);
  border: 1px solid rgba(22, 114, 103, 0.09);
}

.stat-chip span,
.config-item span {
  display: block;
  font-size: 12px;
  color: var(--text-muted);
}

.stat-chip strong {
  display: block;
  margin-top: 6px;
  line-height: 1.5;
  color: var(--text-strong);
}

.source-config {
  display: grid;
  gap: 10px;
}

.config-item {
  padding: 10px 12px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(22, 114, 103, 0.08);
}

.config-item code {
  display: block;
  margin-top: 6px;
  font-family: var(--font-mono);
  color: var(--brand-700);
  word-break: break-all;
}

.error-note {
  margin: 12px 0 0;
  color: var(--danger-600);
  line-height: 1.7;
  white-space: pre-wrap;
}

.mount-actions {
  margin-top: 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.mount-summary {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
}

.mount-feature-grid p {
  margin: 8px 0 0;
  color: var(--text-muted);
  line-height: 1.8;
}

.source-modal {
  max-width: 760px;
}

@media (max-width: 860px) {
  .source-top,
  .mount-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .source-stats {
    grid-template-columns: 1fr;
  }
}
</style>

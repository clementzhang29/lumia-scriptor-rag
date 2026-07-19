<script setup>
import { onMounted, onUnmounted } from "vue"
import { useAppStore } from "./stores/app"
import {
  NConfigProvider,
  NMessageProvider,
  NDialogProvider,
  NLayout,
  NLayoutHeader,
  NLayoutContent,
  NButton,
  NBadge,
  NIcon,
  darkTheme,
} from "naive-ui"
import {
  DocumentText,
  Settings,
  CogOutline,
  Sparkles,
  Library,
  FolderOpen,
  Layers,
  PlayCircle,
  Pulse,
  OpenOutline,
  HelpCircle,
} from "@vicons/ionicons5"

const store = useAppStore()

const navItems = [
  { to: "/", shortLabel: "OCR", title: "上传 PDF 并启动 OCR", icon: DocumentText },
  { to: "/guide", shortLabel: "导览", title: "查看完整产品流程", icon: PlayCircle },
  { to: "/format", shortLabel: "排版", title: "清理并导出 Markdown", icon: Sparkles },
  { to: "/rag", shortLabel: "RAG", title: "构建知识库并检索引用", icon: Library },
  { to: "/sources", shortLabel: "知识源", title: "挂载外部目录与云盘知识库", icon: FolderOpen },
  { to: "/providers", shortLabel: "模型", title: "配置 LLM Provider", icon: Settings },
  { to: "/help", shortLabel: "帮助", title: "查看使用与迁移说明", icon: HelpCircle },
]

let healthTimer = null

onMounted(() => {
  store.fetchHealth()
  store.fetchEngines()
  store.fetchProviders()
  healthTimer = window.setInterval(() => store.fetchHealth(), 15000)
})

onUnmounted(() => {
  if (healthTimer) window.clearInterval(healthTimer)
})

function openLocalRoot() {
  window.location.href = "http://127.0.0.1:8080/"
}
</script>

<template>
  <NConfigProvider
    :theme="store.darkMode ? darkTheme : null"
    :theme-overrides="{
      common: {
        primaryColor: '#167267',
        primaryColorHover: '#1f8a7d',
        primaryColorPressed: '#11564f',
        borderRadius: '14px',
        fontFamily: 'Noto Sans SC, PingFang SC, Microsoft YaHei UI, Segoe UI, sans-serif',
      },
      Card: { color: '#fffdf8', borderRadius: '22px' },
      Button: {
        borderRadiusSmall: '12px',
        borderRadiusMedium: '14px',
        borderRadiusLarge: '16px',
      },
    }"
  >
    <NMessageProvider>
      <NDialogProvider>
        <NLayout position="absolute" class="app-shell">
          <NLayoutHeader bordered class="app-header">
            <div class="header-inner">
              <router-link to="/" class="brand" aria-label="返回首页">
                <span class="brand-mark"><NIcon size="20"><Layers /></NIcon></span>
                <span class="brand-copy">
                  <strong>Lumia ScriptorRAG</strong>
                  <small>本地 OCR、Markdown 排版与文档 RAG 工作台</small>
                </span>
              </router-link>

              <nav class="main-nav" aria-label="主导航">
                <router-link
                  v-for="item in navItems"
                  :key="item.to"
                  :to="item.to"
                  class="nav-link"
                  :title="item.title"
                >
                  <NIcon size="16"><component :is="item.icon" /></NIcon>
                  <span>{{ item.shortLabel }}</span>
                </router-link>
              </nav>

              <div class="header-actions">
                <span class="health-pill" :class="{ ok: !!store.health, bad: !store.health }">
                  <NIcon size="14"><Pulse /></NIcon>
                  {{ store.health ? "服务在线" : "服务离线" }}
                </span>
                <NButton secondary size="small" @click="openLocalRoot">
                  <template #icon><NIcon><OpenOutline /></NIcon></template>
                  打开本地
                </NButton>
                <NBadge :value="store.providers.length" :max="99">
                  <NButton secondary size="small" @click="store.darkMode = !store.darkMode">
                    <template #icon><NIcon><CogOutline /></NIcon></template>
                    {{ store.darkMode ? "浅色" : "深色" }}
                  </NButton>
                </NBadge>
              </div>
            </div>
          </NLayoutHeader>
          <NLayoutContent class="app-content">
            <div class="page-container">
              <router-view />
            </div>
          </NLayoutContent>
        </NLayout>
      </NDialogProvider>
    </NMessageProvider>
  </NConfigProvider>
</template>

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
  Sparkles,
  Library,
  FolderOpen,
  Layers,
  PlayCircle,
  Pulse,
  HelpCircle,
  CloudUploadOutline,
} from "@vicons/ionicons5"

const store = useAppStore()

const navItems = [
  { to: "/", shortLabel: "OCR", title: "上传 PDF 并转换 Markdown", icon: DocumentText },
  { to: "/guide", shortLabel: "流程", title: "查看智能体工作流", icon: PlayCircle },
  { to: "/format", shortLabel: "排版", title: "清理、润色与导出 Markdown", icon: Sparkles },
  { to: "/rag", shortLabel: "检索", title: "知识库问答与引用检索", icon: Library },
  { to: "/sources", shortLabel: "挂载", title: "维护本地与云盘知识源", icon: FolderOpen },
  { to: "/providers", shortLabel: "模型", title: "配置模型与校正能力", icon: Settings },
  { to: "/help", shortLabel: "帮助", title: "使用说明与二次开发", icon: HelpCircle },
]

let healthTimer = null

onMounted(() => {
  store.darkMode = true
  store.fetchHealth()
  store.fetchEngines()
  store.fetchProviders()
  healthTimer = window.setInterval(() => store.fetchHealth(), 15000)
})

onUnmounted(() => {
  if (healthTimer) window.clearInterval(healthTimer)
})
</script>

<template>
  <NConfigProvider
    :theme="darkTheme"
    :theme-overrides="{
      common: {
        primaryColor: '#20e7d7',
        primaryColorHover: '#61fff4',
        primaryColorPressed: '#12bdb0',
        borderRadius: '16px',
        fontFamily: 'Noto Sans SC, PingFang SC, Microsoft YaHei UI, Segoe UI, sans-serif',
        bodyColor: '#070b12',
        cardColor: 'rgba(10, 17, 28, 0.78)',
      },
      Card: {
        color: 'rgba(10, 17, 28, 0.82)',
        borderColor: 'rgba(125, 231, 255, 0.13)',
        borderRadius: '22px',
      },
      Button: {
        borderRadiusSmall: '12px',
        borderRadiusMedium: '14px',
        borderRadiusLarge: '16px',
      },
    }"
  >
    <NMessageProvider>
      <NDialogProvider>
        <NLayout position="absolute" class="app-shell zclum-shell">
          <div class="ambient-field" aria-hidden="true">
            <span class="ambient-grid"></span>
            <span class="ambient-scanner"></span>
            <span class="ambient-orbit orbit-a"></span>
            <span class="ambient-orbit orbit-b"></span>
          </div>

          <NLayoutHeader bordered class="app-header">
            <div class="header-inner">
              <router-link to="/" class="brand" aria-label="返回 OCR 智能体首页">
                <span class="brand-mark"><NIcon size="20"><Layers /></NIcon></span>
                <span class="brand-copy">
                  <strong>ZCLUM · 光棱 OCR</strong>
                  <small>PDF 解析、排版与 RAG 知识接入智能体</small>
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
                  {{ store.health ? "在线" : "离线" }}
                </span>
                <NBadge :value="store.providers.length" :max="99">
                  <NButton tertiary size="small" tag="router-link" to="/providers">
                    <template #icon><NIcon><CloudUploadOutline /></NIcon></template>
                    模型
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

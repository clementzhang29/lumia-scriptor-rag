<script setup>
import { computed, ref } from "vue"
import { useRouter } from "vue-router"
import { NButton, NCard, NIcon, NSpace, NTag } from "naive-ui"
import { ArrowBack, ArrowForward, DocumentText, Sparkles, Library, Settings, Rocket, OpenOutline } from "@vicons/ionicons5"

const router = useRouter()
const current = ref(0)

const scenes = [
  {
    eyebrow: "Prism OCR",
    title: "光棱 OCR 路由",
    body: "从上传 PDF 开始，光棱官先分析文档类型、语言、扫描属性，再按 Surya → MinerU → Marker → Docling → PaddleOCR 的策略执行识文。",
    route: "/",
    action: "进入光棱工作台",
    icon: DocumentText,
    points: ["自动推荐引擎", "失败回退", "质量评分"],
  },
  {
    eyebrow: "Glyph Forge",
    title: "字炉排版与结构清洗",
    body: "OCR 输出的 Markdown 会进入字炉：修标题、空行、列表、代码块，并尽可能去掉无意义符号，让文档适合阅读和建库。",
    route: "/format",
    action: "进入字炉排版",
    icon: Sparkles,
    points: ["复制结果", "导出 MD", "导出 HTML"],
  },
  {
    eyebrow: "ScriptorRAG Vault",
    title: "文枢 RAG 建库",
    body: "选择整理后的文档目录，支持 md / txt / html / pdf / epub / docx，检索时至少返回 5 条不同文档来源。",
    route: "/rag",
    action: "进入文枢 RAG",
    icon: Library,
    points: ["来源去重", "原典加权", "结果导出"],
  },
  {
    eyebrow: "Model Orbit",
    title: "星轨模型复用",
    body: "OpenAI、DeepSeek、GLM、Kimi、Qwen、Claude 等 Provider 在星轨模型中配置，OCR 校正和文枢综合回答共用。",
    route: "/providers",
    action: "配置星轨模型",
    icon: Settings,
    points: ["自动识别厂商", "连接检查", "内存保存 Key"],
  },
]

const scene = computed(() => scenes[current.value])

function prev() {
  current.value = Math.max(0, current.value - 1)
}

function next() {
  current.value = Math.min(scenes.length - 1, current.value + 1)
}
</script>

<template>
  <div class="guide-page">
    <section class="guide-stage">
      <div class="stage-copy">
        <div class="hero-eyebrow">{{ scene.eyebrow }}</div>
        <h1>{{ scene.title }}</h1>
        <p>{{ scene.body }}</p>
        <NSpace>
          <NTag v-for="point in scene.points" :key="point" :bordered="false">{{ point }}</NTag>
        </NSpace>
        <NSpace style="margin-top:26px">
          <NButton secondary :disabled="current === 0" @click="prev">
            <template #icon><NIcon><ArrowBack /></NIcon></template>
            上一步
          </NButton>
          <NButton secondary :disabled="current === scenes.length - 1" @click="next">
            下一步
            <template #icon><NIcon><ArrowForward /></NIcon></template>
          </NButton>
          <NButton type="primary" @click="router.push(scene.route)">
            <template #icon><NIcon><OpenOutline /></NIcon></template>
            {{ scene.action }}
          </NButton>
        </NSpace>
      </div>

      <div class="stage-visual">
        <div class="orbit">
          <div class="orbit-core">
            <NIcon size="54"><component :is="scene.icon" /></NIcon>
          </div>
          <span v-for="(item, index) in scenes" :key="item.title" class="orbit-node" :class="{ active: index === current }" :style="{ '--i': index }" @click="current = index">
            {{ index + 1 }}
          </span>
        </div>
      </div>
    </section>

    <div class="guide-strip">
      <NCard v-for="(item, index) in scenes" :key="item.title" class="guide-card" :class="{ active: index === current }" @click="current = index">
        <div class="guide-card-title">
          <NIcon><component :is="item.icon" /></NIcon>
          <strong>{{ item.title }}</strong>
        </div>
        <p>{{ item.body }}</p>
      </NCard>
    </div>

    <NCard class="card-shadow">
      <div class="release-row">
        <div>
          <h2 class="section-title">发布前产品闭环</h2>
          <p class="muted" style="margin:0">当前版本已形成光棱 OCR、字炉排版、文枢 RAG、星轨模型四个独立模块，也能串成完整工作流。</p>
        </div>
        <NButton type="primary" @click="router.push('/')">
          <template #icon><NIcon><Rocket /></NIcon></template>
          开始使用
        </NButton>
      </div>
    </NCard>
  </div>
</template>

<style scoped>
.guide-page {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.guide-stage {
  min-height: 560px;
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(340px, .9fr);
  gap: 28px;
  align-items: center;
  padding: 38px;
  border-radius: 34px;
  color: white;
  overflow: hidden;
  background:
    radial-gradient(circle at 78% 22%, rgba(250, 204, 21, .24), transparent 28%),
    linear-gradient(135deg, #0f766e, #132f2d 72%);
  box-shadow: 0 32px 90px rgba(15, 118, 110, .26);
}

.stage-copy h1 {
  max-width: 780px;
  margin: 12px 0 14px;
  font-size: clamp(42px, 7vw, 82px);
  line-height: .95;
  letter-spacing: -.07em;
}

.stage-copy p {
  max-width: 680px;
  color: rgba(255, 255, 255, .78);
  font-size: 17px;
  line-height: 1.9;
}

.stage-visual {
  display: grid;
  place-items: center;
}

.orbit {
  position: relative;
  width: min(360px, 72vw);
  aspect-ratio: 1;
  display: grid;
  place-items: center;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, .22);
  background: radial-gradient(circle, rgba(255,255,255,.13), rgba(255,255,255,.04));
}

.orbit-core {
  width: 154px;
  height: 154px;
  display: grid;
  place-items: center;
  border-radius: 48px;
  color: #0f766e;
  background: #fffdf8;
  box-shadow: 0 26px 70px rgba(0, 0, 0, .22);
}

.orbit-node {
  --angle: calc(var(--i) * 90deg - 42deg);
  position: absolute;
  top: 50%;
  left: 50%;
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  color: rgba(255,255,255,.78);
  background: rgba(255,255,255,.12);
  border: 1px solid rgba(255,255,255,.18);
  transform: translate(-50%, -50%) rotate(var(--angle)) translate(168px) rotate(calc(-1 * var(--angle)));
  cursor: pointer;
  transition: all .2s ease;
}

.orbit-node.active {
  color: #134e4a;
  background: #fde68a;
  transform: translate(-50%, -50%) rotate(var(--angle)) translate(168px) rotate(calc(-1 * var(--angle))) scale(1.14);
}

.guide-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.guide-card {
  cursor: pointer;
}

.guide-card.active {
  outline: 2px solid rgba(15, 118, 110, .45);
}

.guide-card-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.guide-card p {
  margin-bottom: 0;
  color: #71807a;
  line-height: 1.7;
}

.release-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
}

@media (max-width: 980px) {
  .guide-stage,
  .guide-strip {
    grid-template-columns: 1fr;
  }

  .guide-stage {
    padding: 26px;
  }

  .release-row {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>

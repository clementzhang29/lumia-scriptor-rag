import { createRouter, createWebHistory } from "vue-router"
import Home from "./views/Home.vue"
import Guide from "./views/Guide.vue"
import Formatter from "./views/Formatter.vue"
import Rag from "./views/Rag.vue"
import KnowledgeSources from "./views/KnowledgeSources.vue"
import Providers from "./views/Providers.vue"
import Result from "./views/Result.vue"
import Help from "./views/Help.vue"

const routes = [
  { path: "/", name: "Home", component: Home },
  { path: "/guide", name: "Guide", component: Guide },
  { path: "/format", name: "Formatter", component: Formatter },
  { path: "/rag", name: "Rag", component: Rag },
  { path: "/sources", name: "KnowledgeSources", component: KnowledgeSources },
  { path: "/providers", name: "Providers", component: Providers },
  { path: "/help", name: "Help", component: Help },
  { path: "/result/:id", name: "Result", component: Result, props: true },
  { path: "/:pathMatch(.*)*", redirect: "/" },
]

export default createRouter({ history: createWebHistory(), routes })

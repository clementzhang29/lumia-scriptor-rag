import { defineStore } from "pinia"
import api from "../api"

export const useAppStore = defineStore("app", {
  state: () => ({
    engines: [],
    providers: [],
    currentTask: null,
    darkMode: false,
    health: null,
    healthError: "",
  }),
  actions: {
    async fetchHealth() {
      try {
        const { data } = await api.health()
        this.health = data
        this.healthError = ""
      } catch (e) {
        this.health = null
        this.healthError = e.message || "服务当前不可用"
      }
    },
    async fetchEngines() {
      try {
        const { data } = await api.engines()
        this.engines = data.engines || []
      } catch (e) {
        console.error("Failed to fetch engines", e)
      }
    },
    async fetchProviders() {
      try {
        const { data } = await api.providers.list()
        this.providers = data.providers || []
      } catch (e) {
        console.error("Failed to fetch providers", e)
      }
    },
  },
})

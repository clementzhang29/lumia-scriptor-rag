import axios from "axios"

const api = axios.create({ baseURL: "/api" })

export default {
  health: () => api.get("/health"),
  engines: () => api.get("/engines"),
  format: {
    markdown: (payload) => api.post("/format/markdown", typeof payload === "string" ? { markdown: payload } : payload),
  },
  rag: {
    status: () => api.get("/rag/status"),
    rebuild: (corpus_dir) => api.post("/rag/rebuild", { corpus_dir }),
    rebuildMounted: (source_ids = [], sync_first = true) => api.post("/rag/rebuild-mounted", { source_ids, sync_first }),
    query: (question, top_k = 8, use_llm = true) => api.post("/rag/query", { question, top_k, use_llm }),
  },
  kbSources: {
    list: () => api.get("/kb-sources"),
    create: (data) => api.post("/kb-sources", data),
    update: (id, data) => api.put(`/kb-sources/${id}`, data),
    delete: (id) => api.delete(`/kb-sources/${id}`),
    sync: (id) => api.post(`/kb-sources/${id}/sync`),
    syncAll: () => api.post("/kb-sources/sync-all"),
  },
  providers: {
    list: () => api.get("/providers"),
    register: (data) => api.post("/providers", data),
    delete: (name) => api.post(`/providers/delete/${name}`),
    verify: () => api.post("/providers/verify"),
    catalog: (name) => api.get(`/providers/catalog/${name}`),
  },
  convert: (file, strategy, preferredEngine, onProgress) => {
    const form = new FormData()
    form.append("file", file)
    form.append("strategy", strategy)
    form.append("preferred_engine", preferredEngine)
    return api.post("/convert", form, {
      onUploadProgress: (e) => onProgress && onProgress(Math.round((e.loaded / e.total) * 100)),
    })
  },
  status: (id) => api.get(`/status/${id}`),
  result: (id) => api.get(`/result/${id}`),
  download: (id) => `${api.defaults.baseURL}/download/${id}`,
}

import axios from "axios"

const embeddedBase =
  window.__ZCLUM_OCR_BASE_URL__ ||
  window.__OCR_HARNESS_BASE_URL__ ||
  window.__HOST_OCR_BASE_URL__ ||
  window.__ANZAIDX_OCR_BASE_URL__ ||
  import.meta.env.VITE_ZCLUM_OCR_BASE ||
  import.meta.env.VITE_OCR_HARNESS_BASE ||
  import.meta.env.VITE_HOST_OCR_BASE ||
  import.meta.env.VITE_ANZAIDX_OCR_BASE ||
  import.meta.env.VITE_API_BASE ||
  "/api"

const api = axios.create({ baseURL: embeddedBase })

function readToken() {
  return (
    window.__ZCLUM_USER_TOKEN__ ||
    window.__ZCLUM_TOKEN__ ||
    window.__OCR_HARNESS_USER_TOKEN__ ||
    window.__OCR_HARNESS_TOKEN__ ||
    window.__HOST_USER_TOKEN__ ||
    window.__ANZAIDX_USER_TOKEN__ ||
    window.__ANZAIDX_TOKEN__ ||
    localStorage.getItem("zclum_user_token") ||
    localStorage.getItem("zclum_token") ||
    localStorage.getItem("ocr_harness_user_token") ||
    localStorage.getItem("ocr_harness_token") ||
    localStorage.getItem("host_user_token") ||
    localStorage.getItem("anzaidx_user_token") ||
    localStorage.getItem("anzaidx_token") ||
    sessionStorage.getItem("zclum_user_token") ||
    sessionStorage.getItem("zclum_token") ||
    sessionStorage.getItem("ocr_harness_user_token") ||
    sessionStorage.getItem("ocr_harness_token") ||
    sessionStorage.getItem("host_user_token") ||
    sessionStorage.getItem("anzaidx_user_token") ||
    sessionStorage.getItem("anzaidx_token") ||
    ""
  )
}

api.interceptors.request.use((config) => {
  const token = readToken()
  if (token && !config.headers.Authorization) {
    config.headers.Authorization = `Bearer ${token}`
  }
  config.headers["X-Agent-App"] = "ocr-harness"
  return config
})

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
  convertBatch: (files, strategy, preferredEngine, onProgress) => {
    const form = new FormData()
    files.forEach((file) => form.append("files", file, file.webkitRelativePath || file.name))
    form.append("strategy", strategy)
    form.append("preferred_engine", preferredEngine)
    return api.post("/convert/batch", form, {
      onUploadProgress: (e) => onProgress && onProgress(Math.round((e.loaded / e.total) * 100)),
    })
  },
  status: (id) => api.get(`/status/${id}`),
  batch: (id) => api.get(`/batch/${id}`),
  result: (id) => api.get(`/result/${id}`),
  download: (id) => `${api.defaults.baseURL}/download/${id}`,
  client: api,
}

# Zclum.con 轻应用部署指南

作者：张春  
整理说明：AI 根据当前可运行项目状态整理生成  
时间：2026-07-09

---

## 1. 目标

把 **Lumia ScriptorRAG** 作为一个对外可访问的“轻应用入口”部署到：

- `https://zclum.con`

这个部署方案适合：

- 前端页面公开访问
- 用户通过网页上传 PDF、做排版、做 RAG 查询
- 后端统一提供 API

---

## 2. 推荐部署形态

不建议把当前系统理解成“纯静态轻应用”，因为它依赖：

- FastAPI
- OCR 引擎
- 本地文件上传
- RAG 索引数据
- LLM Provider 配置

因此推荐结构为：

```text
zclum.con
  └─ Nginx / Caddy
       └─ Reverse Proxy
            └─ Lumia ScriptorRAG (FastAPI + Built Frontend)
```

也就是：

- 域名访问是“轻应用入口”
- 实际仍由后端服务承载 OCR / 排版 / RAG

---

## 3. 当前最适合的上线模式

### 模式 A：单机轻应用版（推荐先用）

适合：

- 先快速上线
- 有 1 台云服务器
- 访问量不大

结构：

- Nginx
- Docker Compose
- `lumia-scriptor-rag` 容器

### 模式 B：前台轻应用 + 独立 OCR Worker

适合：

- 后续要接 GPU
- OCR 转换量会变大
- 想把 Web 入口和 OCR 执行隔离

当前仓库先支持模式 A，后续可演进到模式 B。

---

## 4. 服务器要求

最低建议：

- Ubuntu 22.04
- 2 vCPU / 4GB RAM
- 20GB 磁盘

如需更重的 OCR：

- 8GB+ RAM
- 或单独 GPU 服务器

---

## 5. 仓库内已提供的部署文件

- `Dockerfile`
- `docker-compose.yml`
- `deploy/.env.example`
- `deploy/nginx/zclum.con.conf`
- `deploy/nginx/zclum.con-https.conf`

---

## 6. 部署步骤

### 6.1 拉代码

```bash
git clone https://github.com/clementzhang29/lumia-scriptor-rag.git
cd lumia-scriptor-rag
```

### 6.2 准备环境变量

```bash
cp deploy/.env.example .env
```

如仅 CPU：

```env
APP_PORT=8080
CUDA_VISIBLE_DEVICES=
```

如 GPU 服务器：

```env
APP_PORT=8080
CUDA_VISIBLE_DEVICES=0
```

### 6.3 启动容器

```bash
docker compose up -d --build
```

### 6.4 本地验证

```bash
curl http://127.0.0.1:8080/api/health
```

应返回：

```json
{"status":"ok", ...}
```

---

## 7. Nginx 绑定域名

### HTTP 版

把 `deploy/nginx/zclum.con.conf` 放到：

```bash
/etc/nginx/sites-available/zclum.con
```

然后：

```bash
ln -s /etc/nginx/sites-available/zclum.con /etc/nginx/sites-enabled/zclum.con
nginx -t
systemctl reload nginx
```

### HTTPS 版

证书申请后，使用：

- `deploy/nginx/zclum.con-https.conf`

建议通过 `certbot`：

```bash
apt-get update
apt-get install -y certbot python3-certbot-nginx
certbot --nginx -d zclum.con -d www.zclum.con
```

---

## 8. DNS 注意事项

当前你给的 `zclum.con` 已有解析，但是否为正式公网服务地址还需要确认。

上线前需要确保：

- `zclum.con` A 记录指向你的公网服务器 IP
- 80 / 443 端口已放行
- 服务器上 Nginx 能访问 `127.0.0.1:8080`

---

## 9. 产品上云后的定位

上线到 `zclum.con` 后，它更适合作为：

- OCR + RAG 的 Web 轻应用入口
- 文档处理工作台
- 私有知识库服务前台

而不是“零后端纯网页工具”。

---

## 10. 生产建议

### 建议先上线的功能

- OCR 上传转换
- 字炉排版
- 文枢 RAG 查询
- 模型中心
- 知识源挂载

### 建议暂缓完全开放的功能

- 大文件高频 OCR
- 公网匿名批量转换
- 高并发模型目录查询

### 原因

因为 OCR 与 RAG 都有计算和存储成本，前期应先保证稳定。

---

## 11. 后续演进方向

后续可升级为：

```text
zclum.con          -> 前端入口
api.zclum.con      -> FastAPI
ocr.zclum.con      -> OCR Worker / GPU 服务
```

这样更适合正式产品化。

---

## 12. 一句话结论

**可以放到 `zclum.con`，但推荐作为“有后端支撑的轻应用入口”部署，而不是纯静态站。**


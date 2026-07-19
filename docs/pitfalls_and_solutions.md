# Lumia ScriptorRAG 踩坑与解决方案

生成时间：2026-07-06
作者：张春
说明：AI 根据项目文件与调试过程整理生成。

## Windows 无法识别 python

**现象**：PowerShell 提示 `python` 不是可识别命令。
**处理**：优先使用 Windows Python Launcher：

```powershell
py -3 -B -m uvicorn src.web.app:app --host 127.0.0.1 --port 8080 --log-level info
```

## MinerU / torch GPU DLL 冲突

**现象**：MinerU 安装后缺少 `doclayout_yolo` 或触发 torch GPU DLL 加载错误。
**处理**：安装缺失依赖，并在必要时让 MinerU CPU 降级：

```powershell
pip install doclayout_yolo ultralytics
```

在调用 MinerU 解析前设置：

```python
os.environ["CUDA_VISIBLE_DEVICES"] = ""
```

## FastAPI 前端白屏

**现象**：`http://127.0.0.1:8080/` 返回 200，但页面空白。
**根因**：`/assets/*.js` 被 SPA fallback 返回成 `index.html`，浏览器没有执行 Vue 入口脚本。
**处理**：在 `src/web/app.py` 中挂载 Vite 构建产物：

```python
app.mount("/assets", StaticFiles(directory=str(assets_path)), name="assets")
```

## Vue History 刷新 404

**现象**：刷新 `/rag`、`/help` 等前端路由可能返回 404。
**处理**：后端保留 SPA fallback：非 `/api/` 路径统一返回 `frontend/dist/index.html`。

## 顶部导航拥挤竖排

**现象**：导航项中文较长，在中等宽度下挤成竖排并越界。
**处理**：最终版改为图标 + 短文案：`OCR / 导览 / 排版 / RAG / 模型 / 帮助`，并增加横向滚动和 `white-space: nowrap`。

## RAG 检索宽度不足

**现象**：回答引用来源过少，知识宽度不足。
**处理**：检索结果要求优先不同文档来源，至少返回多条引用；古籍原典权重高于近现代补充资料。

## API Key 安全

**现象**：LLM Provider 需要测试，但 Key 不能进入仓库。
**处理**：不要把 API Key 写入代码或提交到 Git；生产版应使用加密落盘或系统密钥管理。

## 仓库体积与临时文件

**现象**：OCR 项目容易产生上传文件、日志、构建缓存、大型下载残留。
**处理**：最终交付前清理 `__pycache__`、日志、临时修复脚本、下载残留；保留源码、文档、前端 dist、必要启动脚本和测试脚本。

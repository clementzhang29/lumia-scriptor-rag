# Security Policy / 安全政策

## Supported Versions

The current `main` branch is the supported development version.

当前 `main` 分支为主要维护版本。

## Sensitive Data

Do not commit:

- API keys,
- model provider tokens,
- private PDF files,
- extracted private Markdown,
- local vector databases,
- runtime upload folders.

不要提交 API Key、模型供应商 Token、私有 PDF、私有 Markdown、向量数据库或运行时上传目录。

## Reporting a Vulnerability

Please report security issues privately through the project maintainer before opening a public issue.

If this project is deployed behind zclum.com or another platform gateway, validate:

- upload size limits,
- user authentication,
- per-user quota,
- file retention policy,
- provider-key isolation,
- path traversal protection for mounted knowledge sources.


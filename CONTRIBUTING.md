# Contributing / 贡献指南

Thank you for considering a contribution to **ZCLUM Prism OCR**.

感谢你愿意参与 **ZCLUM 光棱 OCR**。这个项目关注 PDF OCR、Markdown 排版、RAG 检索与智能体平台接入。

## Good First Contributions

- Fix documentation or translation issues.
- Add OCR engine installation notes.
- Improve frontend interaction states.
- Add RAG ranking experiments.
- Add deployment examples.
- Add test PDFs with clear expected Markdown output.

## Development Setup

```powershell
python -m pip install -r requirements-web.txt
python -m pip install -r requirements-rag.txt
cd frontend
npm install
npm run build
```

## Pull Request Checklist

- Keep changes focused and minimal.
- Do not commit API keys, provider URLs with secrets, private documents, or generated runtime data.
- Update documentation when behavior changes.
- Run relevant tests or explain why tests were not run.
- For frontend changes, ensure desktop and mobile layouts do not overflow.

## Issue Reports

Please include:

- operating system,
- Python and Node.js versions,
- OCR engine used,
- sample error message,
- whether the file is a native PDF or scanned PDF.


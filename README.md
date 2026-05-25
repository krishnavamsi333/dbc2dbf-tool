---
title: DBC to DBF Converter
emoji: 🔌
colorFrom: green
colorTo: gray
sdk: docker
pinned: false
---

# DBC → DBF Converter

Convert Vector **DBC** (CAN database) files to BUSMASTER **DBF** format.  
Includes a REST API, drag-and-drop web UI, and a CLI tool.

---
https://dbc2dbf-tool.onrender.com/
## Features

- **Auto-sanitize** — fixes encoding issues, bad line endings, malformed syntax before converting
- **Validation** — reports message/signal counts and common structural warnings
- **REST API** — integrate into any pipeline
- **Web UI** — drag-and-drop, no installation needed for end users
- **CLI** — scriptable for batch processing

---

## Project Structure

```
dbc2dbf-tool/
├── backend/
│   ├── app.py          # FastAPI REST API
│   ├── converter.py    # Core DBC → DBF logic (canmatrix)
│   ├── cleaner.py      # DBC sanitizer
│   ├── validator.py    # File validation
│   └── requirements.txt
├── frontend/
│   ├── index.html      # Web UI
│   ├── style.css
│   └── script.js
├── Dockerfile          # HuggingFace Spaces / Docker deployment
├── docs/
│   ├── API.md
│   └── BUSMASTER_NOTES.md
└── tests/
    ├── sample.dbc
    └── output.dbf
```

---

## Local Setup

```bash
git clone https://huggingface.co/spaces/krishnavamsi333/dbc2dbf-tool
cd dbc2dbf-tool

python -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
python backend/app.py
# open http://localhost:7860
```

---

## API Endpoints

| Method | Endpoint        | Description                        |
|--------|-----------------|------------------------------------|
| GET    | `/health`       | Service health check               |
| POST   | `/api/validate` | Validate a DBC file                |
| POST   | `/api/convert`  | Convert DBC → DBF (returns file)   |

See [docs/API.md](docs/API.md) for full reference.

---

## License

MIT

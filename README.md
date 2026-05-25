# DBC → DBF Converter

Convert Vector **DBC** (CAN database) files to BUSMASTER **DBF** format.  
Includes a REST API, drag-and-drop web UI, and a CLI tool.

---

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
│   ├── app.py          # Flask REST API
│   ├── converter.py    # Core DBC → DBF logic (canmatrix)
│   ├── cleaner.py      # DBC sanitizer
│   ├── validator.py    # File validation
│   └── requirements.txt
├── frontend/
│   ├── index.html      # Web UI
│   ├── style.css
│   └── script.js
├── docker/
│   └── Dockerfile
├── docs/
│   ├── API.md
│   └── BUSMASTER_NOTES.md
└── tests/
    ├── sample.dbc
    └── output.dbf
```

---

## Setup

### Requirements

- Python 3.9+
- pip

### Install

```bash
git clone https://github.com/youruser/dbc2dbf-tool.git
cd dbc2dbf-tool

python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r backend/requirements.txt
```

---

## Usage

### 1. Web UI + API (recommended)

```bash
cd dbc2dbf-tool
source venv/bin/activate
python backend/app.py
```

Then open `frontend/index.html` in your browser (or serve it with any static server).

The API runs at `http://localhost:5000`.

---

### 2. CLI

```bash
# Basic conversion
python backend/converter.py input.dbc output.dbf

# With auto-sanitize
python backend/converter.py input.dbc output.dbf --clean
```

---

### 3. Docker

```bash
docker build -t dbc2dbf -f docker/Dockerfile .
docker run -p 5000:5000 dbc2dbf
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

## Environment Variables

| Variable      | Default | Description                     |
|---------------|---------|---------------------------------|
| `PORT`        | `5000`  | API server port                 |
| `FLASK_DEBUG` | `false` | Enable Flask debug mode         |

---

## Dependencies

- [canmatrix](https://github.com/ebroecker/canmatrix) — DBC/DBF parsing and conversion
- [Flask](https://flask.palletsprojects.com/) — REST API framework
- [flask-cors](https://flask-cors.readthedocs.io/) — CORS support

---

## License

MIT
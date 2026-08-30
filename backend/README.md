# IT Support Assistant — Backend (Python / FastAPI)

## Setup

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env   # then fill in values
```

## Run

The FastAPI equivalent of `dev` / `build` / `start`:

- **dev** (auto-reload): `uvicorn app.main:app --reload --port 8000`
- **build**: no build step for Python (nothing to compile)
- **start** (production): `uvicorn app.main:app --host 0.0.0.0 --port 8000`

## Health check

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

FastAPI parses JSON request bodies automatically, and CORS is enabled via
`CORSMiddleware` in `app/main.py`.

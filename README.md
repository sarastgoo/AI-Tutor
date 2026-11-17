# AI English Tutor

Local-first, bilingual (English/Persian), adaptive AI English tutor built on scanned textbooks.

**Status:** P1 (Foundation) in progress  
**Target environment:** Windows 11, 24 GB RAM, NVIDIA RTX 3050 Laptop 6 GB  
**Offline:** Yes, after initial model downloads.

## Quick Start

### Prerequisites

- Windows 11
- Python 3.12.10 (Microsoft Store)
- Docker Desktop (for PostgreSQL only)
- Ollama (native Windows, running on port 11434)
- Node.js 20+ and npm

### First-time setup

```powershell
# 1. Clone or navigate to the repo
cd C:\Projects\ai-english-tutor

# 2. Create Python venv (if not exists)
python3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-dev.txt

# 3. Copy .env.example to .env and adjust
Copy-Item .env.example .env

# 4. Start PostgreSQL
docker compose up -d db

# 5. Run migrations
cd backend
..\.venv\Scripts\python.exe -m alembic upgrade head
cd ..

# 6. Start backend
cd backend
..\.venv\Scripts\uvicorn.exe app.main:app --reload --port 8000
# In another terminal:
# 7. Start frontend
cd frontend
npm install
npm run dev
# PDF Summarizer

A full-stack app that lets authenticated users upload a PDF and get an AI-generated summary using **T5-small**.

## Stack

| Layer     | Tech |
|-----------|------|
| Backend   | FastAPI + Uvicorn |
| ML model  | T5-small (HuggingFace Transformers) |
| Database  | PostgreSQL (Render) / SQLite (local) |
| Auth      | JWT (python-jose) + bcrypt passwords |
| Frontend  | Vanilla HTML/CSS/JS (static) |
| Deploy    | Render (web service + static site + PostgreSQL) |

---

## Project Structure

```
pdf-summarizer/
├── backend/
│   ├── __init__.py
│   ├── main.py        # FastAPI app, lifespan startup
│   ├── database.py    # SQLAlchemy engine + session
│   ├── models.py      # User + SummaryLog ORM models
│   ├── seed.py        # Seeds 5 users on first startup
│   ├── auth.py        # /auth/login + JWT helpers
│   └── summarize.py   # /api/summarize (T5-small)
├── frontend/
│   └── index.html     # Single-page app (login + upload + result)
├── requirements.txt
├── Procfile
├── render.yaml
└── README.md
```

---

## Demo Users (seeded automatically)

| Username | Password     |
|----------|-------------|
| alice    | alice123    |
| bob      | bob456      |
| charlie  | charlie789  |
| diana    | diana321    |
| eve      | eve654      |

---

## Run Locally

### 1. Clone and install
```bash
git clone https://github.com/YOUR_USERNAME/pdf-summarizer.git
cd pdf-summarizer
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Start the backend
```bash
uvicorn backend.main:app --reload --port 8000
```

- API docs: http://localhost:8000/docs
- On first start, tables are created and 5 users are seeded into SQLite (`local.db`).

### 3. Open the frontend
Open `frontend/index.html` in your browser (double-click, or use a live server).

> Make sure `API_BASE` in `index.html` is `http://localhost:8000` (it is by default when hostname is localhost).

---

## Deploy on Render

### Step 1 — Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/pdf-summarizer.git
git push -u origin main
```

### Step 2 — Create PostgreSQL database on Render
1. Go to https://render.com → New → **PostgreSQL**
2. Name it `pdf-summarizer-db`
3. Choose the **Free** plan
4. Click **Create Database**
5. Copy the **Internal Database URL** (used in next step)

### Step 3 — Deploy the Backend (Web Service)
1. New → **Web Service**
2. Connect your GitHub repo
3. Settings:
   - **Name**: `pdf-summarizer-api`
   - **Runtime**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Standard (T5-small needs ~500 MB RAM; free plan may OOM)
4. Environment Variables:
   - `DATABASE_URL` → paste the Internal Database URL from Step 2
   - `SECRET_KEY` → any long random string (e.g. generate with `openssl rand -hex 32`)
5. Click **Create Web Service**
6. Wait for deploy. Note the URL: `https://pdf-summarizer-api.onrender.com`

### Step 4 — Update Frontend API URL
In `frontend/index.html`, find this line and update with your actual backend URL:
```js
: "https://pdf-summarizer-api.onrender.com"; // ← UPDATE THIS AFTER DEPLOY
```

Commit and push:
```bash
git add frontend/index.html
git commit -m "Set production API URL"
git push
```

### Step 5 — Deploy the Frontend (Static Site)
1. New → **Static Site**
2. Connect same GitHub repo
3. Settings:
   - **Name**: `pdf-summarizer-frontend`
   - **Publish Directory**: `frontend`
   - **Build Command**: leave empty
4. Click **Create Static Site**

---

## How the T5 Window Works

T5-small has a **512-token** input limit. To keep things well within bounds:

- We take the **first 1,800 characters** of extracted PDF text (`MAX_INPUT_CHARS`)
- The input is prefixed with `"summarize: "` (T5 instruction prefix)
- Tokenized and passed to `model.generate()` with `max_new_tokens=200`
- If the PDF has more text, a `"truncated": true` flag is returned in the response

This is intentionally simple — in a real app you'd chunk the document and summarize recursively.

---

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/login` | No | Get JWT token |
| GET | `/auth/me` | Yes | Get current user |
| POST | `/api/summarize` | Yes | Upload PDF → get summary |
| GET | `/health` | No | Health check |

Full interactive docs at `/docs` (Swagger UI).

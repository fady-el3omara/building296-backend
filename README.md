# Building 296 Backend (FastAPI + SQLite) — v5 (GitHub-ready)

Complete backend for Building 296: rents, expenses, owner distribution, variance, wallets, and Excel reports.

## Features
- Forecast distribution and variance, saved in DB
- Owner wallets with running balances (auto-updated on forecast/variance)
- Export monthly Excel reports (`/reports/export/{month}`) and download (`/reports/download/{month}`)
- Export owner wallet ledger (`/wallets/export/{ownerId}/{month}`)

## Run locally
```bash
cd building296-backend/backend
python -m venv .venv
# Windows: .venv\Scripts\activate
. .venv/bin/activate
pip install -r requirements.txt

# (Re)create DB schema and import Excel (already included)
python import_from_excel.py ../data/"296_Shoubra_Phase2_Visual_Light (1).xlsx" ../schema/building296.db

# start API
uvicorn main:app --reload
```
Open: http://127.0.0.1:8000/docs

## Deploy on Render (free)
- Push this repo to GitHub.
- Go to https://render.com → New → Web Service → connect your repo.
- Render will detect `render.yaml` and auto-deploy.
- Your live docs: `https://<your-app>.onrender.com/docs`

from fastapi import FastAPI, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from .database import SessionLocal
from . import crud
from .reports_export import export_month_report
from .wallets_export import export_wallet_ledger
import os

app = FastAPI(title="Building 296 — Backend API (v6)")
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/owners")
def owners(db: Session = Depends(get_db)):
    return crud.list_owners(db)

@app.get("/rents/{month}")
def rents(month: str, db: Session = Depends(get_db)):
    return crud.list_rents_by_month(db, month)

@app.get("/forecast/{month}")
def forecast_total(month: str, db: Session = Depends(get_db)):
    return {"month": month, "expectedRevenue": crud.expected_revenue(db, month)}

@app.post("/forecast/distribution/{month}")
def forecast_distribution(month: str, db: Session = Depends(get_db)):
    return crud.generate_expected_distribution(db, month)

@app.post("/variance/{month}")
def variance(month: str, db: Session = Depends(get_db)):
    return crud.generate_variance(db, month)

@app.post("/reports/export/{month}")
def export_report(month: str):
    path, owners_count = export_month_report("../schema/building296.db", month, out_dir="reports")
    return {"status": "ok", "file": path, "owners": owners_count}

@app.get("/reports/download/{month}")
def download_report(month: str):
    file_path = f"reports/Building296_Report_{month}.xlsx"
    if not os.path.exists(file_path):
        return {"error": f"Report not found for {month}. Please run /reports/export/{month} first."}
    return FileResponse(path=file_path, filename=os.path.basename(file_path), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@app.get("/wallets/{ownerId}/{month}")
def get_wallet(ownerId: int, month: str, db: Session = Depends(get_db)):
    entries, balance, prior_balance = crud.wallet_entries(db, ownerId, month)
    return {"ownerId": ownerId, "month": month, "priorBalance": prior_balance, "entries": entries, "endingBalance": balance}

@app.post("/wallets/export/{ownerId}/{month}")
def export_wallet(ownerId: int, month: str):
    path = export_wallet_ledger("../schema/building296.db", ownerId, month, out_dir="reports")
    if not path:
        return {"error": "Nothing to export (no entries for that owner/month)."}
    return {"status": "ok", "file": path}
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
from fastapi import UploadFile, File
import pandas as pd
from backend.database import init_db, SessionLocal
from backend.import_from_excel import import_excel_data

# Initialize DB once
init_db()

@app.post("/import_excel")
async def import_excel(file: UploadFile = File(...)):
    """Upload and import Excel data into the database"""
    # Read the uploaded file into pandas
    contents = await file.read()
    df = pd.read_excel(contents)

    # Use your helper function to insert into DB
    db = SessionLocal()
    import_excel_data(df, db)
    db.close()

    return {"status": "success", "rows_imported": len(df)}

def read_root():
    return {"message": "Building 296 backend is live!"}

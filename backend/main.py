from fastapi import FastAPI, Depends, UploadFile, File, HTTPException, Header
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
import pandas as pd
import os

# Local imports
from .database import SessionLocal
from . import crud
from .reports_export import export_month_report, calculate_owner_shares
from .wallets_export import export_wallet_ledger
from .import_from_excel import import_excel_data

# --- App Initialization ---
app = FastAPI(title="Building 296 – Backend API (Secure)")

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Auth Configuration ---
API_KEY = os.getenv("IMPORT_API_KEY", "changeme123")  # Set this in Render env vars

def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden: Invalid API key")


# --- Excel Import Endpoint (Protected) ---
@app.post("/import-excel")
async def import_excel(
    file: UploadFile = File(...),
    _: str = Depends(verify_api_key)
):
    """
    Upload and import Excel data into the database.
    Protected by API key header: X-API-Key
    """
    contents = await file.read()
    df = pd.read_excel(contents)

    db = SessionLocal()
    import_excel_data(df, db)
    db.close()

    return {"status": "success", "rows_imported": len(df)}


# --- Owner Revenue Distribution ---
@app.get("/owners_distribution")
def owners_distribution():
    db = SessionLocal()
    result = calculate_owner_shares(db)
    db.close()
    return result


# --- Export Monthly Report ---
@app.get("/export_month_report")
def export_month_report_endpoint():
    file_path = export_month_report()
    return FileResponse(file_path, filename="month_report.xlsx")


# --- Export Wallet Ledger ---
@app.get("/export_wallet_ledger")
def export_wallet_ledger_endpoint():
    file_path = export_wallet_ledger()
    return FileResponse(file_path, filename="wallet_ledger.xlsx")


# --- Root Endpoint ---
@app.get("/")
def read_root():
    return {"message": "Building 296 backend is live and secured!"}


# --- Root Endpoint ---
@app.get("/")
def read_root():
    return {"message": "Building 296 backend is live!"}

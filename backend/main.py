from fastapi import FastAPI, Depends
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
import os

# Local imports
from .database import SessionLocal
from . import crud
from .reports_export import export_month_report, calculate_owner_shares
from .wallets_export import export_wallet_ledger
from .import_from_excel import import_excel_data

# --- App Initialization ---
app = FastAPI(title="Building 296 – Backend API (v6)")

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Excel Import Endpoint ---
@app.post("/import-excel")
def import_excel(month: str):
    """
    Import Excel data from the predefined file into the database.
    """
    db = SessionLocal()
    summary = import_excel_data(
        db,
        month=month,
        file_path="backend/data/296_Shoubra_Phase2_Visual_Light (1).xlsx"
    )
    db.close()
    return {"ok": True, "summary": summary}

# --- Owner Revenue Distribution Endpoint ---
@app.get("/owners_distribution")
def owners_distribution():
    """
    Return expected owner revenue distribution assuming all tenants paid.
    """
    db = SessionLocal()
    result = calculate_owner_shares(db)
    db.close()
    return result

# --- Export Monthly Report Endpoint ---
@app.get("/export_month_report")
def export_month_report_endpoint():
    """
    Export the monthly report as an Excel file.
    """
    file_path = export_month_report()
    return FileResponse(file_path, filename="month_report.xlsx")

# --- Export Wallet Ledger Endpoint ---
@app.get("/export_wallet_ledger")
def export_wallet_ledger_endpoint():
    """
    Export wallet ledger as an Excel file.
    """
    file_path = export_wallet_ledger()
    return FileResponse(file_path, filename="wallet_ledger.xlsx")

# --- Root Endpoint ---
@app.get("/")
def read_root():
    return {"message": "Building 296 backend is live!"}


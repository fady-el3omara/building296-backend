from fastapi import FastAPI, Depends, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
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
from .auth import create_access_token, get_current_admin, Token


# --- App Initialization ---
app = FastAPI(title="Building 296 – Backend API (v6)")


# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict to your admin frontend domain later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- LOGIN ROUTE (JWT Auth) ---
@app.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login endpoint to authenticate admin and return a JWT token.
    """
    if form_data.username != "admin" or form_data.password != "296admin":
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}


# --- Excel Import Endpoint (PROTECTED) ---
@app.post("/import-excel")
async def import_excel(
    file: UploadFile = File(...),
    current_admin: dict = Depends(get_current_admin)
):
    """
    Upload and import Excel data into the database.
    Protected by JWT authentication.
    """
    contents = await file.read()

    try:
        df = pd.read_excel(contents)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid Excel file: {e}")

    db = SessionLocal()
    try:
        import_excel_data(df, db)
        db.close()
        return {"status": "success", "rows_imported": len(df)}
    except Exception as e:
        db.close()
        raise HTTPException(status_code=500, detail=f"Database import failed: {e}")


# --- Owner Revenue Distribution (PUBLIC) ---
@app.get("/owners_distribution")
def owners_distribution():
    """
    Return expected owner revenue distribution assuming all tenants paid.
    Publicly accessible.
    """
    db = SessionLocal()
    result = calculate_owner_shares(db)
    db.close()
    return result


# --- Export Monthly Report (PUBLIC) ---
@app.get("/export_month_report")
def export_month_report_endpoint():
    """
    Export the monthly report as an Excel file.
    Publicly accessible.
    """
    file_path = export_month_report()
    return FileResponse(file_path, filename="month_report.xlsx")


# --- Export Wallet Ledger (PUBLIC) ---
@app.get("/export_wallet_ledger")
def export_wallet_ledger_endpoint():
    """
    Export wallet ledger as an Excel file.
    Publicly accessible.
    """
    file_path = export_wallet_ledger()
    return FileResponse(file_path, filename="wallet_ledger.xlsx")


# --- Root Endpoint ---
@app.get("/")
def read_root():
    return {"message": "Building 296 backend is live!"}

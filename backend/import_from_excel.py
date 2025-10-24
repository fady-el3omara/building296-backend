from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple, Any
from pathlib import Path
from datetime import datetime

import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import text

# Default location on the server
DEFAULT_EXCEL_PATH = "backend/data/latest.xlsx"


# ----------------------------
# Utilities
# ----------------------------

def _now_iso() -> str:
    return datetime.utcnow().isoformat()


def _clean_header(h: str) -> str:
    return (
        str(h or "")
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
    )


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [_clean_header(c) for c in df.columns]
    return df


def _require_cols(df: pd.DataFrame, required: List[str], sheet: str):
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(
            f"[{sheet}] Missing required columns: {missing}. "
            f"Found: {list(df.columns)}"
        )


def _coalesce_number(val: Any) -> float:
    if pd.isna(val):
        return 0.0
    try:
        return float(val)
    except Exception:
        return 0.0


def _coalesce_int(val: Any) -> int:
    if pd.isna(val) or val == "":
        return 0
    try:
        return int(val)
    except Exception:
        try:
            return int(float(val))
        except Exception:
            return 0


def _coalesce_str(val: Any) -> str:
    if pd.isna(val):
        return ""
    return str(val).strip()


# ----------------------------
# Sheet mappers
# ----------------------------

@dataclass
class SheetSpec:
    # canonical column names your DB expects
    required: List[str]
    # alias map: incoming -> canonical
    aliases: Dict[str, str]
    # insert SQL (named params must match canonical)
    insert_sql: str
    # delete SQL for overwrite behavior
    delete_sql: str
    # whether the sheet is month-scoped
    monthly: bool


SHEETS: Dict[str, SheetSpec] = {
    # Global owner shares (overwrites all)
    "owners_shares": SheetSpec(
        required=["ownerid", "name", "shareheld"],
        aliases={
            "owner_id": "ownerid",
            "owner": "name",
            "owner_name": "name",
            "share": "shareheld",
            "share_held": "shareheld",
            "shares": "shareheld",
        },
        insert_sql=(
            "INSERT INTO owners (ownerId, name, shareHeld) "
            "VALUES (:ownerid, :name, :shareheld)"
        ),
        delete_sql="DELETE FROM owners",
        monthly=False,
    ),

    # Units / Rents definition per month (effective rent etc.)
    "units_rents": SheetSpec(
        required=["month", "unitid", "tenantname", "effectiverent", "paidamount"],
        aliases={
            "unit_id": "unitid",
            "unit": "unitid",
            "tenant": "tenantname",
            "tenant_name": "tenantname",
            "effective_rent": "effectiverent",
            "paid": "paidamount",
            "paid_amount": "paidamount",
        },
        insert_sql=(
            "INSERT INTO rents (month, unitId, tenantName, effectiveRent, paidAmount) "
            "VALUES (:month, :unitid, :tenantname, :effectiverent, :paidamount)"
        ),
        delete_sql="DELETE FROM rents WHERE month=:month",
        monthly=True,
    ),

    # Bills (shared building bills)
    "bills": SheetSpec(
        required=["month", "billtype", "amount"],
        aliases={
            "bill_type": "billtype",
            "type": "billtype",
            "value": "amount",
        },
        insert_sql=(
            "INSERT INTO bills (month, billType, amount) "
            "VALUES (:month, :billtype, :amount)"
        ),
        delete_sql="DELETE FROM bills WHERE month=:month",
        monthly=True,
    ),

    # Expenses (shared + owner-specific)
    "expenses": SheetSpec(
        required=["month", "description", "amount", "ownerspecific", "chargedowner"],
        aliases={
            "desc": "description",
            "owner_specific": "ownerspecific",
            "owner_specific_flag": "ownerspecific",
            "charged_owner": "chargedowner",
            "ownerid": "chargedowner",
            "owner_id": "chargedowner",
            "value": "amount",
        },
        insert_sql=(
            "INSERT INTO expenses (month, description, amount, ownerSpecific, chargedOwner) "
            "VALUES (:month, :description, :amount, :ownerspecific, :chargedowner)"
        ),
        delete_sql="DELETE FROM expenses WHERE month=:month",
        monthly=True,
    ),

    # Owner allowances (credits)
    "owner_allowance": SheetSpec(
        required=["month", "ownerid", "allowancevalue"],
        aliases={
            "owner_id": "ownerid",
            "allowance_value": "allowancevalue",
            "value": "allowancevalue",
        },
        insert_sql=(
            "INSERT INTO owner_allowances (month, ownerId, allowanceValue) "
            "VALUES (:month, :ownerid, :allowancevalue)"
        ),
        delete_sql="DELETE FROM owner_allowances WHERE month=:month",
        monthly=True,
    ),

    # Revenue distribution (the main objective, per owner per month)
    "revenue_distribution": SheetSpec(
        required=["month", "ownerid", "expectedrent", "expectedexpenses", "expectednet"],
        aliases={
            "owner_id": "ownerid",
            "expected_rent": "expectedrent",
            "expected_expenses": "expectedexpenses",
            "expected_net": "expectednet",
            # accept 'actualnet' if provided (optional)
            "actual_net": "actualnet",
        },
        insert_sql=(
            "INSERT INTO revenue_distribution "
            "(month, ownerId, expectedRent, expectedExpenses, expectedNet, generatedOn) "
            "VALUES (:month, :ownerid, :expectedrent, :expectedexpenses, :expectednet, :generatedon)"
        ),
        delete_sql="DELETE FROM revenue_distribution WHERE month=:month",
        monthly=True,
    ),
}


def _apply_aliases(df: pd.DataFrame, spec: SheetSpec) -> pd.DataFrame:
    rename_map = {}
    for col in list(df.columns):
        # already canonical
        if col in spec.required:
            continue
        # alias -> canonical
        if col in spec.aliases:
            rename_map[col] = spec.aliases[col]
    if rename_map:
        df = df.rename(columns=rename_map)
    return df


def _prepare_values(spec: SheetSpec, row: Dict[str, Any]) -> Dict[str, Any]:
    # Casts and defaults per sheet
    r: Dict[str, Any] = {}

    # Common: month
    if spec.monthly:
        r["month"] = _coalesce_str(row.get("month"))

    # Owners_Shares
    if spec is SHEETS["owners_shares"]:
        r["ownerid"] = _coalesce_int(row.get("ownerid"))
        r["name"] = _coalesce_str(row.get("name"))
        r["shareheld"] = float(row.get("shareheld") or 0.0)

    # Units_Rents
    elif spec is SHEETS["units_rents"]:
        r["unitid"] = _coalesce_str(row.get("unitid"))
        r["tenantname"] = _coalesce_str(row.get("tenantname"))
        r["effectiverent"] = _coalesce_number(row.get("effectiverent"))
        r["paidamount"] = _coalesce_number(row.get("paidamount"))

    # Bills
    elif spec is SHEETS["bills"]:
        r["billtype"] = _coalesce_str(row.get("billtype"))
        r["amount"] = _coalesce_number(row.get("amount"))

    # Expenses
    elif spec is SHEETS["expenses"]:
        r["description"] = _coalesce_str(row.get("description"))
        r["amount"] = _coalesce_number(row.get("amount"))
        # ownerSpecific as 0/1
        os_flag = row.get("ownerspecific")
        if isinstance(os_flag, str):
            os_flag = os_flag.strip().lower() in {"1", "y", "yes", "true", "t"}
        r["ownerspecific"] = 1 if bool(os_flag) else 0
        r["chargedowner"] = _coalesce_int(row.get("chargedowner"))

    # Owner_Allowance
    elif spec is SHEETS["owner_allowance"]:
        r["ownerid"] = _coalesce_int(row.get("ownerid"))
        r["allowancevalue"] = _coalesce_number(row.get("allowancevalue"))

    # Revenue_Distribution
    elif spec is SHEETS["revenue_distribution"]:
        r["ownerid"] = _coalesce_int(row.get("ownerid"))
        r["expectedrent"] = _coalesce_number(row.get("expectedrent"))
        r["expectedexpenses"] = _coalesce_number(row.get("expectedexpenses"))
        r["expectednet"] = _coalesce_number(row.get("expectednet"))
        r["generatedon"] = _now_iso()

    return r


def _delete_existing(db: Session, spec: SheetSpec, month: str | None):
    if spec.monthly:
        db.execute(text(spec.delete_sql), {"month": month})
    else:
        db.execute(text(spec.delete_sql))


def _insert_rows(db: Session, spec: SheetSpec, rows: List[Dict[str, Any]]):
    for vals in rows:
        db.execute(text(spec.insert_sql), vals)


# ----------------------------
# Public entry point
# ----------------------------

def import_excel_data(db: Session, month: str, file_path: str = DEFAULT_EXCEL_PATH) -> Dict[str, Any]:
    """
    Import data from the Excel workbook at `file_path` into the database,
    overwriting rows for the provided `month` (for monthly sheets) or the whole
    table (for global sheets like Owners_Shares).

    Returns a summary dict: { sheet_name: {inserted: int, deleted: int} }
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Excel file not found at: {file_path}")

    wb = pd.ExcelFile(path)

    summary: Dict[str, Dict[str, int]] = {}

    for raw_sheet_name, spec in SHEETS.items():
        # Match ignoring case & spaces/underscores
        candidates = [s for s in wb.sheet_names if _clean_header(s) == raw_sheet_name]
        if not candidates:
            # Sheet not present; skip silently (but record zeroes)
            summary[raw_sheet_name] = {"inserted": 0, "deleted": 0}
            continue

        sheet_name = candidates[0]
        df = pd.read_excel(wb, sheet_name=sheet_name, dtype=object)
        if df.empty:
            summary[raw_sheet_name] = {"inserted": 0, "deleted": 0}
            continue

        df = _normalize_columns(df)
        df = _apply_aliases(df, spec)

        _require_cols(df, spec.required, sheet_name)

        # Overwrite behavior
        _delete_existing(db, spec, month if spec.monthly else None)
        deleted = 0  # Render/Postgres doesn’t return deleted count easily without RETURNING
        # We can’t rely on rowcount cross-DB; keep it as 0 or compute separately if needed.

        # Prepare rows
        out_rows: List[Dict[str, Any]] = []
        for _, row in df.iterrows():
            vals = _prepare_values(spec, row.to_dict())
            # enforce month binding for monthly sheets (override whatever is in file to the API month)
            if spec.monthly:
                vals["month"] = month
            out_rows.append(vals)

        _insert_rows(db, spec, out_rows)
        db.commit()

        summary[raw_sheet_name] = {"inserted": len(out_rows), "deleted": deleted}

    return summary

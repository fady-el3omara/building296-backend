import sys
import pandas as pd
import sqlite3
from pathlib import Path

SCHEMA_SQL = Path(__file__).resolve().parent.parent / "schema" / "schema.sql"

def _normalize_cols(df):
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    return df

def import_from_excel(xlsx_path: str, db_path: str):
    xls = pd.ExcelFile(xlsx_path)
    conn = sqlite3.connect(db_path)
    try:
        with open(SCHEMA_SQL, "r", encoding="utf-8") as f:
            conn.executescript(f.read())

        # Owners_Shares
        if "Owners_Shares" in xls.sheet_names:
            df = _normalize_cols(pd.read_excel(xls, "Owners_Shares"))
            name_col = next((c for c in df.columns if "owner" in c and ("name" in c or c=="owner")), None)
            share_col = next((c for c in df.columns if "share" in c), None)
            if name_col and share_col:
                out = pd.DataFrame({"name": df[name_col], "shareHeld": pd.to_numeric(df[share_col], errors="coerce").fillna(0)})
                out = out.dropna(subset=["name"])
                out.to_sql("owners", conn, if_exists="append", index=False)

        # Units_Rents
        if "Units_Rents" in xls.sheet_names:
            dfu = _normalize_cols(pd.read_excel(xls, "Units_Rents"))
            month_c = next((c for c in dfu.columns if c in ["month","months"]), None)
            unit_c = next((c for c in dfu.columns if "unit" in c and ("number" in c or c=="unit")), None)
            tenant_c = next((c for c in dfu.columns if "tenant" in c), None)
            base_rent_c = next((c for c in dfu.columns if "base" in c and "rent" in c or c=="base_rent"), None)
            eff_rent_c = next((c for c in dfu.columns if "effective" in c and "rent" in c or c=="effective_rent"), None)
            paid_amount_c = next((c for c in dfu.columns if "paid" in c and "amount" in c or c=="paid_amount"), None)

            units = pd.DataFrame()
            units["unitNumber"] = dfu.get(unit_c, pd.Series([f"U{i+1}" for i in range(len(dfu))])).astype(str)
            units["tenantName"] = dfu.get(tenant_c, None)
            units["baseRent"] = pd.to_numeric(dfu.get(base_rent_c, 0), errors="coerce").fillna(0)
            units["status"] = "Active"
            units = units.drop_duplicates(subset=["unitNumber"])
            units.to_sql("units", conn, if_exists="append", index=False)

            umap = pd.read_sql_query("SELECT unitId, unitNumber FROM units", conn).set_index("unitNumber")["unitId"].to_dict()

            rents = pd.DataFrame()
            rents["month"] = dfu.get(month_c, "").astype(str)
            rents["unitId"] = dfu.get(unit_c, "").astype(str).map(umap)
            rents["effectiveRent"] = pd.to_numeric(dfu.get(eff_rent_c, dfu.get(base_rent_c, 0)), errors="coerce").fillna(0)
            rents["paidAmount"] = pd.to_numeric(dfu.get(paid_amount_c, 0), errors="coerce").fillna(0)
            rents["discount"] = 0.0
            rents["arrearsBF"] = 0.0
            rents["status"] = "Pending"
            rents = rents.dropna(subset=["unitId"])
            rents.to_sql("rents", conn, if_exists="append", index=False)

        # Expenses
        if "Expenses" in xls.sheet_names:
            dfe = _normalize_cols(pd.read_excel(xls, "Expenses"))
            date_c = next((c for c in dfe.columns if "date" in c), None)
            month_c = next((c for c in dfe.columns if c in ["month","months"]), None)
            desc_c = next((c for c in dfe.columns if "desc" in c or c=="description"), None)
            amount_c = next((c for c in dfe.columns if "amount" in c or c=="value"), None)
            owner_spec_c = next((c for c in dfe.columns if "owner_specific" in c or "owner specific" in c), None)
            charged_owner_c = next((c for c in dfe.columns if "charged" in c and "owner" in c), None)
            type_c = next((c for c in dfe.columns if c=="type" or "category" in c), None)

            out = pd.DataFrame()
            out["date"] = dfe.get(date_c, "")
            out["month"] = dfe.get(month_c, "")
            out["description"] = dfe.get(desc_c, dfe.columns[:1])
            out["amount"] = pd.to_numeric(dfe.get(amount_c, 0), errors="coerce").fillna(0)
            out["recurring"] = 0
            out["ownerSpecific"] = dfe.get(owner_spec_c, 0)
            out["chargedOwner"] = dfe.get(charged_owner_c, None)
            out["type"] = dfe.get(type_c, None)
            out["notes"] = None
            out.to_sql("expenses", conn, if_exists="append", index=False)

        # Owner_Allowance
        if "Owner_Allowance" in xls.sheet_names:
            dfa = _normalize_cols(pd.read_excel(xls, "Owner_Allowance"))
            month_c = next((c for c in dfa.columns if c in ["month","months"]), None)
            owner_c = next((c for c in dfa.columns if "owner" in c), None)
            value_c = next((c for c in dfa.columns if "allowance" in c or "value" in c or "amount" in c), None)

            odf = pd.read_sql_query("SELECT ownerId, name FROM owners", conn)
            omap = dict(zip(odf["name"].str.lower(), odf["ownerId"]))

            out = pd.DataFrame()
            out["month"] = dfa.get(month_c, "")
            names = dfa.get(owner_c, "").astype(str).str.lower()
            out["ownerId"] = names.map(omap)
            out["allowanceValue"] = pd.to_numeric(dfa.get(value_c, 0), errors="coerce").fillna(0)
            out["notes"] = None
            out = out.dropna(subset=["ownerId"])
            out.to_sql("owner_allowances", conn, if_exists="append", index=False)

        conn.commit()
        return True, "Import completed."
    except Exception as e:
        conn.rollback()
        return False, f"Import failed: {e}"
    finally:
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python import_from_excel.py <excel_path> <sqlite_db_path>")
        sys.exit(1)
    ok, msg = import_from_excel(sys.argv[1], sys.argv[2])
    print(msg)

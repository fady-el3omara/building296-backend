import pandas as pd
from sqlalchemy.orm import Session
from . import crud

def import_excel_data(df: pd.DataFrame, db: Session):
    """
    Imports rent, owner, or expense data from a DataFrame into the database.
    Adjust this logic based on the structure of your Excel file.
    """
    # Example: detect which sheet/data structure it is
    if "rents" in df.columns:
        for _, row in df.iterrows():
            db.execute("""
                INSERT OR REPLACE INTO rents (tenantId, ownerId, month, effectiveRent, paidAmount)
                VALUES (:tid, :oid, :m, :er, :pa)
            """, {
                "tid": row.get("tenantId"),
                "oid": row.get("ownerId"),
                "m": row.get("month"),
                "er": row.get("effectiveRent", 0),
                "pa": row.get("paidAmount", 0),
            })

    elif "expenses" in df.columns:
        for _, row in df.iterrows():
            db.execute("""
                INSERT INTO expenses (month, description, amount, ownerSpecific, chargedOwner)
                VALUES (:m, :d, :a, :os, :oid)
            """, {
                "m": row.get("month"),
                "d": row.get("description"),
                "a": row.get("amount", 0),
                "os": row.get("ownerSpecific", 0),
                "oid": row.get("chargedOwner"),
            })

    db.commit()
    return {"rows_imported": len(df)}

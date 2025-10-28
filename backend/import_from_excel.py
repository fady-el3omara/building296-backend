import pandas as pd
from sqlalchemy import text
from datetime import datetime

# -----------------------------------------------------------
#  Excel → Database Importer
# -----------------------------------------------------------

def import_excel_data(df_or_file, db):
    """
    Import all Excel sheets into the database.
    Supports overwriting existing month data and ignores summaries.
    """

    # If given an Excel file instead of a DataFrame
    if not isinstance(df_or_file, pd.DataFrame):
        xls = pd.ExcelFile(df_or_file)
        sheet_names = xls.sheet_names
    else:
        raise ValueError("Expected an Excel file, not a single DataFrame.")

    imported_sheets = []
    skipped_sheets = []

    for sheet_name in sheet_names:
        try:
            # Skip obviously summary sheets
            if "summary" in sheet_name.lower() or "dashboard" in sheet_name.lower():
                skipped_sheets.append(sheet_name)
                continue

            df = pd.read_excel(df_or_file, sheet_name=sheet_name)
            if df.empty:
                skipped_sheets.append(sheet_name)
                continue

            df.columns = [str(c).strip().replace(" ", "_") for c in df.columns]
            table_name = sheet_name.strip().lower()

            # Sanitize: only keep columns that have proper names
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            if df.empty:
                skipped_sheets.append(sheet_name)
                continue

            # Overwrite old data for same month if applicable
            if "month" in df.columns:
                months = df["month"].dropna().unique().tolist()
                if months:
                    for m in months:
                        db.execute(text(f"DELETE FROM {table_name} WHERE month=:m"), {"m": str(m)})

            # Try to insert
            df.to_sql(table_name, db.bind, if_exists="append", index=False)
            imported_sheets.append(sheet_name)

        except Exception as e:
            db.rollback()
            skipped_sheets.append(f"{sheet_name} (error: {e})")

    db.commit()

    return {
        "status": "completed",
        "imported_sheets": imported_sheets,
        "skipped_sheets": skipped_sheets,
        "timestamp": datetime.utcnow().isoformat()
    }

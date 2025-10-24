import pandas as pd, sqlite3
from pathlib import Path

def export_month_report(db_path: str, month: str, out_dir: str = "reports"):
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)

    exp = pd.read_sql(
        "SELECT e.ownerId, o.name AS owner, e.expectedRent, e.expectedExpenses, e.expectedNet "
        "FROM expected_distribution e JOIN owners o ON o.ownerId = e.ownerId WHERE e.month = ?",
        conn, params=(month,)
    )
    var = pd.read_sql(
        "SELECT v.ownerId, o.name AS owner, v.expectedNet, v.actualNet, v.variance "
        "FROM variance_report v JOIN owners o ON o.ownerId = v.ownerId WHERE v.month = ?",
        conn, params=(month,)
    )

    path = Path(out_dir) / f"Building296_Report_{month}.xlsx"
    with pd.ExcelWriter(path) as writer:
        exp.to_excel(writer, sheet_name="Expected_Distribution", index=False)
        var.to_excel(writer, sheet_name="Variance_Report", index=False)

    conn.close()
    return str(path), int(exp["ownerId"].nunique()) if not exp.empty else 0
from sqlalchemy.orm import Session
from . import crud

def calculate_owner_shares(db: Session):
    """
    Calculates expected owner revenue distribution assuming all tenants paid.
    Adjust this logic to match your actual owner–tenant structure.
    """
    owners = crud.get_all_owners(db)  # <-- adjust to your own crud function
    tenants = crud.get_all_tenants(db)  # <-- adjust if you track tenants separately

    # Example logic (replace with your real calculation):
    owner_distribution = []
    for owner in owners:
        total_rent = sum([tenant.rent for tenant in tenants if tenant.owner_id == owner.id])
        owner_distribution.append({
            "owner_id": owner.id,
            "owner_name": owner.name,
            "expected_revenue": total_rent
        })

    return {"owners_distribution": owner_distribution}

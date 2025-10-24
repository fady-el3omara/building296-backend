
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime

# ---------- Basic queries ----------

def list_owners(db: Session):
    return db.execute(text("SELECT * FROM owners")).mappings().all()

def list_rents_by_month(db: Session, month: str):
    return db.execute(text("SELECT * FROM rents WHERE month=:m"), {"m": month}).mappings().all()

def _sum(sql: str, db: Session, **params):
    val = db.execute(text(sql), params).scalar()
    return float(val or 0.0)

def expected_revenue(db: Session, month: str) -> float:
    return _sum("SELECT COALESCE(SUM(effectiveRent),0) FROM rents WHERE month=:m", db, m=month)

def total_paid(db: Session, month: str) -> float:
    return _sum("SELECT COALESCE(SUM(paidAmount),0) FROM rents WHERE month=:m", db, m=month)

def total_expenses(db: Session, month: str) -> float:
    return _sum("SELECT COALESCE(SUM(amount),0) FROM expenses WHERE month=:m", db, m=month)

def owner_specific_expenses(db: Session, month: str, owner_id: int) -> float:
    return _sum("SELECT COALESCE(SUM(amount),0) FROM expenses WHERE month=:m AND ownerSpecific=1 AND chargedOwner=:oid", db, m=month, oid=owner_id)

def owner_allowance(db: Session, month: str, owner_id: int) -> float:
    return _sum("SELECT COALESCE(SUM(allowanceValue),0) FROM owner_allowances WHERE month=:m AND ownerId=:oid", db, m=month, oid=owner_id)

def get_owners(db: Session):
    return db.execute(text("SELECT ownerId, name, shareHeld FROM owners ORDER BY ownerId")).mappings().all()

# ---------- Wallet helpers ----------

def _wallet_add(db: Session, owner_id: int, month: str, entry_type: str, description: str, amount: float, direction: str):
    db.execute(text(
        "INSERT INTO owner_wallets (ownerId, month, entryType, description, amount, direction, createdOn) "
        "VALUES (:oid, :m, :t, :d, :a, :dir, :ts)"
    ), {
        "oid": owner_id, "m": month, "t": entry_type, "d": description, "a": amount,
        "dir": direction, "ts": datetime.utcnow().isoformat()
    })

def _wallet_clear_month(db: Session, month: str):
    db.execute(text("DELETE FROM owner_wallets WHERE month=:m"), {"m": month})

def wallet_entries(db: Session, owner_id: int, month: str):
    rows = db.execute(text(
        "SELECT id, ownerId, month, entryType, description, amount, direction, createdOn "
        "FROM owner_wallets WHERE ownerId=:oid AND month=:m ORDER BY createdOn ASC, id ASC"
    ), {"oid": owner_id, "m": month}).mappings().all()
    prior = db.execute(text(
        "SELECT COALESCE(SUM(CASE WHEN direction='in' THEN amount ELSE -amount END),0) "
        "FROM owner_wallets WHERE ownerId=:oid AND (month < :m)"
    ), {"oid": owner_id, "m": month}).scalar() or 0.0
    balance = float(prior)
    enriched = []
    for r in rows:
        delta = r["amount"] if r["direction"] == "in" else -r["amount"]
        balance += delta
        enriched.append({**dict(r), "runningBalance": round(balance, 2)})
    return enriched, round(balance, 2), round(float(prior), 2)

# ---------- Forecast & Variance with wallet auto-update ----------

def generate_expected_distribution(db: Session, month: str):
    db.execute(text("DELETE FROM expected_distribution WHERE month=:m"), {"m": month})
    _wallet_clear_month(db, month)
    db.commit()

    expected_total_rent = expected_revenue(db, month)
    total_exp = total_expenses(db, month)
    distributable = expected_total_rent - total_exp
    owners = get_owners(db)
    total_shares = sum(o["shareHeld"] for o in owners) or 1.0

    rows = []
    for o in owners:
        gross = distributable * (o["shareHeld"] / total_shares)
        o_exp = owner_specific_expenses(db, month, o["ownerId"])
        allow = owner_allowance(db, month, o["ownerId"])
        net = gross - o_exp + allow
        rows.append({"owner": o["name"], "ownerId": o["ownerId"], "expectedRent": round(gross,2), "expectedExpenses": round(o_exp,2), "expectedNet": round(net,2)})
        db.execute(text(
            "INSERT INTO expected_distribution (month, ownerId, expectedRent, expectedExpenses, expectedNet, generatedOn) "
            "VALUES (:m,:oid,:er,:ee,:en,:ts)"
        ), {"m":month,"oid":o["ownerId"],"er":gross,"ee":o_exp,"en":net,"ts":datetime.utcnow().isoformat()})
        if gross != 0: _wallet_add(db, o["ownerId"], month, "distribution_forecast", "Expected distribution", abs(gross), "in")
        if o_exp != 0: _wallet_add(db, o["ownerId"], month, "owner_expense_forecast", "Owner-specific expense (forecast)", abs(o_exp), "out")
        if allow != 0: _wallet_add(db, o["ownerId"], month, "allowance_forecast", "Allowance (forecast)", abs(allow), "in")
    db.commit()
    return rows

def generate_variance(db: Session, month: str):
    db.execute(text("DELETE FROM variance_report WHERE month=:m"), {"m": month})
    db.commit()

    total_paid_amt = total_paid(db, month)
    total_exp = total_expenses(db, month)
    distributable_actual = total_paid_amt - total_exp
    owners = get_owners(db)
    total_shares = sum(o["shareHeld"] for o in owners) or 1.0
    exp_map = {r["ownerId"]: float(r["expectedNet"]) for r in db.execute(text("SELECT ownerId, expectedNet FROM expected_distribution WHERE month=:m"), {"m": month}).mappings().all()}

    results = []
    for o in owners:
        gross_actual = distributable_actual * (o["shareHeld"] / total_shares)
        o_exp = owner_specific_expenses(db, month, o["ownerId"])
        allow = owner_allowance(db, month, o["ownerId"])
        actual_net = gross_actual - o_exp + allow
        expected_net = exp_map.get(o["ownerId"], 0.0)
        var = actual_net - expected_net
        results.append({"owner": o["name"], "expectedNet": round(expected_net,2), "actualNet": round(actual_net,2), "variance": round(var,2)})
        db.execute(text(
            "INSERT INTO variance_report (month, ownerId, expectedNet, actualNet, variance, generatedOn) "
            "VALUES (:m,:oid,:en,:an,:v,:ts)"
        ), {"m":month,"oid":o["ownerId"],"en":expected_net,"an":actual_net,"v":var,"ts":datetime.utcnow().isoformat()})
        if gross_actual != 0: _wallet_add(db, o["ownerId"], month, "distribution_actual", "Actual distribution", abs(gross_actual), "in")
        if o_exp != 0: _wallet_add(db, o["ownerId"], month, "owner_expense_actual", "Owner-specific expense (actual)", abs(o_exp), "out")
        if allow != 0: _wallet_add(db, o["ownerId"], month, "allowance_actual", "Allowance (actual)", abs(allow), "in")
    db.commit()
    return results
from datetime import datetime
from . import crud

def calculate_owner_shares(db):
    """
    Calculate each owner's expected revenue distribution for the most recent month.

    This summarizes what `crud.generate_expected_distribution()` stores,
    but returns a clean JSON-friendly structure for your API endpoint.
    """

    # Determine the most recent month that has rent data
    month_row = db.execute("SELECT DISTINCT month FROM rents ORDER BY month DESC LIMIT 1").fetchone()
    if not month_row:
        return {"message": "No rent data found."}

    month = month_row[0]

    # Generate expected distribution (updates DB + returns computed rows)
    result_rows = crud.generate_expected_distribution(db, month)

    # Also compute high-level totals
    total_expected_rent = crud.expected_revenue(db, month)
    total_expenses = crud.total_expenses(db, month)
    distributable = total_expected_rent - total_expenses

    return {
        "month": month,
        "generated_on": datetime.utcnow().isoformat(),
        "summary": {
            "total_expected_rent": round(total_expected_rent, 2),
            "total_expenses": round(total_expenses, 2),
            "distributable": round(distributable, 2)
        },
        "owners_distribution": result_rows
    }

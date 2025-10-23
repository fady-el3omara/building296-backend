import pandas as pd, sqlite3
from pathlib import Path

def export_wallet_ledger(db_path: str, owner_id: int, month: str, out_dir: str = "reports"):
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)

    oname = pd.read_sql("SELECT name FROM owners WHERE ownerId = ?", conn, params=(owner_id,))
    if oname.empty:
        conn.close()
        return None
    owner_name = oname.iloc[0,0]

    df = pd.read_sql(
        "SELECT createdOn as date, entryType as type, description, direction, amount "
        "FROM owner_wallets WHERE ownerId=? AND month=? ORDER BY createdOn ASC, id ASC",
        conn, params=(owner_id, month)
    )
    if df.empty:
        conn.close()
        return None

    prior = pd.read_sql(
        "SELECT COALESCE(SUM(CASE WHEN direction='in' THEN amount ELSE -amount END),0) as bal "
        "FROM owner_wallets WHERE ownerId=? AND month < ?",
        conn, params=(owner_id, month)
    )["bal"].iloc[0]

    bal = float(prior)
    balances = []
    for _, r in df.iterrows():
        bal += r["amount"] if r["direction"] == "in" else -r["amount"]
        balances.append(bal)
    df["runningBalance"] = balances

    path = Path(out_dir) / f"Wallet_{owner_name.replace(' ','_')}_{month}.xlsx"
    with pd.ExcelWriter(path) as w:
        df.to_excel(w, sheet_name="Wallet", index=False)

    conn.close()
    return str(path)

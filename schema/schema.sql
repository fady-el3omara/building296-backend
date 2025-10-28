-- ===========================================================
-- Building 296 – Core Database Schema
-- ===========================================================
-- Works for SQLite, PostgreSQL, or MySQL with minor tweaks.
-- Author: ChatGPT (for Building 296 App)
-- ===========================================================

PRAGMA foreign_keys = ON;

-- ===========================================================
-- 1. OWNERS
-- ===========================================================
CREATE TABLE IF NOT EXISTS owners (
    ownerId INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    shareHeld REAL NOT NULL DEFAULT 0.0,
    phone TEXT,
    email TEXT
);

-- ===========================================================
-- 2. RENTS
-- ===========================================================
CREATE TABLE IF NOT EXISTS rents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    unitNumber TEXT,
    tenantName TEXT,
    month TEXT NOT NULL,
    effectiveRent REAL DEFAULT 0.0,
    paidAmount REAL DEFAULT 0.0,
    paymentDate TEXT,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_rents_month ON rents (month);

-- ===========================================================
-- 3. EXPENSES
-- ===========================================================
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    description TEXT,
    amount REAL DEFAULT 0.0,
    month TEXT NOT NULL,
    paidBy TEXT,
    category TEXT,
    ownerSpecific INTEGER DEFAULT 0,   -- 0 = shared, 1 = owner-specific
    chargedOwner INTEGER,
    FOREIGN KEY(chargedOwner) REFERENCES owners(ownerId)
);

CREATE INDEX IF NOT EXISTS idx_expenses_month ON expenses (month);

-- ===========================================================
-- 4. OWNER ALLOWANCES
-- ===========================================================
CREATE TABLE IF NOT EXISTS owner_allowances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ownerId INTEGER,
    month TEXT NOT NULL,
    allowanceType TEXT,
    allowanceValue REAL DEFAULT 0.0,
    notes TEXT,
    FOREIGN KEY(ownerId) REFERENCES owners(ownerId)
);

CREATE INDEX IF NOT EXISTS idx_owner_allowances_month ON owner_allowances (month);

-- ===========================================================
-- 5. EXPECTED DISTRIBUTION (Forecasted Earnings)
-- ===========================================================
CREATE TABLE IF NOT EXISTS expected_distribution (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ownerId INTEGER NOT NULL,
    month TEXT NOT NULL,
    expectedRent REAL DEFAULT 0.0,
    expectedExpenses REAL DEFAULT 0.0,
    expectedNet REAL DEFAULT 0.0,
    generatedOn TEXT NOT NULL,
    FOREIGN KEY(ownerId) REFERENCES owners(ownerId)
);

CREATE INDEX IF NOT EXISTS idx_expected_distribution_month ON expected_distribution (month);

-- ===========================================================
-- 6. VARIANCE REPORT (Actual vs Expected)
-- ===========================================================
CREATE TABLE IF NOT EXISTS variance_report (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ownerId INTEGER NOT NULL,
    month TEXT NOT NULL,
    expectedNet REAL DEFAULT 0.0,
    actualNet REAL DEFAULT 0.0,
    variance REAL DEFAULT 0.0,
    generatedOn TEXT NOT NULL,
    FOREIGN KEY(ownerId) REFERENCES owners(ownerId)
);

CREATE INDEX IF NOT EXISTS idx_variance_report_month ON variance_report (month);

-- ===========================================================
-- 7. OWNER WALLETS (Ledger System)
-- ===========================================================
CREATE TABLE IF NOT EXISTS owner_wallets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ownerId INTEGER NOT NULL,
    month TEXT NOT NULL,
    entryType TEXT NOT NULL,
    description TEXT,
    amount REAL NOT NULL,
    direction TEXT CHECK(direction IN ('in', 'out')),
    createdOn TEXT NOT NULL,
    FOREIGN KEY(ownerId) REFERENCES owners(ownerId)
);

CREATE INDEX IF NOT EXISTS idx_owner_wallets_owner_month ON owner_wallets (ownerId, month);

-- ===========================================================
-- 8. META / LOGS (optional utility)
-- ===========================================================
CREATE TABLE IF NOT EXISTS import_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sheetName TEXT,
    rowsInserted INTEGER,
    status TEXT,
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
);

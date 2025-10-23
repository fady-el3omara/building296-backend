PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS owners (
  ownerId       INTEGER PRIMARY KEY AUTOINCREMENT,
  name          TEXT NOT NULL,
  shareHeld     REAL NOT NULL,
  bankAccount   TEXT,
  email         TEXT
);

CREATE TABLE IF NOT EXISTS units (
  unitId        INTEGER PRIMARY KEY AUTOINCREMENT,
  unitNumber    TEXT NOT NULL,
  tenantName    TEXT,
  startDate     TEXT,
  baseRent      REAL NOT NULL,
  annualIncrease REAL,
  status        TEXT DEFAULT 'Active'
);

CREATE TABLE IF NOT EXISTS rents (
  rentId        INTEGER PRIMARY KEY AUTOINCREMENT,
  month         TEXT NOT NULL,
  unitId        INTEGER NOT NULL,
  effectiveRent REAL NOT NULL,
  paidAmount    REAL NOT NULL DEFAULT 0.0,
  discount      REAL NOT NULL DEFAULT 0.0,
  arrearsBF     REAL NOT NULL DEFAULT 0.0,
  ownerFundedBy INTEGER,
  status        TEXT DEFAULT 'Pending',
  notes         TEXT,
  FOREIGN KEY (unitId) REFERENCES units(unitId) ON DELETE CASCADE,
  FOREIGN KEY (ownerFundedBy) REFERENCES owners(ownerId) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_rents_unitId ON rents(unitId);
CREATE INDEX IF NOT EXISTS idx_rents_month ON rents(month);

CREATE TABLE IF NOT EXISTS expenses (
  expenseId     INTEGER PRIMARY KEY AUTOINCREMENT,
  date          TEXT NOT NULL,
  month         TEXT NOT NULL,
  description   TEXT NOT NULL,
  amount        REAL NOT NULL,
  recurring     INTEGER NOT NULL DEFAULT 0,
  ownerSpecific INTEGER NOT NULL DEFAULT 0,
  chargedOwner  INTEGER,
  type          TEXT,
  notes         TEXT,
  FOREIGN KEY (chargedOwner) REFERENCES owners(ownerId) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_expenses_month ON expenses(month);

CREATE TABLE IF NOT EXISTS owner_allowances (
  allowanceId   INTEGER PRIMARY KEY AUTOINCREMENT,
  month         TEXT NOT NULL,
  ownerId       INTEGER NOT NULL,
  allowanceValue REAL NOT NULL,
  notes         TEXT,
  FOREIGN KEY (ownerId) REFERENCES owners(ownerId) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS expected_distribution (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  month TEXT NOT NULL,
  ownerId INTEGER NOT NULL,
  expectedRent REAL NOT NULL,
  expectedExpenses REAL NOT NULL,
  expectedNet REAL NOT NULL,
  generatedOn TEXT NOT NULL,
  FOREIGN KEY (ownerId) REFERENCES owners(ownerId)
);

CREATE TABLE IF NOT EXISTS variance_report (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  month TEXT NOT NULL,
  ownerId INTEGER NOT NULL,
  expectedNet REAL NOT NULL,
  actualNet REAL NOT NULL,
  variance REAL NOT NULL,
  generatedOn TEXT NOT NULL,
  FOREIGN KEY (ownerId) REFERENCES owners(ownerId)
);

CREATE TABLE IF NOT EXISTS owner_wallets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ownerId INTEGER NOT NULL,
  month TEXT NOT NULL,
  entryType TEXT NOT NULL,
  description TEXT,
  amount REAL NOT NULL,
  direction TEXT NOT NULL, -- 'in' or 'out'
  createdOn TEXT NOT NULL,
  FOREIGN KEY (ownerId) REFERENCES owners(ownerId)
);

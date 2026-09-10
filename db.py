import os
import sqlite3
from datetime import datetime

# Try to connect to SQL Server via pyodbc first
PYODBC_AVAILABLE = False
try:
    import pyodbc
    PYODBC_AVAILABLE = True
except ImportError:
    PYODBC_AVAILABLE = False

SQL_SERVER_CONN_STR = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=localhost;"
    "Database=ElectricityBillingDB;"
    "Trusted_Connection=yes;"
)

import shutil

IS_VERCEL = bool(os.environ.get("VERCEL"))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if IS_VERCEL:
    TMP_DB = "/tmp/electricity_billing.db"
    ORIGINAL_DB = os.path.join(BASE_DIR, "electricity_billing.db")
    if not os.path.exists(TMP_DB):
        if os.path.exists(ORIGINAL_DB):
            try:
                shutil.copy2(ORIGINAL_DB, TMP_DB)
            except Exception:
                pass
    DB_PATH = TMP_DB
else:
    DB_PATH = os.path.join(BASE_DIR, "electricity_billing.db")

class Database:
    def __init__(self):
        self.is_sql_server = False
        self.test_connection()

    def test_connection(self):
        if PYODBC_AVAILABLE:
            try:
                conn = pyodbc.connect(SQL_SERVER_CONN_STR, timeout=2)
                conn.close()
                self.is_sql_server = True
                return True
            except Exception:
                self.is_sql_server = False
        else:
            self.is_sql_server = False
        
        # Ensure SQLite fallback is initialized if SQL Server is not available
        if not self.is_sql_server:
            self._init_sqlite()
        return self.is_sql_server

    def get_connection(self):
        if self.is_sql_server:
            return pyodbc.connect(SQL_SERVER_CONN_STR)
        else:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            return conn

    def _init_sqlite(self):
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.executescript("""
            CREATE TABLE IF NOT EXISTS Customers (
                CustomerID INTEGER PRIMARY KEY AUTOINCREMENT,
                CustomerCode TEXT,
                Title TEXT DEFAULT 'លោក',
                FullName TEXT NOT NULL,
                LastName TEXT,
                FirstName TEXT,
                LastNameEn TEXT,
                FirstNameEn TEXT,
                Gender TEXT DEFAULT 'ប្រុស',
                DOB DATE,
                POB TEXT,
                Occupation TEXT,
                IDType TEXT DEFAULT 'អត្តសញ្ញាណប័ណ្ណ',
                IDNumber TEXT,
                FamilyMembers INTEGER DEFAULT 1,
                CustomerType TEXT DEFAULT 'បុគ្គលមិនជាប់អាករ',
                IsPoorFamily INTEGER DEFAULT 0,
                Representative TEXT,
                AccountNumber TEXT,
                Province TEXT DEFAULT 'កណ្តាល',
                District TEXT DEFAULT 'មុខកំពូល',
                Commune TEXT DEFAULT 'ឫស្សីជ្រោយ',
                Village TEXT DEFAULT 'ឫស្សីជ្រោយ',
                Zone TEXT DEFAULT 'តំបន់ ១',
                HouseNo TEXT,
                StreetNo TEXT,
                Address TEXT NOT NULL,
                PhoneNumber TEXT NOT NULL,
                PoleNo TEXT,
                BoxNo TEXT,
                Breaker TEXT DEFAULT '20A',
                Phase TEXT DEFAULT '1-Phase (220V)',
                TariffType TEXT DEFAULT 'tiered',
                PhotoPath TEXT,
                Status INTEGER NOT NULL DEFAULT 1,
                CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS MeterReadings (
                ReadingID INTEGER PRIMARY KEY AUTOINCREMENT,
                CustomerID INTEGER NOT NULL,
                BillingMonth DATE NOT NULL,
                PreviousReading REAL NOT NULL DEFAULT 0,
                CurrentReading REAL NOT NULL,
                UsageKWh REAL NOT NULL,
                RecordedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS Invoices (
                InvoiceID INTEGER PRIMARY KEY AUTOINCREMENT,
                ReadingID INTEGER NOT NULL,
                RatePerKWh REAL NOT NULL,
                TotalAmount REAL NOT NULL,
                IsPaid INTEGER NOT NULL DEFAULT 0,
                PaymentDate TIMESTAMP NULL,
                CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ReadingID) REFERENCES MeterReadings(ReadingID) ON DELETE CASCADE
            );
        """)
        conn.commit()

        # Migrate existing database if any columns are missing
        cur.execute("PRAGMA table_info(Customers)")
        existing_cols = {row[1] for row in cur.fetchall()}
        required_cols = {
            "CustomerCode": "TEXT",
            "Title": "TEXT DEFAULT 'លោក'",
            "LastName": "TEXT",
            "FirstName": "TEXT",
            "LastNameEn": "TEXT",
            "FirstNameEn": "TEXT",
            "Gender": "TEXT DEFAULT 'ប្រុស'",
            "DOB": "DATE",
            "POB": "TEXT",
            "Occupation": "TEXT",
            "IDType": "TEXT DEFAULT 'អត្តសញ្ញាណប័ណ្ណ'",
            "IDNumber": "TEXT",
            "FamilyMembers": "INTEGER DEFAULT 1",
            "CustomerType": "TEXT DEFAULT 'បុគ្គលមិនជាប់អាករ'",
            "IsPoorFamily": "INTEGER DEFAULT 0",
            "Representative": "TEXT",
            "AccountNumber": "TEXT",
            "Province": "TEXT DEFAULT 'កណ្តាល'",
            "District": "TEXT DEFAULT 'មុខកំពូល'",
            "Commune": "TEXT DEFAULT 'ឫស្សីជ្រោយ'",
            "Village": "TEXT DEFAULT 'ឫស្សីជ្រោយ'",
            "Zone": "TEXT DEFAULT 'តំបន់ ១'",
            "HouseNo": "TEXT",
            "StreetNo": "TEXT",
            "PoleNo": "TEXT",
            "BoxNo": "TEXT",
            "Breaker": "TEXT DEFAULT '20A'",
            "Phase": "TEXT DEFAULT '1-Phase (220V)'",
            "TariffType": "TEXT DEFAULT 'tiered'",
            "PhotoPath": "TEXT"
        }
        for col_name, col_def in required_cols.items():
            if col_name not in existing_cols:
                cur.execute(f"ALTER TABLE Customers ADD COLUMN {col_name} {col_def}")

        cur.execute("UPDATE Customers SET CustomerCode = printf('%06d', CustomerID) WHERE CustomerCode IS NULL OR CustomerCode = ''")
        cur.execute("UPDATE Customers SET Title = 'លោក' WHERE Title IS NULL OR Title = ''")
        cur.execute("UPDATE Customers SET TariffType = 'tiered' WHERE TariffType IS NULL OR TariffType = ''")
        conn.commit()

        # Seed sample data if empty
        cur.execute("SELECT COUNT(*) FROM Customers")
        if cur.fetchone()[0] == 0:
            cur.executescript("""
                INSERT INTO Customers (
                    CustomerCode, Title, FullName, LastName, FirstName,
                    PhoneNumber, Address, Province, District, Commune, Village,
                    Zone, PoleNo, BoxNo, Breaker, Phase, TariffType, Status
                ) VALUES
                ('004158', 'លោក', 'សុខ ចាន់ដារ៉ា (Sok Chandara)', 'សុខ', 'ចាន់ដារ៉ា', '012345678', 'ផ្ទះលេខ 12A, ផ្លូវ 271, ភ្នំពេញ (BP-012)', 'ភ្នំពេញ', 'មានជ័យ', 'បឹងទំពុន', 'បឹងទំពុន', 'តំបន់ ១', 'BP-012', 'BX-12', '20A', '1-Phase (220V)', 'tiered', 1),
                ('004159', 'លោកស្រី', 'កែវ សោភា (Keo Sophea)', 'កែវ', 'សោភា', '098765432', 'ផ្ទះលេខ 45B, ផ្លូវ 2004, ភ្នំពេញ (KK-045)', 'ភ្នំពេញ', 'ពោធិ៍សែនជ័យ', 'កាកាប', 'កាកាប', 'តំបន់ ១', 'KK-045', 'BX-45', '20A', '1-Phase (220V)', 'tiered', 1),
                ('004160', 'លោក', 'ម៉ៅ វិបុល (Mao Vibol)', 'ម៉ៅ', 'វិបុល', '088123456', 'ផ្ទះលេខ 78, ផ្លូវជាតិលេខ 4, ភ្នំពេញ (CC-078)', 'ភ្នំពេញ', 'ពោធិ៍សែនជ័យ', 'ចោមចៅ', 'ចោមចៅ', 'តំបន់ ២', 'CC-078', 'BX-78', '32A', '1-Phase (220V)', 'tiered', 1),
                ('004161', 'កញ្ញា', 'ចាន់ ធីតា (Chan Thida)', 'ចាន់', 'ធីតា', '097987654', 'ផ្ទះលេខ 102, ផ្លូវ 598, ភ្នំពេញ (TS-102)', 'ភ្នំពេញ', 'ឫស្សីកែវ', 'ទួលសង្កែ', 'ទួលសង្កែ', 'តំបន់ ២', 'TS-102', 'BX-102', '20A', '1-Phase (220V)', 'tiered', 1),
                ('004162', 'លោក', 'ហេង ពិសិដ្ឋ (Heng Piseth)', 'ហេង', 'ពិសិដ្ឋ', '016555888', 'ផ្ទះលេខ 33, ផ្លូវ 371, ភ្នំពេញ (SM-033)', 'ភ្នំពេញ', 'មានជ័យ', 'ស្ទឹងមានជ័យ', 'ស្ទឹងមានជ័យ', 'តំបន់ ១', 'SM-033', 'BX-33', '20A', '1-Phase (220V)', 'tiered', 1),
                ('004163', 'អ្នកស្រី', 'លី ស្រីមុំ (Ly Sreymom)', 'លី', 'ស្រីមុំ', '077333444', 'ផ្ទះលេខ 89, ផ្លូវ 217, ភ្នំពេញ (DK-089)', 'ភ្នំពេញ', 'ដង្កោ', 'ដង្កោ', 'ដង្កោ', 'តំបន់ ៣', 'DK-089', 'BX-89', '20A', '1-Phase (220V)', 'tiered', 0);

                INSERT INTO MeterReadings (CustomerID, BillingMonth, PreviousReading, CurrentReading, UsageKWh)
                VALUES (1, '2026-08-01', 0, 45, 45);
                INSERT INTO Invoices (ReadingID, RatePerKWh, TotalAmount, IsPaid, PaymentDate)
                VALUES (1, 400, 18000, 1, '2026-08-25 10:00:00');

                INSERT INTO MeterReadings (CustomerID, BillingMonth, PreviousReading, CurrentReading, UsageKWh)
                VALUES (2, '2026-08-01', 0, 120, 120);
                INSERT INTO Invoices (ReadingID, RatePerKWh, TotalAmount, IsPaid, PaymentDate)
                VALUES (2, 400, 62000, 1, '2026-08-28 15:30:00');

                INSERT INTO MeterReadings (CustomerID, BillingMonth, PreviousReading, CurrentReading, UsageKWh)
                VALUES (1, '2026-09-01', 45, 115, 70);
                INSERT INTO Invoices (ReadingID, RatePerKWh, TotalAmount, IsPaid)
                VALUES (3, 400, 32000, 0);

                INSERT INTO MeterReadings (CustomerID, BillingMonth, PreviousReading, CurrentReading, UsageKWh)
                VALUES (2, '2026-09-01', 120, 210, 90);
                INSERT INTO Invoices (ReadingID, RatePerKWh, TotalAmount, IsPaid)
                VALUES (4, 400, 44000, 0);
            """)
            conn.commit()
        conn.close()

db = Database()

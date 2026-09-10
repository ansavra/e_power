-- Electricity Billing System Database Setup
USE ElectricityBillingDB;
GO

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO

-- 1. Drop existing tables if they exist in reverse order
IF OBJECT_ID('Invoices', 'U') IS NOT NULL DROP TABLE Invoices;
IF OBJECT_ID('MeterReadings', 'U') IS NOT NULL DROP TABLE MeterReadings;
IF OBJECT_ID('Customers', 'U') IS NOT NULL DROP TABLE Customers;
GO

-- 2. Create Customers Table
CREATE TABLE Customers (
    CustomerID INT IDENTITY(1,1) PRIMARY KEY,
    CustomerCode VARCHAR(20) NULL,
    Title NVARCHAR(20) DEFAULT N'លោក',
    FullName NVARCHAR(100) NOT NULL,
    LastName NVARCHAR(50) NULL,
    FirstName NVARCHAR(50) NULL,
    LastNameEn VARCHAR(50) NULL,
    FirstNameEn VARCHAR(50) NULL,
    Gender NVARCHAR(10) DEFAULT N'ប្រុស',
    DOB DATE NULL,
    POB NVARCHAR(255) NULL,
    Occupation NVARCHAR(100) NULL,
    IDType NVARCHAR(50) DEFAULT N'អត្តសញ្ញាណប័ណ្ណ',
    IDNumber VARCHAR(50) NULL,
    FamilyMembers INT DEFAULT 1,
    CustomerType NVARCHAR(50) DEFAULT N'បុគ្គលមិនជាប់អាករ',
    IsPoorFamily BIT DEFAULT 0,
    Representative NVARCHAR(100) NULL,
    AccountNumber VARCHAR(50) NULL,
    Province NVARCHAR(50) DEFAULT N'កណ្តាល',
    District NVARCHAR(50) DEFAULT N'មុខកំពូល',
    Commune NVARCHAR(50) DEFAULT N'ឫស្សីជ្រោយ',
    Village NVARCHAR(50) DEFAULT N'ឫស្សីជ្រោយ',
    Zone NVARCHAR(50) DEFAULT N'តំបន់ ១',
    HouseNo NVARCHAR(50) NULL,
    StreetNo NVARCHAR(50) NULL,
    Address NVARCHAR(255) NOT NULL,
    PhoneNumber VARCHAR(20) NOT NULL,
    PoleNo VARCHAR(50) NULL,
    BoxNo VARCHAR(50) NULL,
    Breaker VARCHAR(20) DEFAULT '20A',
    Phase VARCHAR(30) DEFAULT '1-Phase (220V)',
    TariffType VARCHAR(20) DEFAULT 'tiered',
    PhotoPath NVARCHAR(255) NULL,
    Status BIT NOT NULL DEFAULT 1, -- 1: Active, 0: Inactive
    CreatedAt DATETIME NOT NULL DEFAULT GETDATE()
);
GO

-- 3. Create MeterReadings Table
CREATE TABLE MeterReadings (
    ReadingID INT IDENTITY(1,1) PRIMARY KEY,
    CustomerID INT NOT NULL,
    BillingMonth DATE NOT NULL,
    PreviousReading DECIMAL(18,2) NOT NULL DEFAULT 0,
    CurrentReading DECIMAL(18,2) NOT NULL,
    UsageKWh DECIMAL(18,2) NOT NULL,
    RecordedDate DATETIME NOT NULL DEFAULT GETDATE(),
    CONSTRAINT FK_MeterReadings_Customers FOREIGN KEY (CustomerID) 
        REFERENCES Customers(CustomerID) ON DELETE CASCADE
);
GO

-- 4. Create Invoices Table
CREATE TABLE Invoices (
    InvoiceID INT IDENTITY(1,1) PRIMARY KEY,
    ReadingID INT NOT NULL,
    RatePerKWh DECIMAL(18,2) NOT NULL,
    TotalAmount DECIMAL(18,2) NOT NULL,
    IsPaid BIT NOT NULL DEFAULT 0, -- 0: Unpaid, 1: Paid
    PaymentDate DATETIME NULL,
    CreatedAt DATETIME NOT NULL DEFAULT GETDATE(),
    CONSTRAINT FK_Invoices_MeterReadings FOREIGN KEY (ReadingID) 
        REFERENCES MeterReadings(ReadingID) ON DELETE CASCADE
);
GO

-- 5. Seed Initial Sample Data (Khmer & English names, realistic locations and readings)
INSERT INTO Customers (
    CustomerCode, Title, FullName, LastName, FirstName, PhoneNumber, Address,
    Province, District, Commune, Village, Zone, PoleNo, BoxNo, Breaker, Phase, TariffType, Status
) VALUES
('004158', N'លោក', N'សុខ ចាន់ដារ៉ា (Sok Chandara)', N'សុខ', N'ចាន់ដារ៉ា', '012345678', N'ផ្ទះលេខ 12A, ផ្លូវ 271, សង្កាត់បឹងទំពុន, ភ្នំពេញ (បង្គោលលេខ BP-012)', N'ភ្នំពេញ', N'មានជ័យ', N'បឹងទំពុន', N'បឹងទំពុន', N'តំបន់ ១', 'BP-012', 'BX-12', '20A', '1-Phase (220V)', 'tiered', 1),
('004159', N'លោកស្រី', N'កែវ សោភា (Keo Sophea)', N'កែវ', N'សោភា', '098765432', N'ផ្ទះលេខ 45B, ផ្លូវ 2004, សង្កាត់កាកាប, ភ្នំពេញ (បង្គោលលេខ KK-045)', N'ភ្នំពេញ', N'ពោធិ៍សែនជ័យ', N'កាកាប', N'កាកាប', N'តំបន់ ១', 'KK-045', 'BX-45', '20A', '1-Phase (220V)', 'tiered', 1),
('004160', N'លោក', N'ម៉ៅ វិបុល (Mao Vibol)', N'ម៉ៅ', N'វិបុល', '088123456', N'ផ្ទះលេខ 78, ផ្លូវជាតិលេខ 4, សង្កាត់ចោមចៅ, ភ្នំពេញ (បង្គោលលេខ CC-078)', N'ភ្នំពេញ', N'ពោធិ៍សែនជ័យ', N'ចោមចៅ', N'ចោមចៅ', N'តំបន់ ២', 'CC-078', 'BX-78', '32A', '1-Phase (220V)', 'tiered', 1),
('004161', N'កញ្ញា', N'ចាន់ ធីតា (Chan Thida)', N'ចាន់', N'ធីតា', '097987654', N'ផ្ទះលេខ 102, ផ្លូវ 598, សង្កាត់ទួលសង្កែ, ភ្នំពេញ (បង្គោលលេខ TS-102)', N'ភ្នំពេញ', N'ឫស្សីកែវ', N'ទួលសង្កែ', N'ទួលសង្កែ', N'តំបន់ ២', 'TS-102', 'BX-102', '20A', '1-Phase (220V)', 'tiered', 1),
('004162', N'លោក', N'ហេង ពិសិដ្ឋ (Heng Piseth)', N'ហេង', N'ពិសិដ្ឋ', '016555888', N'ផ្ទះលេខ 33, ផ្លូវ 371, សង្កាត់ស្ទឹងមានជ័យ, ភ្នំពេញ (បង្គោលលេខ SM-033)', N'ភ្នំពេញ', N'មានជ័យ', N'ស្ទឹងមានជ័យ', N'ស្ទឹងមានជ័យ', N'តំបន់ ១', 'SM-033', 'BX-33', '20A', '1-Phase (220V)', 'tiered', 1),
('004163', N'អ្នកស្រី', N'លី ស្រីមុំ (Ly Sreymom)', N'លី', N'ស្រីមុំ', '077333444', N'ផ្ទះលេខ 89, ផ្លូវ 217, សង្កាត់ដង្កោ, ភ្នំពេញ (បង្គោលលេខ DK-089)', N'ភ្នំពេញ', N'ដង្កោ', N'ដង្កោ', N'ដង្កោ', N'តំបន់ ៣', 'DK-089', 'BX-89', '20A', '1-Phase (220V)', 'tiered', 0);
GO

-- Month 1 Readings (2026-08)
-- Chandara: 0 -> 45 kWh (<=50 => 45 * 400 = 18,000 KHR)
INSERT INTO MeterReadings (CustomerID, BillingMonth, PreviousReading, CurrentReading, UsageKWh)
VALUES (1, '2026-08-01', 0, 45, 45);
INSERT INTO Invoices (ReadingID, RatePerKWh, TotalAmount, IsPaid, PaymentDate)
VALUES (SCOPE_IDENTITY(), 400, 18000, 1, '2026-08-25');

-- Sophea: 0 -> 120 kWh (50*400 + 70*600 = 20,000 + 42,000 = 62,000 KHR)
INSERT INTO MeterReadings (CustomerID, BillingMonth, PreviousReading, CurrentReading, UsageKWh)
VALUES (2, '2026-08-01', 0, 120, 120);
INSERT INTO Invoices (ReadingID, RatePerKWh, TotalAmount, IsPaid, PaymentDate)
VALUES (SCOPE_IDENTITY(), 400, 62000, 1, '2026-08-28');

-- Vibol: 0 -> 85 kWh (50*400 + 35*600 = 20,000 + 21,000 = 41,000 KHR)
INSERT INTO MeterReadings (CustomerID, BillingMonth, PreviousReading, CurrentReading, UsageKWh)
VALUES (3, '2026-08-01', 0, 85, 85);
INSERT INTO Invoices (ReadingID, RatePerKWh, TotalAmount, IsPaid, PaymentDate)
VALUES (SCOPE_IDENTITY(), 400, 41000, 0, NULL);

-- Month 2 Readings (2026-09)
-- Chandara: 45 -> 115 kWh (Usage = 70 kWh => 50*400 + 20*600 = 20,000 + 12,000 = 32,000 KHR)
INSERT INTO MeterReadings (CustomerID, BillingMonth, PreviousReading, CurrentReading, UsageKWh)
VALUES (1, '2026-09-01', 45, 115, 70);
INSERT INTO Invoices (ReadingID, RatePerKWh, TotalAmount, IsPaid, PaymentDate)
VALUES (SCOPE_IDENTITY(), 400, 32000, 0, NULL);

-- Sophea: 120 -> 210 kWh (Usage = 90 kWh => 50*400 + 40*600 = 20,000 + 24,000 = 44,000 KHR)
INSERT INTO MeterReadings (CustomerID, BillingMonth, PreviousReading, CurrentReading, UsageKWh)
VALUES (2, '2026-09-01', 120, 210, 90);
INSERT INTO Invoices (ReadingID, RatePerKWh, TotalAmount, IsPaid, PaymentDate)
VALUES (SCOPE_IDENTITY(), 400, 44000, 0, NULL);

-- Thida: 0 -> 40 kWh (Usage = 40 kWh => 40*400 = 16,000 KHR)
INSERT INTO MeterReadings (CustomerID, BillingMonth, PreviousReading, CurrentReading, UsageKWh)
VALUES (4, '2026-09-01', 0, 40, 40);
INSERT INTO Invoices (ReadingID, RatePerKWh, TotalAmount, IsPaid, PaymentDate)
VALUES (SCOPE_IDENTITY(), 400, 16000, 0, NULL);
GO

SELECT 'Database and sample data initialized successfully' AS Result;
GO

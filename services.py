from datetime import datetime
from db import db

class BillingService:
    TIER1_THRESHOLD = 50.0
    TIER1_RATE = 400.0  # 400 Riels per kWh for first 50 kWh
    TIER2_RATE = 600.0  # 600 Riels per kWh above 50 kWh

    @classmethod
    def calculate_total(cls, usage_kwh: float, use_tiered: bool = True, flat_rate: float = 500.0,
                        tier1_limit: float = 50.0, tier1_rate: float = 400.0, tier2_rate: float = 600.0) -> float:
        if usage_kwh <= 0:
            return 0.0

        if not use_tiered:
            return usage_kwh * flat_rate

        if usage_kwh <= tier1_limit:
            return usage_kwh * tier1_rate
        else:
            tier1_cost = tier1_limit * tier1_rate
            tier2_usage = usage_kwh - tier1_limit
            tier2_cost = tier2_usage * tier2_rate
            return tier1_cost + tier2_cost

    @classmethod
    def get_tier_breakdown(cls, usage_kwh: float, rate_per_kwh: float = 400.0,
                           tier1_limit: float = 50.0, tier1_rate: float = 400.0, tier2_rate: float = 600.0,
                           is_flat: bool = False):
        if usage_kwh <= 0:
            return {"is_flat": is_flat, "t1_kwh": 0, "t1_cost": 0, "t2_kwh": 0, "t2_cost": 0, "flat_rate": rate_per_kwh}

        if is_flat:
            return {
                "is_flat": True,
                "flat_rate": rate_per_kwh,
                "flat_cost": usage_kwh * rate_per_kwh,
                "t1_kwh": usage_kwh,
                "t1_cost": usage_kwh * rate_per_kwh,
                "t2_kwh": 0,
                "t2_cost": 0
            }

        if usage_kwh <= tier1_limit:
            return {
                "is_flat": False,
                "t1_limit": tier1_limit,
                "t1_rate": tier1_rate,
                "t1_kwh": usage_kwh,
                "t1_cost": usage_kwh * tier1_rate,
                "t2_kwh": 0,
                "t2_cost": 0,
                "t2_rate": tier2_rate
            }
        else:
            t1_kwh = tier1_limit
            t1_cost = t1_kwh * tier1_rate
            t2_kwh = usage_kwh - tier1_limit
            t2_cost = t2_kwh * tier2_rate
            return {
                "is_flat": False,
                "t1_limit": tier1_limit,
                "t1_rate": tier1_rate,
                "t1_kwh": t1_kwh,
                "t1_cost": t1_cost,
                "t2_kwh": t2_kwh,
                "t2_cost": t2_cost,
                "t2_rate": tier2_rate
            }

    @classmethod
    def get_invoices(cls, status_filter="All", search=""):
        conn = db.get_connection()
        cur = conn.cursor()

        where_clauses = ["1=1"]
        params = []

        if status_filter == "Unpaid":
            where_clauses.append("i.IsPaid = 0")
        elif status_filter == "Paid":
            where_clauses.append("i.IsPaid = 1")

        if search:
            search_param = f"%{search.strip()}%"
            where_clauses.append("(c.FullName LIKE ? OR c.PhoneNumber LIKE ? OR c.Address LIKE ? OR CAST(i.InvoiceID AS VARCHAR) = ?)")
            params.extend([search_param, search_param, search_param, search.strip()])

        where_sql = " AND ".join(where_clauses)
        sql = f"""
            SELECT 
                i.InvoiceID, i.ReadingID, c.CustomerID, c.FullName, c.PhoneNumber, c.Address,
                r.BillingMonth, r.PreviousReading, r.CurrentReading, r.UsageKWh,
                i.RatePerKWh, i.TotalAmount, i.IsPaid, i.PaymentDate, i.CreatedAt
            FROM Invoices i
            INNER JOIN MeterReadings r ON i.ReadingID = r.ReadingID
            INNER JOIN Customers c ON r.CustomerID = c.CustomerID
            WHERE {where_sql}
            ORDER BY i.InvoiceID DESC
        """

        cur.execute(sql, params)
        rows = cur.fetchall()

        invoices = []
        for r in rows:
            # Handle both pyodbc Row and sqlite3 Row
            inv = {
                "invoice_id": r[0],
                "reading_id": r[1],
                "customer_id": r[2],
                "customer_name": r[3],
                "phone_number": r[4],
                "address": r[5],
                "billing_month": str(r[6])[:7] if r[6] else "",
                "previous_reading": float(r[7]),
                "current_reading": float(r[8]),
                "usage_kwh": float(r[9]),
                "rate_per_kwh": float(r[10]),
                "total_amount": float(r[11]),
                "is_paid": bool(r[12]),
                "payment_date": str(r[13])[:16] if r[13] else None,
                "created_at": str(r[14])[:16] if r[14] else "",
            }
            invoices.append(inv)

        conn.close()
        return invoices

    @classmethod
    def get_invoice_by_id(cls, invoice_id: int):
        conn = db.get_connection()
        cur = conn.cursor()
        sql = """
            SELECT 
                i.InvoiceID, i.ReadingID, c.CustomerID, c.FullName, c.PhoneNumber, c.Address,
                r.BillingMonth, r.PreviousReading, r.CurrentReading, r.UsageKWh,
                i.RatePerKWh, i.TotalAmount, i.IsPaid, i.PaymentDate, i.CreatedAt,
                c.CustomerCode, c.Zone, c.PoleNo, c.BoxNo, c.Breaker, c.Phase,
                c.Village, c.Commune, c.District, c.Province
            FROM Invoices i
            INNER JOIN MeterReadings r ON i.ReadingID = r.ReadingID
            INNER JOIN Customers c ON r.CustomerID = c.CustomerID
            WHERE i.InvoiceID = ?
        """
        try:
            cur.execute(sql, [invoice_id])
            r = cur.fetchone()
        except Exception:
            # Fallback if extended columns missing
            cur.execute("""
                SELECT 
                    i.InvoiceID, i.ReadingID, c.CustomerID, c.FullName, c.PhoneNumber, c.Address,
                    r.BillingMonth, r.PreviousReading, r.CurrentReading, r.UsageKWh,
                    i.RatePerKWh, i.TotalAmount, i.IsPaid, i.PaymentDate, i.CreatedAt
                FROM Invoices i
                INNER JOIN MeterReadings r ON i.ReadingID = r.ReadingID
                INNER JOIN Customers c ON r.CustomerID = c.CustomerID
                WHERE i.InvoiceID = ?
            """, [invoice_id])
            r = cur.fetchone()
            conn.close()
            if not r:
                return None
            b_month = str(r[6])[:7] if r[6] else ""
            yymm = b_month.replace("-", "")[2:] if len(b_month) >= 7 else "2608"
            return {
                "invoice_id": r[0],
                "reading_id": r[1],
                "customer_id": r[2],
                "customer_name": r[3],
                "phone_number": r[4],
                "address": r[5],
                "billing_month": b_month,
                "previous_reading": float(r[7]),
                "current_reading": float(r[8]),
                "usage_kwh": float(r[9]),
                "rate_per_kwh": float(r[10]),
                "total_amount": float(r[11]),
                "is_paid": bool(r[12]),
                "payment_date": str(r[13])[:16] if r[13] else None,
                "created_at": str(r[14])[:16] if r[14] else "",
                "customer_code": f"{r[2]:06d}",
                "zone": "តំបន់ ១",
                "pole_no": "P-01",
                "box_no": "B-01",
                "breaker": "20A",
                "phase": "1-Phase (220V)",
                "village": "",
                "commune": "",
                "district": "",
                "province": "",
                "invoice_code": f"INV{yymm}-{r[0]:06d}"
            }

        conn.close()
        if not r:
            return None

        b_month = str(r[6])[:7] if r[6] else ""
        yymm = b_month.replace("-", "")[2:] if len(b_month) >= 7 else "2608"
        inv_code = f"INV{yymm}-{r[0]:06d}"

        return {
            "invoice_id": r[0],
            "reading_id": r[1],
            "customer_id": r[2],
            "customer_name": r[3],
            "phone_number": r[4],
            "address": r[5],
            "billing_month": b_month,
            "previous_reading": float(r[7]),
            "current_reading": float(r[8]),
            "usage_kwh": float(r[9]),
            "rate_per_kwh": float(r[10]),
            "total_amount": float(r[11]),
            "is_paid": bool(r[12]),
            "payment_date": str(r[13])[:16] if r[13] else None,
            "created_at": str(r[14])[:16] if r[14] else "",
            "customer_code": r[15] or f"{r[2]:06d}",
            "zone": r[16] or "តំបន់ ១",
            "pole_no": r[17] or "P-01",
            "box_no": r[18] or "B-01",
            "breaker": r[19] or "20A",
            "phase": r[20] or "1-Phase (220V)",
            "village": r[21] or "",
            "commune": r[22] or "",
            "district": r[23] or "",
            "province": r[24] or "",
            "invoice_code": inv_code
        }

    @classmethod
    def get_customer_usage_history_12m(cls, customer_id: int, current_billing_month: str = ""):
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT BillingMonth, UsageKWh 
            FROM MeterReadings 
            WHERE CustomerID = ? 
            ORDER BY BillingMonth ASC
        """, [customer_id])
        rows = cur.fetchall()
        conn.close()

        actual_map = {}
        for r in rows:
            m_str = str(r[0])[:7]
            actual_map[m_str] = float(r[1])

        if current_billing_month and len(current_billing_month) >= 7:
            try:
                base_dt = datetime.strptime(current_billing_month[:7], "%Y-%m")
            except Exception:
                base_dt = datetime.now()
        else:
            base_dt = datetime.now()

        history = []
        for offset in range(12, 0, -1):
            year = base_dt.year
            month = base_dt.month - offset
            while month <= 0:
                month += 12
                year -= 1
            m_key = f"{year:04d}-{month:02d}"
            label = f"{month:02d}-{year:04d}"
            if m_key in actual_map:
                kwh = actual_map[m_key]
            else:
                sample_kwhs = [5, 3, 7, 5, 10, 6, 4, 6, 9, 9, 9, 11]
                idx = (customer_id * 3 + offset) % len(sample_kwhs)
                kwh = sample_kwhs[idx]
            history.append({
                "month_label": label,
                "usage_kwh": int(round(kwh)) if round(kwh) == int(kwh) else round(kwh, 1)
            })
        return history

    @classmethod
    def mark_as_paid(cls, invoice_id: int):
        conn = db.get_connection()
        cur = conn.cursor()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur.execute(
            "UPDATE Invoices SET IsPaid = 1, PaymentDate = ? WHERE InvoiceID = ? AND IsPaid = 0",
            [now_str, invoice_id]
        )
        conn.commit()
        affected = cur.rowcount
        conn.close()
        return affected > 0


import base64
import os
import re

def save_base64_photo(code, photo_data):
    if not photo_data or not photo_data.startswith("data:image"):
        return photo_data or None
    try:
        match = re.search(r"data:image/(\w+);base64,(.*)", photo_data)
        if not match:
            return None
        ext = match.group(1).lower()
        if ext == "jpeg":
            ext = "jpg"
        img_bytes = base64.b64decode(match.group(2))
        upload_dir = os.path.join(os.path.dirname(__file__), "static", "uploads", "customers")
        os.makedirs(upload_dir, exist_ok=True)
        filename = f"cust_{code}.{ext}"
        filepath = os.path.join(upload_dir, filename)
        with open(filepath, "wb") as f:
            f.write(img_bytes)
        return f"/static/uploads/customers/{filename}"
    except Exception as e:
        print("Error saving photo:", e)
        return None


def normalize_dob(dob_str):
    if not dob_str:
        return None
    dob_str = str(dob_str).strip()
    if not dob_str:
        return None
    # Check DD/MM/YYYY or DD-MM-YYYY
    m = re.match(r"^(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4})$", dob_str)
    if m:
        d, mth, y = m.groups()
        return f"{y}-{int(mth):02d}-{int(d):02d}"
    # Check YYYY-MM-DD
    m = re.match(r"^(\d{4})[/\-.](\d{1,2})[/\-.](\d{1,2})$", dob_str)
    if m:
        y, mth, d = m.groups()
        return f"{y}-{int(mth):02d}-{int(d):02d}"
    if re.match(r"^\d{4}$", dob_str):
        return f"{dob_str}-01-01"
    return dob_str


class CustomerService:
    @classmethod
    def get_paged(cls, search="", page=1, page_size=10):
        conn = db.get_connection()
        cur = conn.cursor()

        where = ""
        params = []
        if search:
            where = "WHERE (CustomerCode LIKE ? OR FullName LIKE ? OR PhoneNumber LIKE ? OR Address LIKE ? OR LastNameEn LIKE ? OR FirstNameEn LIKE ?)"
            p = f"%{search.strip()}%"
            params = [p, p, p, p, p, p]

        # Total count
        cur.execute(f"SELECT COUNT(*) FROM Customers {where}", params)
        total_records = cur.fetchone()[0]

        offset = max(0, (page - 1) * page_size)

        if db.is_sql_server:
            sql = f"""
                SELECT CustomerID, FullName, PhoneNumber, Address, Status, CreatedAt,
                       CustomerCode, Title, LastName, FirstName, LastNameEn, FirstNameEn,
                       PhotoPath, PoleNo
                FROM Customers {where}
                ORDER BY CustomerID DESC
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """
            cur.execute(sql, params + [offset, page_size])
        else:
            sql = f"""
                SELECT CustomerID, FullName, PhoneNumber, Address, Status, CreatedAt,
                       CustomerCode, Title, LastName, FirstName, LastNameEn, FirstNameEn,
                       PhotoPath, PoleNo
                FROM Customers {where}
                ORDER BY CustomerID DESC
                LIMIT ? OFFSET ?
            """
            cur.execute(sql, params + [page_size, offset])

        rows = cur.fetchall()
        customers = []
        for r in rows:
            customers.append({
                "customer_id": r[0],
                "full_name": r[1],
                "phone_number": r[2],
                "address": r[3],
                "status": bool(r[4]),
                "created_at": str(r[5])[:10] if r[5] else "",
                "customer_code": r[6] or f"{r[0]:06d}",
                "title": r[7] or "លោក",
                "last_name": r[8] or "",
                "first_name": r[9] or "",
                "last_name_en": r[10] or "",
                "first_name_en": r[11] or "",
                "photo_path": r[12] or "",
                "pole_no": r[13] or ""
            })

        conn.close()
        return customers, total_records

    @classmethod
    def get_all_active(cls):
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT CustomerID, CustomerCode, Title, FullName, PhoneNumber, Address, PoleNo, TariffType
            FROM Customers 
            WHERE Status = 1 
            ORDER BY CustomerCode ASC, FullName ASC
        """)
        rows = cur.fetchall()
        conn.close()
        return [
            {
                "customer_id": r[0],
                "customer_code": r[1] or f"#{r[0]}",
                "title": r[2] or "លោក",
                "full_name": r[3],
                "phone_number": r[4],
                "address": r[5],
                "pole_no": r[6] or "",
                "tariff_type": r[7] or "tiered",
                "display": f"[{r[1] or ('#' + str(r[0]))}] {r[2] or ''} {r[3]} ({r[4]})"
            }
            for r in rows
        ]

    @classmethod
    def get_by_id(cls, customer_id: int):
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT CustomerID, FullName, PhoneNumber, Address, Status,
                   CustomerCode, Title, LastName, FirstName, LastNameEn, FirstNameEn,
                   Gender, DOB, POB, Occupation, IDType, IDNumber, FamilyMembers,
                   CustomerType, IsPoorFamily, Representative, AccountNumber,
                   Province, District, Commune, Village, Zone, HouseNo, StreetNo,
                   PoleNo, BoxNo, Breaker, Phase, TariffType, PhotoPath
            FROM Customers WHERE CustomerID = ?
        """, [customer_id])
        r = cur.fetchone()
        conn.close()
        if r:
            return {
                "customer_id": r[0],
                "full_name": r[1] or "",
                "phone_number": r[2] or "",
                "address": r[3] or "",
                "status": bool(r[4]),
                "customer_code": r[5] or "",
                "title": r[6] or "លោក",
                "last_name": r[7] or "",
                "first_name": r[8] or "",
                "last_name_en": r[9] or "",
                "first_name_en": r[10] or "",
                "gender": r[11] or "ប្រុស",
                "dob": str(r[12])[:10] if r[12] else "",
                "pob": r[13] or "",
                "occupation": r[14] or "",
                "id_type": r[15] or "អត្តសញ្ញាណប័ណ្ណ",
                "id_number": r[16] or "",
                "family_members": r[17] if r[17] is not None else 1,
                "customer_type": r[18] or "បុគ្គលមិនជាប់អាករ",
                "is_poor_family": bool(r[19]),
                "representative": r[20] or "",
                "account_number": r[21] or "",
                "province": r[22] or "កណ្តាល",
                "district": r[23] or "មុខកំពូល",
                "commune": r[24] or "ឫស្សីជ្រោយ",
                "village": r[25] or "ឫស្សីជ្រោយ",
                "zone": r[26] or "តំបន់ ១",
                "house_no": r[27] or "",
                "street_no": r[28] or "",
                "pole_no": r[29] or "",
                "box_no": r[30] or "",
                "breaker": r[31] or "20A",
                "phase": r[32] or "1-Phase (220V)",
                "tariff_type": r[33] or "tiered",
                "photo_path": r[34] or ""
            }
        return None

    @classmethod
    def generate_next_code(cls):
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT CustomerCode FROM Customers WHERE CustomerCode IS NOT NULL")
        rows = cur.fetchall()
        conn.close()
        max_num = 0
        for r in rows:
            val = str(r[0]).strip()
            if val.isdigit():
                num = int(val)
                if num > max_num:
                    max_num = num
        if max_num > 0:
            return f"{max_num + 1:06d}"
        return "004158"

    @classmethod
    def add(cls, data: dict):
        last_name = data.get("last_name", "").strip()
        first_name = data.get("first_name", "").strip()
        full_name = f"{last_name} {first_name}".strip() or last_name or data.get("full_name", "").strip()
        phone = data.get("phone_number", "").strip()
        
        # Build address
        house = data.get("house_no", "").strip()
        street = data.get("street_no", "").strip()
        village = data.get("village", "").strip()
        commune = data.get("commune", "").strip()
        district = data.get("district", "").strip()
        province = data.get("province", "").strip()
        custom_addr = data.get("address", "").strip()

        addr_parts = []
        if house: addr_parts.append(f"ផ្ទះលេខ {house}")
        if street: addr_parts.append(f"ផ្លូវលេខ {street}")
        if village: addr_parts.append(f"ភូមិ {village}")
        if commune: addr_parts.append(f"ឃុំ/សង្កាត់ {commune}")
        if district: addr_parts.append(f"ស្រុក/ក្រុង {district}")
        if province: addr_parts.append(f"ខេត្ត/រាជធានី {province}")
        computed_addr = ", ".join(addr_parts)
        final_addr = custom_addr if custom_addr else computed_addr

        code = data.get("customer_code") or cls.generate_next_code()
        photo_path = save_base64_photo(code, data.get("photo_data")) or data.get("photo_path")

        conn = db.get_connection()
        cur = conn.cursor()
        if db.is_sql_server:
            cur.execute("""
                INSERT INTO Customers (
                    FullName, PhoneNumber, Address, Status,
                    CustomerCode, Title, LastName, FirstName, LastNameEn, FirstNameEn,
                    Gender, DOB, POB, Occupation, IDType, IDNumber, FamilyMembers,
                    CustomerType, IsPoorFamily, Representative, AccountNumber,
                    Province, District, Commune, Village, Zone, HouseNo, StreetNo,
                    PoleNo, BoxNo, Breaker, Phase, TariffType, PhotoPath
                )
                VALUES (
                    ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?
                )
            """, [
                full_name, phone, final_addr, 1 if data.get("status", True) else 0,
                code, data.get("title", "លោក"), last_name, first_name, data.get("last_name_en", ""), data.get("first_name_en", ""),
                data.get("gender", "ប្រុស"), normalize_dob(data.get("dob")), data.get("pob", ""), data.get("occupation", ""),
                data.get("id_type", "អត្តសញ្ញាណប័ណ្ណ"), data.get("id_number", ""), int(data.get("family_members", 1)),
                data.get("customer_type", "បុគ្គលមិនជាប់អាករ"), 1 if data.get("is_poor_family") else 0,
                data.get("representative", ""), data.get("account_number", ""),
                province, district, commune, village, data.get("zone", "តំបន់ ១"), house, street,
                data.get("pole_no", ""), data.get("box_no", ""), data.get("breaker", "20A"),
                data.get("phase", "1-Phase (220V)"), data.get("tariff_type", "tiered"), photo_path
            ])
            cur.execute("SELECT @@IDENTITY")
            new_id = int(cur.fetchone()[0])
        else:
            cur.execute("""
                INSERT INTO Customers (
                    FullName, PhoneNumber, Address, Status,
                    CustomerCode, Title, LastName, FirstName, LastNameEn, FirstNameEn,
                    Gender, DOB, POB, Occupation, IDType, IDNumber, FamilyMembers,
                    CustomerType, IsPoorFamily, Representative, AccountNumber,
                    Province, District, Commune, Village, Zone, HouseNo, StreetNo,
                    PoleNo, BoxNo, Breaker, Phase, TariffType, PhotoPath
                )
                VALUES (
                    ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?
                )
            """, [
                full_name, phone, final_addr, 1 if data.get("status", True) else 0,
                code, data.get("title", "លោក"), last_name, first_name, data.get("last_name_en", ""), data.get("first_name_en", ""),
                data.get("gender", "ប្រុស"), normalize_dob(data.get("dob")), data.get("pob", ""), data.get("occupation", ""),
                data.get("id_type", "អត្តសញ្ញាណប័ណ្ណ"), data.get("id_number", ""), int(data.get("family_members", 1)),
                data.get("customer_type", "បុគ្គលមិនជាប់អាករ"), 1 if data.get("is_poor_family") else 0,
                data.get("representative", ""), data.get("account_number", ""),
                province, district, commune, village, data.get("zone", "តំបន់ ១"), house, street,
                data.get("pole_no", ""), data.get("box_no", ""), data.get("breaker", "20A"),
                data.get("phase", "1-Phase (220V)"), data.get("tariff_type", "tiered"), photo_path
            ])
            new_id = cur.lastrowid

        conn.commit()
        conn.close()
        return new_id

    @classmethod
    def update(cls, customer_id: int, data: dict):
        last_name = data.get("last_name", "").strip()
        first_name = data.get("first_name", "").strip()
        full_name = f"{last_name} {first_name}".strip() or last_name or data.get("full_name", "").strip()
        phone = data.get("phone_number", "").strip()
        
        house = data.get("house_no", "").strip()
        street = data.get("street_no", "").strip()
        village = data.get("village", "").strip()
        commune = data.get("commune", "").strip()
        district = data.get("district", "").strip()
        province = data.get("province", "").strip()
        custom_addr = data.get("address", "").strip()

        addr_parts = []
        if house: addr_parts.append(f"ផ្ទះលេខ {house}")
        if street: addr_parts.append(f"ផ្លូវលេខ {street}")
        if village: addr_parts.append(f"ភូមិ {village}")
        if commune: addr_parts.append(f"ឃុំ/សង្កាត់ {commune}")
        if district: addr_parts.append(f"ស្រុក/ក្រុង {district}")
        if province: addr_parts.append(f"ខេត្ត/រាជធានី {province}")
        computed_addr = ", ".join(addr_parts)
        final_addr = custom_addr if custom_addr else computed_addr

        code = data.get("customer_code", "")
        photo_path = save_base64_photo(code, data.get("photo_data")) or data.get("photo_path")

        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE Customers
            SET FullName = ?, PhoneNumber = ?, Address = ?, Status = ?,
                CustomerCode = ?, Title = ?, LastName = ?, FirstName = ?, LastNameEn = ?, FirstNameEn = ?,
                Gender = ?, DOB = ?, POB = ?, Occupation = ?, IDType = ?, IDNumber = ?, FamilyMembers = ?,
                CustomerType = ?, IsPoorFamily = ?, Representative = ?, AccountNumber = ?,
                Province = ?, District = ?, Commune = ?, Village = ?, Zone = ?, HouseNo = ?, StreetNo = ?,
                PoleNo = ?, BoxNo = ?, Breaker = ?, Phase = ?, TariffType = ?,
                PhotoPath = COALESCE(?, PhotoPath)
            WHERE CustomerID = ?
        """, [
            full_name, phone, final_addr, 1 if data.get("status", True) else 0,
            code, data.get("title", "លោក"), last_name, first_name,
            data.get("last_name_en", ""), data.get("first_name_en", ""),
            data.get("gender", "ប្រុស"), normalize_dob(data.get("dob")), data.get("pob", ""), data.get("occupation", ""),
            data.get("id_type", "អត្តសញ្ញាណប័ណ្ណ"), data.get("id_number", ""), int(data.get("family_members", 1)),
            data.get("customer_type", "បុគ្គលមិនជាប់អាករ"), 1 if data.get("is_poor_family") else 0,
            data.get("representative", ""), data.get("account_number", ""),
            province, district, commune, village, data.get("zone", "តំបន់ ១"), house, street,
            data.get("pole_no", ""), data.get("box_no", ""), data.get("breaker", "20A"),
            data.get("phase", "1-Phase (220V)"), data.get("tariff_type", "tiered"),
            photo_path,
            customer_id
        ])
        conn.commit()
        affected = cur.rowcount
        conn.close()
        return affected > 0

    @classmethod
    def delete(cls, customer_id):
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM Customers WHERE CustomerID = ?", [customer_id])
        conn.commit()
        affected = cur.rowcount
        conn.close()
        return affected > 0


class MeterReadingService:
    @classmethod
    def get_latest_reading(cls, customer_id: int) -> float:
        conn = db.get_connection()
        cur = conn.cursor()
        sql = """
            SELECT CurrentReading 
            FROM MeterReadings 
            WHERE CustomerID = ? 
            ORDER BY BillingMonth DESC, ReadingID DESC
        """
        if db.is_sql_server:
            sql = f"SELECT TOP 1 CurrentReading FROM MeterReadings WHERE CustomerID = ? ORDER BY BillingMonth DESC, ReadingID DESC"
        else:
            sql = f"{sql} LIMIT 1"

        cur.execute(sql, [customer_id])
        r = cur.fetchone()
        conn.close()
        if r and r[0] is not None:
            return float(r[0])
        return 0.0

    @classmethod
    def get_recent(cls, count=25):
        conn = db.get_connection()
        cur = conn.cursor()
        if db.is_sql_server:
            sql = f"""
                SELECT TOP (?)
                    r.ReadingID, r.CustomerID, c.FullName, r.BillingMonth,
                    r.PreviousReading, r.CurrentReading, r.UsageKWh, r.RecordedDate
                FROM MeterReadings r
                INNER JOIN Customers c ON r.CustomerID = c.CustomerID
                ORDER BY r.ReadingID DESC
            """
            cur.execute(sql, [count])
        else:
            sql = f"""
                SELECT 
                    r.ReadingID, r.CustomerID, c.FullName, r.BillingMonth,
                    r.PreviousReading, r.CurrentReading, r.UsageKWh, r.RecordedDate
                FROM MeterReadings r
                INNER JOIN Customers c ON r.CustomerID = c.CustomerID
                ORDER BY r.ReadingID DESC
                LIMIT ?
            """
            cur.execute(sql, [count])

        rows = cur.fetchall()
        readings = []
        for r in rows:
            readings.append({
                "reading_id": r[0],
                "customer_id": r[1],
                "customer_name": r[2],
                "billing_month": str(r[3])[:7] if r[3] else "",
                "previous_reading": float(r[4]),
                "current_reading": float(r[5]),
                "usage_kwh": float(r[6]),
                "recorded_date": str(r[7])[:16] if r[7] else ""
            })
        conn.close()
        return readings

    @classmethod
    def save_reading_and_invoice(cls, customer_id, billing_month, prev_reading, curr_reading, rate_per_kwh, total_amount):
        usage_kwh = curr_reading - prev_reading
        conn = db.get_connection()
        cur = conn.cursor()
        try:
            # 1. Insert MeterReading
            cur.execute(
                """
                INSERT INTO MeterReadings (CustomerID, BillingMonth, PreviousReading, CurrentReading, UsageKWh)
                VALUES (?, ?, ?, ?, ?)
                """,
                [customer_id, billing_month, prev_reading, curr_reading, usage_kwh]
            )
            if db.is_sql_server:
                cur.execute("SELECT @@IDENTITY")
                reading_id = int(cur.fetchone()[0])
            else:
                reading_id = cur.lastrowid

            # 2. Insert Invoice
            cur.execute(
                """
                INSERT INTO Invoices (ReadingID, RatePerKWh, TotalAmount, IsPaid)
                VALUES (?, ?, ?, 0)
                """,
                [reading_id, rate_per_kwh, total_amount]
            )
            if db.is_sql_server:
                cur.execute("SELECT @@IDENTITY")
                invoice_id = int(cur.fetchone()[0])
            else:
                invoice_id = cur.lastrowid

            conn.commit()
            return reading_id, invoice_id
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


class DashboardService:
    @classmethod
    def get_stats(cls):
        conn = db.get_connection()
        cur = conn.cursor()

        # Customers count
        cur.execute("SELECT COUNT(*), SUM(CASE WHEN Status = 1 THEN 1 ELSE 0 END) FROM Customers")
        c_row = cur.fetchone()
        total_customers = c_row[0] or 0
        active_customers = c_row[1] or 0

        # Invoices Unpaid
        cur.execute("SELECT COUNT(*), SUM(TotalAmount) FROM Invoices WHERE IsPaid = 0")
        u_row = cur.fetchone()
        unpaid_count = u_row[0] or 0
        unpaid_amount = float(u_row[1] or 0)

        # Revenue Paid
        cur.execute("SELECT SUM(TotalAmount) FROM Invoices WHERE IsPaid = 1")
        rev_row = cur.fetchone()
        paid_revenue = float(rev_row[0] or 0)

        # Total kWh
        cur.execute("SELECT SUM(UsageKWh) FROM MeterReadings")
        kwh_row = cur.fetchone()
        total_kwh = float(kwh_row[0] or 0)

        conn.close()

        return {
            "total_customers": total_customers,
            "active_customers": active_customers,
            "unpaid_count": unpaid_count,
            "unpaid_amount": unpaid_amount,
            "paid_revenue": paid_revenue,
            "total_kwh": total_kwh,
            "is_sql_server": db.is_sql_server
        }


from werkzeug.security import generate_password_hash, check_password_hash

class UserService:
    @classmethod
    def register(cls, username, password, full_name, role="Staff"):
        username = (username or "").strip().lower()
        full_name = (full_name or "").strip()
        if not username or not password or not full_name:
            return False, "សូមបំពេញព័ត៌មានចាំបាច់ទាំងអស់ (Username, Password, ឈ្មោះពេញ)!"
        if len(password) < 4:
            return False, "ពាក្យសម្ងាត់ត្រូវមានយ៉ាងតិច ៤ តួអក្សរឡើងទៅ!"
        
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT UserID FROM Users WHERE LOWER(Username) = ?", [username])
        if cur.fetchone():
            conn.close()
            return False, f"ឈ្មោះគណនី '{username}' នេះមានរួចហើយ! សូមជ្រើសរើសឈ្មោះផ្សេង។"

        pw_hash = generate_password_hash(password)
        cur.execute(
            "INSERT INTO Users (Username, PasswordHash, FullName, Role) VALUES (?, ?, ?, ?)",
            [username, pw_hash, full_name, role]
        )
        new_id = cur.lastrowid
        conn.commit()
        conn.close()
        return True, new_id

    @classmethod
    def authenticate(cls, username, password):
        username = (username or "").strip().lower()
        if not username or not password:
            return None, "សូមបញ្ចូលឈ្មោះគណនី និងពាក្យសម្ងាត់!"
        
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT UserID, Username, PasswordHash, FullName, Role FROM Users WHERE LOWER(Username) = ?", [username])
        user_row = cur.fetchone()
        conn.close()

        if not user_row:
            return None, "ឈ្មោះគណនី ឬពាក្យសម្ងាត់មិនត្រឹមត្រូវទេ!"
        
        pw_hash = user_row["PasswordHash"] if hasattr(user_row, "keys") else user_row[2]
        
        valid = False
        try:
            valid = check_password_hash(pw_hash, password)
        except Exception:
            import hashlib
            valid = (hashlib.sha256(password.encode()).hexdigest() == pw_hash)

        if not valid:
            return None, "ឈ្មោះគណនី ឬពាក្យសម្ងាត់មិនត្រឹមត្រូវទេ!"

        return {
            "user_id": user_row["UserID"] if hasattr(user_row, "keys") else user_row[0],
            "username": user_row["Username"] if hasattr(user_row, "keys") else user_row[1],
            "full_name": user_row["FullName"] if hasattr(user_row, "keys") else user_row[3],
            "role": user_row["Role"] if hasattr(user_row, "keys") else user_row[4],
        }, None

    @classmethod
    def get_by_id(cls, user_id):
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT UserID, Username, FullName, Role FROM Users WHERE UserID = ?", [user_id])
        r = cur.fetchone()
        conn.close()
        if r:
            return {
                "user_id": r["UserID"] if hasattr(r, "keys") else r[0],
                "username": r["Username"] if hasattr(r, "keys") else r[1],
                "full_name": r["FullName"] if hasattr(r, "keys") else r[2],
                "role": r["Role"] if hasattr(r, "keys") else r[3],
            }
        return None

    @classmethod
    def get_all(cls):
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT UserID, Username, FullName, Role, CreatedAt FROM Users ORDER BY UserID ASC")
        rows = cur.fetchall()
        conn.close()
        users = []
        for r in rows:
            users.append({
                "user_id": r["UserID"] if hasattr(r, "keys") else r[0],
                "username": r["Username"] if hasattr(r, "keys") else r[1],
                "full_name": r["FullName"] if hasattr(r, "keys") else r[2],
                "role": r["Role"] if hasattr(r, "keys") else r[3],
                "created_at": str(r["CreatedAt"] if hasattr(r, "keys") else r[4])[:19]
            })
        return users

    @classmethod
    def update_role(cls, user_id, new_role):
        allowed_roles = ["Admin", "Staff", "Accountant"]
        if new_role not in allowed_roles:
            return False, "តួនាទីមិនត្រឹមត្រូវទេ!"
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE Users SET Role = ? WHERE UserID = ?", [new_role, user_id])
        conn.commit()
        conn.close()
        return True, "បានកែប្រែតួនាទីដោយជោគជ័យ!"

    @classmethod
    def update_user(cls, user_id, full_name, role):
        full_name = (full_name or "").strip()
        if not full_name:
            return False, "សូមបញ្ចូលឈ្មោះពេញ!"
        allowed_roles = ["Admin", "Staff", "Accountant"]
        if role not in allowed_roles:
            role = "Staff"
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE Users SET FullName = ?, Role = ? WHERE UserID = ?", [full_name, role, user_id])
        conn.commit()
        conn.close()
        return True, "បានកែប្រែព័ត៌មានដោយជោគជ័យ!"

    @classmethod
    def reset_password(cls, user_id, new_password):
        if not new_password or len(new_password) < 4:
            return False, "ពាក្យសម្ងាត់ថ្មីត្រូវមានយ៉ាងតិច ៤ តួអក្សរឡើងទៅ!"
        pw_hash = generate_password_hash(new_password)
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE Users SET PasswordHash = ? WHERE UserID = ?", [pw_hash, user_id])
        conn.commit()
        conn.close()
        return True, "បានកំណត់ពាក្យសម្ងាត់ថ្មីដោយជោគជ័យ!"

    @classmethod
    def delete(cls, user_id, current_admin_id):
        if int(user_id) == int(current_admin_id):
            return False, "លោកអ្នកមិនអាចលុបគណនីផ្ទាល់ខ្លួនដែលកំពុងប្រើប្រាស់បានទេ!"
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM Users WHERE UserID = ?", [user_id])
        rows_affected = cur.rowcount
        conn.commit()
        conn.close()
        if rows_affected > 0:
            return True, "បានលុបអ្នកប្រើប្រាស់ដោយជោគជ័យ!"
        return False, "រកមិនឃើញអ្នកប្រើប្រាស់ដែលត្រូវលុបទេ!"

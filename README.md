# ⚡ E-POWER: ប្រព័ន្ធគ្រប់គ្រងការប្រើប្រាស់អគ្គិសនី (Electricity Billing System)

ប្រព័ន្ធគ្រប់គ្រងការប្រើប្រាស់អគ្គិសនី (Electricity Billing System) ត្រូវបានបង្កើតឡើងជា **Python Web Application (Flask + Modern HTML5/CSS3/JS + Microsoft SQL Server / SQLite)** ស្របតាមរូបមន្តគណនាតាមកាំតម្លៃ (Tiered Electricity Tariffs) និងទម្រង់បញ្ចូលអតិថិជនជាក់ស្តែង។

---

## 🚀 របៀបដំណើរការរហ័ស (1-Click Run with run.bat)

អ្នកគ្រាន់តែចុចពីរដង (**Double-click**) លើ file **[run.bat](file:///c:/Users/Administrator/Desktop/E-Power/run.bat)** នោះកម្មវិធីនឹង៖
1. ចាប់ផ្តើម **Python Web Server** ដោយស្វ័យប្រវត្តិ
2. បើក **Web Browser** ចូលទៅកាន់ **http://127.0.0.1:5050** ដោយផ្ទាល់ភ្លាមៗ!

ឬដំណើរការតាម Terminal៖
```powershell
python app.py
```

---

## 🌟 លក្ខណៈពិសេសចម្បងនៃប្រព័ន្ធ (Key Features)

### ១. ផ្ទាំងគ្រប់គ្រងទូទៅ (Dashboard - `/dashboard`)
- KPI Stat Cards: អតិថិជនសរុប (សកម្ម/អសកម្ម), វិក័យបត្រមិនទាន់បង់, ចំណូលប្រមូលបាន, ថាមពលអគ្គិសនីសរុប (kWh)
- Banner បង្ហាញព័ត៌មានអត្រាតម្លៃភ្លើងតាមកាំ (Tier 1 vs Tier 2)
- តារាងវិក័យបត្រចុងក្រោយ ជាមួយប៊ូតុង "💳 បង់" និង "🖨️ បោះពុម្ព"

### ២. គ្រប់គ្រងព័ត៌មានអតិថិជន (Customers - `/customers`)
- **ទម្រង់បញ្ចូលអតិថិជនតាមគំរូជាក់ស្តែង (Tabs & Multi-columns)**៖
  - **Tab ១: ព័ត៌មានទូទៅ**៖
    - ឆ្វេង: ងារ*, គោត្តនាម*, នាម, ថ្ងៃខែឆ្នាំកំណើត, កន្លែងកំណើត, ប្រភេទអត្តសញ្ញាណ, អត្តសញ្ញាណ*, អ្នកតំណាង
    - កណ្តាល: លេខកូដ*, គោត្តនាមឡាតាំង, នាមឡាតាំង, ភេទ*, មុខរបរ, ចំនួនគ្រួសារ*, ប្រភេទអតិថិជន*, គ្រួសារក្រីក្រ (Checkbox)
    - ស្តាំ: ស៊ុមដាក់ **រូបថតអតិថិជន** និងប៊ូតុងជ្រើសរើសរូបភាព
    - ផ្នែកខាងក្រោម (អាសយដ្ឋានទំនាក់ទំនង): លេខទូរស័ព្ទ*, លេខគណនី, ខេត្ត/រាជធានី*, ស្រុក/ក្រុង*, ឃុំ/សង្កាត់*, ភូមិ/ក្រុម*, តំបន់*, ផ្ទះលេខ, ផ្លូវលេខ, អាសយដ្ឋាន
  - **Tab ២: ព័ត៌មានការប្រើប្រាស់**៖ ប្រភេទតំណភ្ជាប់ (1-Phase/3-Phase), លេខបង្គោលភ្លើង, លេខប្រអប់កុងទ័រ, ទំហំឌីសង់ទ័រ, កាំតម្លៃ
- របារ **ស្វែងរក (Search)** តាមឈ្មោះ លេខទូរស័ព្ទ ឬអាសយដ្ឋាន
- មុខងារ **Pagination (បែងចែកទំព័រ)** ងាយស្រួលគ្រប់គ្រងទិន្នន័យច្រើន

### ៣. កត់ត្រាលេខកុងទ័រ & គណនាថ្លៃ (Meter Reading - `/meter-reading`)
- ជ្រើសរើសអតិថិជន ➔ **ប្រព័ន្ធទាញយក Previous Reading (លេខកុងទ័រចាស់) ដោយស្វ័យប្រវត្តិតាមរយៈ AJAX**
- បញ្ចូលលេខកុងទ័រថ្មី ➔ **JavaScript គណនា `UsageKWh = Current - Previous` និងតម្លៃភ្លើងតាមកាំភ្លាមៗ (Real-time)**
- Live Preview Box: បង្ហាញការបំបែកកាំ (0-50 kWh @ 400៛ និង >50 kWh @ 600៛) និងទឹកប្រាក់សរុប (៛ និង $)
- Validation ការពារមិនឱ្យលេខកុងទ័រថ្មីតូចជាងលេខចាស់
- ប៊ូតុងរក្សាទុក៖ បញ្ចូលកុងទ័រ និងបង្កើតវិក័យបត្រភ្លាមៗ ព្រមទាំងផ្តល់ជម្រើសបោះពុម្ពវិក័យបត្រ

### ៤. វិក័យបត្រ & ការទូទាត់ប្រាក់ (Billing - `/billing`)
- តម្រងវិក័យបត្រ (មិនទាន់បង់ / បង់រួច / ទាំងអស់)
- ប៊ូតុង **"Pay"** សម្រាប់កត់ត្រាការបង់ប្រាក់ (`IsPaid = 1` ជាមួយកាលបរិច្ឆេទទូទាត់)
- ប៊ូតុង **"Print"** បើកមើល និងបោះពុម្ពវិក័យបត្រ

### ៥. ទម្រង់វិក័យបត្រផ្លូវការ (Printable Official Invoice - `/invoice/<id>/print`)
- ទម្រង់វិក័យបត្រអគ្គិសនីផ្លូវការទ្វេភាសា (ខ្មែរ/អង់គ្លេស)
- មានព័ត៌មានអតិថិជន, លេខកុងទ័រចាស់-ថ្មី, គីឡូវ៉ាត់ប្រើប្រាស់, តារាងកាំតម្លៃ
- ត្រាផ្លូវការ **PAID (បៃតង)** ឬ **UNPAID (ក្រហម)**
- កន្លែងចុះហត្ថលេខាអតិថិជន និងបេឡាធិការ រៀបចំរួចជាស្រេចសម្រាប់បោះពុម្ព ឬ Save ជា PDF

---

## 💡 រូបមន្តគណនាថ្លៃភ្លើង (Tariff Calculation Formula)

```python
# គណនាចំនួនគីឡូវ៉ាត់ម៉ោង
usage_kwh = current_reading - previous_reading

# គណនាតាមកាំតម្លៃ (Tiered Rate Calculation)
if usage_kwh <= 50:
    total_amount = usage_kwh * 400  # ៥០ គីឡូដំបូង = ៤០០៛/kWh
else:
    tier1_cost = 50 * 400           # 20,000 KHR
    tier2_usage = usage_kwh - 50
    tier2_cost = tier2_usage * 600  # លើសពី ៥០ គីឡូ = ៦០០៛/kWh
    total_amount = tier1_cost + tier2_cost
```

---

## 🗄️ មូលដ្ឋានទិន្នន័យ (Database)

- **SQL Server Database**: `ElectricityBillingDB`
- **Script បង្កើត Database**: [Database/SetupDatabase.sql](file:///c:/Users/Administrator/Desktop/E-Power/Database/SetupDatabase.sql)
- តារាងសំខាន់ៗ: `Customers`, `MeterReadings`, `Invoices`
- មានប្រព័ន្ធ **SQLite Fallback ស្វ័យប្រវត្តិ** ប្រសិនបើម៉ាស៊ីនមិនទាន់បើក SQL Server។

---

## 📁 រចនាសម្ព័ន្ធ Project

```
E-Power/
├── run.bat                    # File ចុចដំណើរការផ្ទាល់ ១ ជំហាន (Launch & Open Browser)
├── app.py                     # Flask Web Application & API Routes
├── db.py                      # Database Manager (SQL Server & SQLite fallback)
├── services.py                # Business Logic (Tiered Tariff, CRUD, Meter Reading)
├── test_web.py                # Automated Unit Tests
├── templates/                 # HTML Templates
│   ├── base.html              # Layout មេ (Sidebar & Header)
│   ├── dashboard.html         # ផ្ទាំងគ្រប់គ្រងទូទៅ
│   ├── customers.html         # គ្រប់គ្រងអតិថិជន (Form តាមគំរូ & Pagination)
│   ├── meter_reading.html     # កត់ត្រាកុងទ័រ & គណនា Real-time
│   ├── billing.html           # វិក័យបត្រ, បង់ប្រាក់ & បោះពុម្ព
│   └── print_invoice.html     # ទម្រង់វិក័យបត្របោះពុម្ពផ្លូវការ
├── static/
│   ├── css/style.css          # Modern Vanilla CSS
│   └── js/app.js              # Real-time calculation, Modals & AJAX
└── Database/
    └── SetupDatabase.sql      # Database Schema & Seed Data
```

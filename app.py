import os
import calendar
from functools import wraps
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from services import CustomerService, MeterReadingService, BillingService, DashboardService, UserService
from db import db

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)
app.secret_key = "epower_secret_key_change_in_prod"
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

@app.context_processor
def inject_global_vars():
    return {
        "now": datetime.now(),
        "is_sql_server": db.is_sql_server,
        "current_user": {
            "user_id": session.get("user_id"),
            "username": session.get("username"),
            "full_name": session.get("full_name"),
            "role": session.get("role")
        } if session.get("user_id") else None
    }

from urllib.parse import parse_qs, urlencode

class VercelPathMiddleware:
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        query_string = environ.get("QUERY_STRING", "")
        if "__path=" in query_string:
            qs = parse_qs(query_string, keep_blank_values=True)
            if "__path" in qs:
                raw_path = qs.pop("__path")[0] or "/"
                if not raw_path.startswith("/"):
                    raw_path = "/" + raw_path
                while raw_path.startswith("//"):
                    raw_path = raw_path[1:]
                environ["PATH_INFO"] = raw_path
                environ["QUERY_STRING"] = urlencode(qs, doseq=True)
        return self.wsgi_app(environ, start_response)

app.wsgi_app = VercelPathMiddleware(app.wsgi_app)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            if request.path.startswith("/api/"):
                return jsonify({"success": False, "error": "សូមចូលគណនីជាមុនសិន (Unauthorized)!"}), 401
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return decorated_function

# --- Auth Routes ---

@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user, err_msg = UserService.authenticate(username, password)
        if user:
            session["user_id"] = user["user_id"]
            session["username"] = user["username"]
            session["full_name"] = user["full_name"]
            session["role"] = user["role"]
            next_url = request.args.get("next")
            if next_url and next_url.startswith("/"):
                return redirect(next_url)
            return redirect(url_for("dashboard"))
        else:
            error = err_msg

    return render_template("login.html", error=error)

@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    
    error = None
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if password != confirm_password:
            error = "ពាក្យសម្ងាត់ទាំងពីរមិនដូចគ្នាទេ!"
        else:
            ok, msg = UserService.register(username, password, full_name)
            if ok:
                user, _ = UserService.authenticate(username, password)
                if user:
                    session["user_id"] = user["user_id"]
                    session["username"] = user["username"]
                    session["full_name"] = user["full_name"]
                    session["role"] = user["role"]
                    return redirect(url_for("dashboard"))
                return redirect(url_for("login"))
            else:
                error = msg

    return render_template("register.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# --- Page Routes ---

@app.route("/")
@login_required
def index():
    return redirect(url_for("dashboard"))

@app.route("/dashboard")
@login_required
def dashboard():
    stats = DashboardService.get_stats()
    recent_invoices = BillingService.get_invoices("All")[:8]
    return render_template("dashboard.html", stats=stats, recent_invoices=recent_invoices, active_page="dashboard")

@app.route("/customers")
@login_required
def customers():
    search = request.args.get("search", "")
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 10))
    customer_list, total_records = CustomerService.get_paged(search, page, page_size)
    total_pages = max(1, (total_records + page_size - 1) // page_size)
    return render_template(
        "customers.html",
        customers=customer_list,
        search=search,
        page=page,
        page_size=page_size,
        total_records=total_records,
        total_pages=total_pages,
        active_page="customers"
    )

@app.route("/meter-reading")
@login_required
def meter_reading():
    active_customers = CustomerService.get_all_active()
    recent_readings = MeterReadingService.get_recent(25)
    current_month = datetime.now().strftime("%Y-%m")
    return render_template(
        "meter_reading.html",
        active_customers=active_customers,
        recent_readings=recent_readings,
        current_month=current_month,
        active_page="meter-reading"
    )

@app.route("/billing")
@login_required
def billing():
    status_filter = request.args.get("status", "Unpaid")
    search = request.args.get("search", "")
    invoices = BillingService.get_invoices(status_filter, search)
    total_amount = sum(inv["total_amount"] for inv in invoices)
    return render_template(
        "billing.html",
        invoices=invoices,
        status_filter=status_filter,
        search=search,
        total_amount=total_amount,
        active_page="billing"
    )

@app.route("/invoice/<int:invoice_id>/print")
@login_required
def print_invoice(invoice_id):
    invoice = BillingService.get_invoice_by_id(invoice_id)
    if not invoice:
        return "រកមិនឃើញវិក័យបត្រ (Invoice not found)", 404
    is_flat = False
    if invoice["usage_kwh"] > 0:
        flat_expected = round(invoice["usage_kwh"] * invoice["rate_per_kwh"])
        if abs(flat_expected - invoice["total_amount"]) < 5:
            is_flat = True
    breakdown = BillingService.get_tier_breakdown(invoice["usage_kwh"], rate_per_kwh=invoice["rate_per_kwh"], is_flat=is_flat)

    history_12m = BillingService.get_customer_usage_history_12m(invoice["customer_id"], invoice["billing_month"])

    b_month = invoice["billing_month"] or datetime.now().strftime("%Y-%m")
    try:
        dt = datetime.strptime(b_month, "%Y-%m")
        y = dt.year
        m = dt.month
        last_day = calendar.monthrange(y, m)[1]
        from_date = f"01-{m:02d}-{y}"
        to_date = f"{last_day:02d}-{m:02d}-{y}"
    except Exception:
        from_date = "01-08-2026"
        to_date = "31-08-2026"

    created_at_str = invoice["created_at"]
    try:
        c_dt = datetime.strptime(created_at_str[:10], "%Y-%m-%d")
        invoice_date = c_dt.strftime("%d-%m-%Y")
        start_pay_dt = c_dt + timedelta(days=5)
        due_dt = c_dt + timedelta(days=15)
        start_pay_date = start_pay_dt.strftime("%d-%m-%Y")
        due_date = due_dt.strftime("%d-%m-%Y")
    except Exception:
        invoice_date = datetime.now().strftime("%d-%m-%Y")
        start_pay_date = (datetime.now() + timedelta(days=5)).strftime("%d-%m-%Y")
        due_date = (datetime.now() + timedelta(days=15)).strftime("%d-%m-%Y")

    meter_no = invoice.get("box_no") or f"YE220{invoice['customer_id']:04d}"

    return render_template(
        "print_invoice.html",
        invoice=invoice,
        breakdown=breakdown,
        is_flat=is_flat,
        history_12m=history_12m,
        from_date=from_date,
        to_date=to_date,
        invoice_date=invoice_date,
        start_pay_date=start_pay_date,
        due_date=due_date,
        meter_no=meter_no
    )


# --- REST API Endpoints ---

@app.route("/api/customers/<int:customer_id>/latest-reading")
def api_latest_reading(customer_id):
    reading = MeterReadingService.get_latest_reading(customer_id)
    return jsonify({"customer_id": customer_id, "previous_reading": reading})

@app.route("/api/calculate", methods=["POST"])
def api_calculate():
    data = request.get_json() or {}
    prev = float(data.get("previous_reading", 0))
    curr = float(data.get("current_reading", 0))
    use_tiered = bool(data.get("use_tiered", True))
    flat_rate = float(data.get("flat_rate", 800))
    t1_limit = float(data.get("tier1_limit", 50))
    t1_rate = float(data.get("tier1_rate", 400))
    t2_rate = float(data.get("tier2_rate", 600))

    if curr < prev:
        return jsonify({"valid": False, "error": "លេខកុងទ័រថ្មី មិនអាចតូចជាងលេខកុងទ័រចាស់បានទេ!"})

    usage = curr - prev
    total = BillingService.calculate_total(usage, use_tiered, flat_rate, t1_limit, t1_rate, t2_rate)
    breakdown = BillingService.get_tier_breakdown(usage, flat_rate, t1_limit, t1_rate, t2_rate, is_flat=not use_tiered)

    return jsonify({
        "valid": True,
        "usage_kwh": usage,
        "total_amount": total,
        "total_usd": round(total / 4100, 2),
        "breakdown": breakdown
    })

@app.route("/api/customers/<int:customer_id>", methods=["GET"])
def api_get_customer(customer_id):
    cust = CustomerService.get_by_id(customer_id)
    if cust:
        return jsonify({"success": True, "customer": cust})
    return jsonify({"success": False, "error": "រកមិនឃើញអតិថិជន"}), 404

@app.route("/api/customers/next-code")
def api_next_customer_code():
    code = CustomerService.generate_next_code()
    return jsonify({"success": True, "next_code": code})

@app.route("/api/customers", methods=["POST"])
def api_add_customer():
    data = request.get_json() or {}
    last_name = data.get("last_name", "").strip() or data.get("full_name", "").strip()
    phone = data.get("phone_number", "").strip()

    if not last_name or not phone:
        return jsonify({"success": False, "error": "សូមបញ្ចូលគោត្តនាម និងលេខទូរស័ព្ទ!"}), 400

    new_id = CustomerService.add(data)
    return jsonify({"success": True, "customer_id": new_id, "message": "បានបន្ថែមអតិថិជនដោយជោគជ័យ!"})

@app.route("/api/customers/<int:customer_id>", methods=["POST", "PUT"])
def api_update_customer(customer_id):
    data = request.get_json() or {}
    last_name = data.get("last_name", "").strip() or data.get("full_name", "").strip()
    phone = data.get("phone_number", "").strip()

    if not last_name or not phone:
        return jsonify({"success": False, "error": "សូមបញ្ចូលគោត្តនាម និងលេខទូរស័ព្ទ!"}), 400

    ok = CustomerService.update(customer_id, data)
    return jsonify({"success": ok, "message": "បានកែប្រែព័ត៌មានអតិថិជនដោយជោគជ័យ!" if ok else "បរាជ័យក្នុងការកែប្រែ"})

@app.route("/api/customers/<int:customer_id>/delete", methods=["POST", "DELETE"])
def api_delete_customer(customer_id):
    ok = CustomerService.delete(customer_id)
    return jsonify({"success": ok, "message": "បានលុបអតិថិជនដោយជោគជ័យ!" if ok else "បរាជ័យក្នុងការលុប"})

@app.route("/api/meter-reading", methods=["POST"])
def api_save_meter_reading():
    data = request.get_json() or {}
    customer_id = int(data.get("customer_id", 0))
    billing_month_str = data.get("billing_month", "")
    prev_reading = float(data.get("previous_reading", 0))
    curr_reading = float(data.get("current_reading", 0))
    use_tiered = bool(data.get("use_tiered", True))
    flat_rate = float(data.get("flat_rate", 800))
    t1_limit = float(data.get("tier1_limit", 50))
    t1_rate = float(data.get("tier1_rate", 400))
    t2_rate = float(data.get("tier2_rate", 600))

    if customer_id <= 0:
        return jsonify({"success": False, "error": "សូមជ្រើសរើសអតិថិជន!"}), 400

    if curr_reading < prev_reading:
        return jsonify({"success": False, "error": "លេខកុងទ័រថ្មីមិនអាចតូចជាងលេខកុងទ័រចាស់បានទេ!"}), 400

    billing_month = f"{billing_month_str}-01" if len(billing_month_str) == 7 else billing_month_str
    usage = curr_reading - prev_reading
    total = BillingService.calculate_total(usage, use_tiered, flat_rate, t1_limit, t1_rate, t2_rate)
    rate_saved = flat_rate if not use_tiered else (t1_rate if usage <= t1_limit else round(total / usage, 1) if usage > 0 else t1_rate)

    try:
        reading_id, invoice_id = MeterReadingService.save_reading_and_invoice(
            customer_id, billing_month, prev_reading, curr_reading, rate_saved, total
        )
        return jsonify({
            "success": True,
            "reading_id": reading_id,
            "invoice_id": invoice_id,
            "usage_kwh": usage,
            "total_amount": total,
            "message": f"បានកត់ត្រាកុងទ័រ និងបង្កើតវិក័យបត្រ INV-{invoice_id:05d} ដោយជោគជ័យ!"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/invoices/<int:invoice_id>/pay", methods=["POST"])
def api_pay_invoice(invoice_id):
    ok = BillingService.mark_as_paid(invoice_id)
    return jsonify({
        "success": ok,
        "message": "បានទូទាត់ប្រាក់ជោគជ័យ!" if ok else "វិក័យបត្រនេះត្រូវបានទូទាត់រួចហើយ ឬរកមិនឃើញ"
    })

if __name__ == "__main__":
    # Run on port 5050 to ensure no conflict
    port = int(os.environ.get("PORT", 5050))
    print(f">> E-Power Web Application running at: http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)

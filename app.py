"""
College Cash – UPI Transaction Facilitation System
Flask Backend
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import mysql.connector
from mysql.connector import Error
from functools import wraps
import math

app = Flask(__name__)
app.secret_key = "college_cash_secret_2024"

# ─── DB CONFIG ───────────────────────────────────────────────────────────────
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",          # ← change to your MySQL root password
    "database": "college_cash"
}

def get_db():
    """Return a new MySQL connection."""
    return mysql.connector.connect(**DB_CONFIG)

# ─── AUTH DECORATOR ──────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

# ─── HAVERSINE DISTANCE (km) ─────────────────────────────────────────────────
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# ─── ROUTES ──────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

# ── Register ─────────────────────────────────────────────────────────────────
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name  = request.form["name"].strip()
        phone = request.form["phone"].strip()
        pwd   = request.form["password"].strip()

        if not name or not phone or not pwd:
            flash("All fields are required.", "danger")
            return render_template("register.html")

        try:
            conn = get_db()
            cur  = conn.cursor()
            cur.execute("SELECT user_id FROM users WHERE phone = %s", (phone,))
            if cur.fetchone():
                flash("Phone number already registered.", "danger")
                return render_template("register.html")

            cur.execute(
                "INSERT INTO users (name, phone, password) VALUES (%s, %s, %s)",
                (name, phone, pwd)
            )
            conn.commit()
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("login"))
        except Error as e:
            flash(f"Database error: {e}", "danger")
        finally:
            cur.close(); conn.close()

    return render_template("register.html")

# ── Login ─────────────────────────────────────────────────────────────────────
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        phone = request.form["phone"].strip()
        pwd   = request.form["password"].strip()
        try:
            conn = get_db()
            cur  = conn.cursor(dictionary=True)
            cur.execute(
                "SELECT * FROM users WHERE phone = %s AND password = %s",
                (phone, pwd)
            )
            user = cur.fetchone()
            if user:
                session["user_id"]   = user["user_id"]
                session["user_name"] = user["name"]
                flash(f"Welcome back, {user['name']}!", "success")
                return redirect(url_for("dashboard"))
            else:
                flash("Invalid phone or password.", "danger")
        except Error as e:
            flash(f"Database error: {e}", "danger")
        finally:
            cur.close(); conn.close()

    return render_template("login.html")

# ── Logout ────────────────────────────────────────────────────────────────────
@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))

# ── Dashboard ─────────────────────────────────────────────────────────────────
@app.route("/dashboard")
@login_required
def dashboard():
    try:
        conn = get_db()
        cur  = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT name, cash_balance, upi_balance FROM users WHERE user_id = %s",
            (session["user_id"],)
        )
        user = cur.fetchone()

        cur.execute(
            """SELECT r.request_id, r.request_type, r.amount, r.status, r.created_at
               FROM exchange_requests r
               WHERE r.user_id = %s
               ORDER BY r.created_at DESC LIMIT 5""",
            (session["user_id"],)
        )
        my_requests = cur.fetchall()

        cur.execute(
            """SELECT t.transaction_id, t.amount, t.transaction_time, t.status,
                      u1.name AS user1_name, u2.name AS user2_name
               FROM transactions t
               JOIN users u1 ON t.user1_id = u1.user_id
               JOIN users u2 ON t.user2_id = u2.user_id
               WHERE t.user1_id = %s OR t.user2_id = %s
               ORDER BY t.transaction_time DESC LIMIT 5""",
            (session["user_id"], session["user_id"])
        )
        recent_txns = cur.fetchall()
    finally:
        cur.close(); conn.close()

    return render_template("dashboard.html", user=user,
                           my_requests=my_requests, recent_txns=recent_txns)

# ── Create Request ────────────────────────────────────────────────────────────
@app.route("/create_request", methods=["GET", "POST"])
@login_required
def create_request():
    if request.method == "POST":
        req_type  = request.form["request_type"]
        amount    = float(request.form["amount"])
        latitude  = float(request.form.get("latitude",  12.9716))
        longitude = float(request.form.get("longitude", 77.5946))

        if amount <= 0:
            flash("Amount must be positive.", "danger")
            return render_template("create_request.html")

        try:
            conn = get_db()
            cur  = conn.cursor(dictionary=True)

            # Check sufficient balance
            cur.execute("SELECT cash_balance, upi_balance FROM users WHERE user_id = %s",
                        (session["user_id"],))
            bal = cur.fetchone()

            if req_type == "need_upi" and bal["cash_balance"] < amount:
                flash("Insufficient cash balance for this request.", "danger")
                return render_template("create_request.html")
            if req_type == "need_cash" and bal["upi_balance"] < amount:
                flash("Insufficient UPI balance for this request.", "danger")
                return render_template("create_request.html")

            cur.execute(
                """INSERT INTO exchange_requests
                   (user_id, request_type, amount, latitude, longitude)
                   VALUES (%s, %s, %s, %s, %s)""",
                (session["user_id"], req_type, amount, latitude, longitude)
            )
            conn.commit()
            flash("Request created successfully!", "success")
            return redirect(url_for("matches"))
        except Error as e:
            flash(f"Database error: {e}", "danger")
        finally:
            cur.close(); conn.close()

    return render_template("create_request.html")

# ── Nearby Matches ────────────────────────────────────────────────────────────
@app.route("/matches")
@login_required
def matches():
    RADIUS_KM = 5.0
    try:
        conn = get_db()
        cur  = conn.cursor(dictionary=True)

        # Get current user's open requests
        cur.execute(
            """SELECT * FROM exchange_requests
               WHERE user_id = %s AND status = 'open'""",
            (session["user_id"],)
        )
        my_requests = cur.fetchall()

        # Get all open requests from others
        cur.execute(
            """SELECT r.*, u.name AS requester_name, u.phone AS requester_phone
               FROM exchange_requests r
               JOIN users u ON r.user_id = u.user_id
               WHERE r.user_id != %s AND r.status = 'open'""",
            (session["user_id"],)
        )
        all_requests = cur.fetchall()

        # Match opposite types within radius
        matches_list = []
        for my_req in my_requests:
            opposite = "need_cash" if my_req["request_type"] == "need_upi" else "need_upi"
            for other in all_requests:
                if other["request_type"] != opposite:
                    continue
                if my_req["latitude"] and other["latitude"]:
                    dist = haversine(
                        float(my_req["latitude"]),  float(my_req["longitude"]),
                        float(other["latitude"]),   float(other["longitude"])
                    )
                else:
                    dist = 0.0   # treat missing coords as nearby (demo)
                if dist <= RADIUS_KM:
                    matches_list.append({
                        "my_request_id":    my_req["request_id"],
                        "my_type":          my_req["request_type"],
                        "their_request_id": other["request_id"],
                        "their_user_id":    other["user_id"],
                        "their_name":       other["requester_name"],
                        "their_phone":      other["requester_phone"],
                        "their_type":       other["request_type"],
                        "amount":           min(float(my_req["amount"]), float(other["amount"])),
                        "distance_km":      round(dist, 2)
                    })
    finally:
        cur.close(); conn.close()

    return render_template("matches.html",
                           my_requests=my_requests,
                           matches=matches_list)

# ── Confirm Transaction ───────────────────────────────────────────────────────
@app.route("/confirm_transaction", methods=["POST"])
@login_required
def confirm_transaction():
    my_req_id    = int(request.form["my_request_id"])
    their_req_id = int(request.form["their_request_id"])
    amount       = float(request.form["amount"])

    conn = get_db()
    cur  = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()

        # Fetch both requests
        cur.execute("SELECT * FROM exchange_requests WHERE request_id = %s AND status = 'open'",
                    (my_req_id,))
        my_req = cur.fetchone()
        cur.execute("SELECT * FROM exchange_requests WHERE request_id = %s AND status = 'open'",
                    (their_req_id,))
        their_req = cur.fetchone()

        if not my_req or not their_req:
            raise Exception("One or both requests are no longer available.")

        user1_id = my_req["user_id"]
        user2_id = their_req["user_id"]

        # Fetch balances
        cur.execute("SELECT cash_balance, upi_balance FROM users WHERE user_id = %s", (user1_id,))
        u1 = cur.fetchone()
        cur.execute("SELECT cash_balance, upi_balance FROM users WHERE user_id = %s", (user2_id,))
        u2 = cur.fetchone()

        # Determine who pays cash vs UPI
        # user1: need_upi → gives cash, gets UPI
        # user1: need_cash → gives UPI, gets cash
        if my_req["request_type"] == "need_upi":
            if u1["cash_balance"] < amount:
                raise Exception("Insufficient cash balance.")
            if u2["upi_balance"] < amount:
                raise Exception("Other user has insufficient UPI balance.")
            # user1 gives cash, user2 gives UPI
            cur.execute("UPDATE users SET cash_balance = cash_balance - %s WHERE user_id = %s", (amount, user1_id))
            cur.execute("UPDATE users SET upi_balance  = upi_balance  + %s WHERE user_id = %s", (amount, user1_id))
            cur.execute("UPDATE users SET upi_balance  = upi_balance  - %s WHERE user_id = %s", (amount, user2_id))
            cur.execute("UPDATE users SET cash_balance = cash_balance + %s WHERE user_id = %s", (amount, user2_id))
        else:
            if u1["upi_balance"] < amount:
                raise Exception("Insufficient UPI balance.")
            if u2["cash_balance"] < amount:
                raise Exception("Other user has insufficient cash balance.")
            cur.execute("UPDATE users SET upi_balance  = upi_balance  - %s WHERE user_id = %s", (amount, user1_id))
            cur.execute("UPDATE users SET cash_balance = cash_balance + %s WHERE user_id = %s", (amount, user1_id))
            cur.execute("UPDATE users SET cash_balance = cash_balance - %s WHERE user_id = %s", (amount, user2_id))
            cur.execute("UPDATE users SET upi_balance  = upi_balance  + %s WHERE user_id = %s", (amount, user2_id))

        # Mark requests as matched
        cur.execute("UPDATE exchange_requests SET status = 'matched' WHERE request_id IN (%s, %s)",
                    (my_req_id, their_req_id))

        # Insert transaction record
        cur.execute(
            "INSERT INTO transactions (user1_id, user2_id, amount, status) VALUES (%s, %s, %s, 'completed')",
            (user1_id, user2_id, amount)
        )

        conn.commit()
        flash(f"Transaction of ₹{amount:.2f} completed successfully!", "success")

    except Exception as e:
        conn.rollback()
        flash(f"Transaction failed: {e}", "danger")
    finally:
        cur.close(); conn.close()

    return redirect(url_for("transactions"))

# ── Wallet ────────────────────────────────────────────────────────────────────
@app.route("/wallet")
@login_required
def wallet():
    try:
        conn = get_db()
        cur  = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT name, phone, cash_balance, upi_balance FROM users WHERE user_id = %s",
            (session["user_id"],)
        )
        user = cur.fetchone()
    finally:
        cur.close(); conn.close()
    return render_template("wallet.html", user=user)

# ── Transaction History ───────────────────────────────────────────────────────
@app.route("/transactions")
@login_required
def transactions():
    try:
        conn = get_db()
        cur  = conn.cursor(dictionary=True)
        cur.execute(
            """SELECT t.transaction_id, t.amount, t.transaction_time, t.status,
                      u1.name AS user1_name, u2.name AS user2_name,
                      t.user1_id, t.user2_id
               FROM transactions t
               JOIN users u1 ON t.user1_id = u1.user_id
               JOIN users u2 ON t.user2_id = u2.user_id
               WHERE t.user1_id = %s OR t.user2_id = %s
               ORDER BY t.transaction_time DESC""",
            (session["user_id"], session["user_id"])
        )
        txns = cur.fetchall()
    finally:
        cur.close(); conn.close()
    return render_template("transactions.html", txns=txns,
                           current_user_id=session["user_id"])

# ── Cancel Request ────────────────────────────────────────────────────────────
@app.route("/cancel_request/<int:req_id>", methods=["POST"])
@login_required
def cancel_request(req_id):
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute(
            "UPDATE exchange_requests SET status = 'cancelled' WHERE request_id = %s AND user_id = %s",
            (req_id, session["user_id"])
        )
        conn.commit()
        flash("Request cancelled.", "info")
    finally:
        cur.close(); conn.close()
    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    app.run(debug=True)

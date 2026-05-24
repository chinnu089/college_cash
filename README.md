# 💸 College Cash – UPI Transaction Facilitation System
> A DBMS Mini Project | Flask + MySQL

---

## 📁 Folder Structure

```
college_cash/
├── app.py                  ← Flask backend (all routes + logic)
├── requirements.txt        ← Python dependencies
├── database.sql            ← MySQL schema + sample data
├── README.md               ← This file
├── static/
│   └── style.css           ← Global CSS
└── templates/
    ├── base.html           ← Shared nav layout
    ├── login.html
    ├── register.html
    ├── dashboard.html
    ├── create_request.html
    ├── matches.html
    ├── transactions.html
    └── wallet.html
```

---

## ⚙️ Prerequisites

- Python 3.8+
- MySQL 8.0+
- pip

---

## 🚀 Setup Instructions

### Step 1 – Clone / Download
Place the `college_cash/` folder wherever you like.

### Step 2 – Create a virtual environment (recommended)
```bash
cd college_cash
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### Step 3 – Install Python dependencies
```bash
pip install -r requirements.txt
```

### Step 4 – Set up MySQL database
Open MySQL Workbench or your terminal MySQL client and run:
```sql
SOURCE /path/to/college_cash/database.sql;
```
Or paste the contents of `database.sql` directly into your MySQL client.

### Step 5 – Configure DB credentials in app.py
Open `app.py` and update the `DB_CONFIG` dict:
```python
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "YOUR_MYSQL_PASSWORD",   # ← change this
    "database": "college_cash"
}
```

### Step 6 – Run the app
```bash
python app.py
```

### Step 7 – Open in browser
Visit: **http://127.0.0.1:5000**

---

## 🧪 Test Credentials (from sample data)

| Name          | Phone       | Password |
|---------------|-------------|----------|
| Arjun Sharma  | 9876543210  | pass123  |
| Priya Nair    | 9876543211  | pass123  |
| Rahul Verma   | 9876543212  | pass123  |
| Sneha Reddy   | 9876543213  | pass123  |
| Vikram Patel  | 9876543214  | pass123  |

---

## 📌 Pages & Routes

| Page              | URL                  | Description                        |
|-------------------|----------------------|------------------------------------|
| Login             | `/login`             | Authenticate existing user         |
| Register          | `/register`          | Create new account                 |
| Dashboard         | `/dashboard`         | Overview: wallet + requests        |
| Wallet            | `/wallet`            | Cash & UPI balance details         |
| New Request       | `/create_request`    | Post a cash↔UPI exchange request   |
| Nearby Matches    | `/matches`           | See matched users within 5 km      |
| Confirm Exchange  | POST `/confirm_transaction` | Executes balanced DB transaction |
| Transaction Hist. | `/transactions`      | Full history of all exchanges      |
| Logout            | `/logout`            | Clear session                      |

---

## 🗄️ Database Tables

| Table               | Purpose                              |
|---------------------|--------------------------------------|
| `users`             | Accounts with cash + UPI balances    |
| `exchange_requests` | Open / matched / cancelled requests  |
| `transactions`      | Completed exchange records           |

---

## 🔐 Key Features

- **Session-based auth** – login/logout with Flask sessions
- **Wallet balances** – cash_balance & upi_balance per user
- **Haversine matching** – finds users within 5 km radius
- **Atomic transactions** – MySQL commit/rollback on exchange
- **Balance validation** – prevents exchange if insufficient funds

---

## 📝 Notes for Viva

- The matching algorithm uses the **Haversine formula** to compute great-circle distance between lat/lon coordinates.
- Transactions use `conn.start_transaction()` + `conn.commit()` / `conn.rollback()` to ensure **ACID compliance**.
- Passwords are stored in plain text for simplicity (for production use `bcrypt` hashing).

# PharmaTrace 💊🔗
### *Low-Latency, Transparent Pharmaceutical Supply Chain Network (SCN)*

![Python](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python)
![Django](https://img.shields.io/badge/Django-5.2-green?logo=django)
![Database](https://img.shields.io/badge/Database-SQLite-lightgrey?logo=sqlite)
![Frontend](https://img.shields.io/badge/UI-Bootstrap%205%20%7C%20High%20Contrast-indigo)
![Security](https://img.shields.io/badge/Security-SHA--256%20Receipts-red)
![License](https://img.shields.io/badge/License-MIT-blue)

---

## 📌 Executive Summary
**PharmaTrace** is a decentralized-style Supply Chain Network (SCN) portal engineered to connect **Manufacturers/Admins**, **Distributors**, and **Retail Pharmacies** into a single source of truth. 

Traditional pharmaceutical supply chains suffer from severe communication bottlenecks, dispatch delays, stock hoarding, and billing discrepancies. **PharmaTrace** solves this by:
1. **Minimizing Operational Latency:** Direct, frictionless order dispatching with automated SLA countdown timers.
2. **Enforcing Transparency:** An immutable, real-time SCN Transparency Ledger recording every state transition.
3. **Preventing Fraud & Overselling:** Strict separation of duties between dispatching distributors and receiving pharmacies.
4. **Verifiable Audit Trails:** Cryptographically hashed (SHA-256) digital receipts for proof-of-placement and proof-of-delivery.
5. **Production-Ready Security:** 1:1 unique email accounts with real-time SMTP-based OTP password recovery.

---

## 👥 Role-Based Permission Matrix (RBAC)

PharmaTrace implements strict separation of duties to maintain supply chain consensus:

| Operation | Retailer (Pharmacy) | Distributor | Admin (Superintendent) |
| :--- | :---: | :---: | :---: |
| **Browse Medicine Catalog** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Place SCN Orders** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Dispatch Order Consignments** | ❌ Blocked | ✅ Yes | ✅ Yes |
| **Confirm Physical Delivery (Received)** | ✅ Yes | ❌ Blocked | ✅ Yes |
| **Update Stock & Lead-Time SLAs** | ❌ Blocked | ✅ Yes | ✅ Yes |
| **Remove / Decommission Nodes** | ❌ Blocked | ❌ Blocked | ✅ Yes |
| **Access Django Admin Console** | ❌ Blocked | ❌ Blocked | ✅ Yes |

> **Four-Eyes Principle:** A distributor cannot falsely declare goods "Delivered," and a retailer cannot dispatch without distributor authorization.

---

## 🚀 Key Architectural Features

### 1. ⏱️ Low-Latency SCN Transparency Ledger
- Logs timestamps for `placed_at`, `dispatched_at`, and `delivered_at`.
- Automatically computes active transit latency:
  $$\text{Latency (Hours)} = \text{delivered\_at} - \text{dispatched\_at}$$
- Compares real-world delivery duration against the drug's manufacturer SLA.

### 2. 🧾 Tamper-Evident Digital Receipts (`RCP-ORD-SCN-xxxx`)
- Generates unique transaction certificates for both **Order Placed** and **Proof-of-Delivery**.
- Includes a deterministic **SHA-256 cryptographic verification digest** derived from order metadata, preventing silent database tampering.
- Native `@media print` CSS for one-click PDF invoice export.

### 3. 🔐 Enterprise Authentication & Real-World OTP Recovery
- **Dual-Identifier Login:** Authenticate using either registered **Username** or **Email**.
- **1-to-1 Email Mapping:** Every account is strictly tied to a unique email address for deterministic production deployments.
- **SMTP TLS Dispatch:** Dispatches 6-digit cryptographic security tokens via Google SMTP, with on-screen demo resilience fallback banners.

---

## 🛠️ Technology Stack
- **Backend:** Python 3.12+, Django 5.2 (MVT Architecture)
- **Database:** Relational SQLite (supports drop-in PostgreSQL migration)
- **Authentication:** Custom Django Authentication Backend (`EmailBackend`) with `Q`-filter lookup & PBKDF2-SHA256 password hashing
- **Frontend:** HTML5, CSS3 (Modern, high-contrast accessible white design system), Bootstrap 5, FontAwesome 6
- **Mailing Engine:** Python `smtplib` over secure TLS (port 587)

---

## ⚡ Quickstart & Installation

### Option 1: 1-Click Launch (Windows)
Double-click `START_SERVER.bat` in the root folder. The script will:
- Check and free port 8000 if occupied.
- Launch the Django development server with auto-restart crash protection.

To stop the server, double-click `STOP_SERVER.bat`.

---

### Option 2: Manual Terminal Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Swastikpandya2357/PharmaTrace.git
   cd PharmaTrace
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Navigate to Django directory and apply migrations:**
   ```bash
   cd proj
   python manage.py migrate
   ```

5. **(Optional) Configure Environment Variables:**
   Copy `.env.example` to `.env` inside `proj/` and insert your Gmail App Password for live SMTP OTP delivery.

6. **Start the development server:**
   ```bash
   python manage.py runserver 127.0.0.1:8000
   ```
   Open **http://127.0.0.1:8000/** in your browser.

---

## 🔑 Default Credentials (Ready for Demonstration)

| Role | Username / Identifier | Email | Password |
| :--- | :--- | :--- | :--- |
| **Admin** | `Swastik Pandya` | `pandyaswastik2005@gmail.com` | `sompandya` |
| **Distributor** | `Vivek Joshi` | `12302110501083@gcet.ac.in` | *(Use account password or OTP reset)* |
| **Retailer** | `Swastik` | `swastikpandya2005@gmail.com` | *(Use account password or OTP reset)* |

*Django Admin URL:* [http://127.0.0.1:8000/admin/login/](http://127.0.0.1:8000/admin/login/)

---

## 🧪 Automated Testing
PharmaTrace includes automated unit and integration tests covering role-based dispatch rules, unique email constraints, and dual authentication:

```bash
cd proj
python manage.py test
```
```text
Creating test database for alias 'default'...
.....
----------------------------------------------------------------------
Ran 5 tests in 2.650s

OK
```

---

## 📂 Project Directory Structure
```text
PharmaTrace/
├── START_SERVER.bat            # 1-Click interactive server launcher with auto-restart
├── STOP_SERVER.bat             # 1-Click server process terminator
├── START_BACKGROUND.vbs        # Silent background launcher
├── requirements.txt            # Python dependencies
├── .gitignore                  # Git ignore rules (ignores .env and pycache)
├── README.md                   # Complete documentation
└── proj/                       # Core Django Project Directory
    ├── manage.py
    ├── proj/                   # Project configurations & URL routing
    │   ├── settings.py
    │   ├── urls.py
    │   └── wsgi.py
    ├── store/                  # SCN Core Application
    │   ├── models.py           # SCNProduct, SCNOrder, SCNLatencyLog, etc.
    │   ├── views.py            # RBAC workflows, OTP recovery, receipt engine
    │   ├── urls.py             # Route definitions
    │   ├── auth_backends.py    # Dual Username/Email authentication backend
    │   ├── tests.py            # Automated test suite
    │   ├── templates/          # High-contrast white HTML5 templates
    │   └── static/             # CSS styling, vendor assets
    └── initial_data.json       # Seeded database fixtures (common medicines)
```

---

## 📜 License
Distributed under the MIT License. See `LICENSE` for more information.

---

## 👤 Author
**Swastik Pandya**  
- **Email:** [pandyaswastik2005@gmail.com](mailto:pandyaswastik2005@gmail.com)  
- **GitHub:** [@Swastikpandya2357](https://github.com/Swastikpandya2357)

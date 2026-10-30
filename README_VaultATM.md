<div align="center">

# 🏦 VaultATM
### Automated ATM Transaction Simulator

**A modern, interactive ATM simulation built with Python, Streamlit, and SQLite.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![SQLite](https://img.shields.io/badge/Database-SQLite-003B57?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![License](https://img.shields.io/badge/Project-Educational-blue)](#-disclaimer)

*Simple banking simulation. Secure account access. Clear transaction tracking.*

</div>

---

## 📌 About the Project

**VaultATM** is an educational, end-to-end ATM transaction simulator that demonstrates core banking-style workflows in a web application. Users can sign in with a demo account or create a new account, check their balance, deposit simulated cash, withdraw funds, transfer funds between demo accounts, and review their transaction history.

The application is built with **Python and Streamlit**, with **SQLite** used to store account and transaction records locally. Its dark interface uses custom CSS for a modern, responsive visual experience.

> **Important:** VaultATM is a learning project. It is not connected to any real bank, ATM network, payment service, or real-money account.

## ✨ Features

- **Account registration** — create a demo account with a name and 4-digit PIN.
- **Account number generation** — generate a 10-digit account number for new accounts.
- **PIN-protected login** — PINs are stored as password hashes, not plain text.
- **Temporary login lockout** — repeated incorrect PIN attempts can temporarily lock an account.
- **Balance inquiry** — view the current available demo balance.
- **Cash deposit simulation** — add a simulated deposit to an account.
- **Cash withdrawal simulation** — withdraw funds subject to balance, denomination, and daily-limit checks.
- **Fund transfer simulation** — transfer demo funds between registered accounts.
- **Transaction history** — view recent deposits, withdrawals, and transfers.
- **CSV export** — download transaction history for further analysis.
- **Interactive dashboard** — quick actions, account overview, and recent activity.
- **Modern UI** — dark theme, gradient accents, glass-style panels, and responsive layout.

## 🧰 Tech Stack

| Technology | Purpose |
|---|---|
| Python | Application logic and transaction processing |
| Streamlit | Interactive web interface |
| SQLite | Local relational database |
| Werkzeug Security | PIN hashing and verification |
| HTML/CSS | Custom visual styling |
| Git & GitHub | Version control and project hosting |
| Streamlit Community Cloud | Optional deployment platform |

## 🗂️ Project Structure

```text
automated-atm-simulator/
├── streamlit_app.py   # Streamlit UI, authentication, and ATM workflows
├── requirements.txt   # Python dependencies
├── README.md          # Project documentation
├── .gitignore         # Excludes local and sensitive files
└── atm.db             # Local SQLite database created at runtime (do not commit)
```

## ⚙️ Getting Started

### Prerequisites

- Python 3.10 or later recommended
- Git (optional, for cloning the repository)
- VS Code or another Python editor

### 1. Clone the repository

Replace `YOUR_USERNAME` with the GitHub account or organization that hosts this project.

```bash
git clone https://github.com/YOUR_USERNAME/automated-atm-simulator.git
cd automated-atm-simulator
```

Alternatively, download the repository as a ZIP and extract it.

### 2. Create a virtual environment

**Windows PowerShell:**

```powershell
py -m venv .venv
```

If PowerShell blocks activation, you can run the environment's Python directly without activating it.

### 3. Install dependencies

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

If your virtual environment is activated, this also works:

```bash
python -m pip install -r requirements.txt
```

### 4. Run the application

```powershell
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

Streamlit will print a local URL, usually:

```text
http://localhost:8501
```

Open that address in your browser.

## 🧪 Demo Accounts

The application seeds demo accounts when the database is first initialized and contains no accounts.

| Account Number | PIN | Starting Balance |
|---|---:|---:|
| `1001001001` | `1234` | ₹25,000.00 |
| `1001001002` | `4321` | ₹12,000.00 |

You can also create a new account from the **Create account** tab.

**Note:** Demo data is created only when the database has no accounts. If you already have an `atm.db` file, its existing records will be used instead.

## 🔄 How It Works

1. **Sign in or register:** authenticate with a demo account or create a new one.
2. **Open the dashboard:** view your balance and recent transactions.
3. **Choose an operation:** deposit, withdraw, transfer, or view transaction history.
4. **Validate the operation:** the application checks relevant account, balance, and withdrawal rules.
5. **Save the result:** the account balance and transaction records are updated in SQLite.
6. **Export history:** download transaction history as a CSV file when available.

## 🗄️ Database Overview

The application uses two main SQLite tables:

### `accounts`

Stores the account ID, account number, account holder name, hashed PIN, balance, failed login attempts, temporary lock information, and creation timestamp.

### `transactions`

Stores the transaction ID, account ID, transaction type, amount, resulting balance, transaction note, and timestamp.

The SQLite database is created locally by the application. The `.gitignore` file excludes `atm.db` so personal/demo records are not accidentally committed to GitHub.

## ☁️ Deploy on Streamlit Community Cloud

1. Push the project files to a GitHub repository.
2. Open [Streamlit Community Cloud](https://share.streamlit.io/).
3. Sign in with GitHub and select **Create app**.
4. Choose the repository and deployment branch.
5. Set **Main file path** to `streamlit_app.py`.
6. Select **Deploy** and wait for the build to finish.

### Database persistence warning

This version uses a local SQLite file. On Streamlit Community Cloud, local files should not be treated as a durable production database; data may be lost when the app restarts, is rebuilt, or is redeployed. For persistent multi-user deployment, migrate the data layer to a managed database such as PostgreSQL (for example, Supabase or Neon), and configure credentials using the platform's secrets manager.

## 🔐 Security & Limitations

- PINs are hashed using Werkzeug's password-hashing utilities.
- The application is a demonstration and has not been designed or audited for production banking.
- Do not enter real bank credentials, real PINs, card numbers, or other sensitive financial information.
- The demo database is local and is not suitable for reliable multi-instance production deployment.
- Production use would require additional security controls, robust session protection, rate limiting, audit logging, secure database hosting, and professional security review.
- All deposits, withdrawals, and transfers are simulated. No real cash or money moves.

## 🛣️ Possible Future Improvements

- Migrate from SQLite to managed PostgreSQL for persistent cloud storage.
- Add downloadable, formatted transaction receipts.
- Add profile management and PIN change functionality.
- Add admin analytics and transaction summaries.
- Add automated unit and integration tests.
- Add deployment health checks and structured application logging.

## 👩‍💻 Developed By

**Sonali Bandari** · **Anjali Gupta**

*Developed as an educational project to demonstrate Python application development, database operations, authentication concepts, and interactive web interfaces.*

---

## 📄 Disclaimer

VaultATM is an educational ATM transaction simulator. It is not affiliated with, endorsed by, or connected to any bank or financial institution. It must not be used for real financial transactions.

<div align="center">

**Built with Python · Streamlit · SQLite**

</div>

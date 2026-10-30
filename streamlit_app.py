import os
import re
import secrets
import sqlite3
from datetime import datetime, date
from contextlib import contextmanager

import streamlit as st
from werkzeug.security import generate_password_hash, check_password_hash

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("ATM_DB_PATH", os.path.join(APP_DIR, "atm.db"))
DAILY_WITHDRAWAL_LIMIT = 20000.00
MAX_FAILED_ATTEMPTS = 3

st.set_page_config(
    page_title="VaultATM | Transaction Simulator",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
:root { color-scheme: dark; }
.stApp {
  background:
    radial-gradient(ellipse at 10% 5%, rgba(61,91,220,.22), transparent 32%),
    radial-gradient(ellipse at 90% 30%, rgba(22,180,210,.10), transparent 28%),
    linear-gradient(135deg,#070d1b 0%,#0a1225 52%,#080f20 100%);
  color: #edf3ff;
  font-family: 'DM Sans', sans-serif;
}
[data-testid="stHeader"] { background: rgba(7,13,27,.72); }
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, rgba(16,26,49,.98), rgba(8,15,31,.98));
  border-right: 1px solid rgba(169,192,255,.14);
}
h1,h2,h3 { font-family: 'Manrope', sans-serif; letter-spacing: -.6px; }
.hero-kicker { color:#91a9ff; font-size:.78rem; font-weight:800; letter-spacing:2.2px; }
.hero-title { font-family:'Manrope',sans-serif; font-size:clamp(2.5rem,5vw,4.4rem); line-height:1.05; font-weight:800; color:#f0f4ff; }
.hero-gradient { background:linear-gradient(90deg,#83a0ff,#5ce5ff);-webkit-background-clip:text;background-clip:text;color:transparent; }
.subtle { color:#a9b7d3; line-height:1.7; }
.glass-card {
  background:linear-gradient(145deg,rgba(21,34,64,.94),rgba(12,21,42,.9));
  border:1px solid rgba(169,192,255,.16); border-radius:22px; padding:24px;
  box-shadow:0 22px 70px rgba(0,0,0,.22),inset 0 1px 0 rgba(255,255,255,.04);
}
.balance-card {
  background:linear-gradient(115deg,#1c306a,#3152be 58%,#168da8);
  border:1px solid rgba(153,185,255,.27); border-radius:24px; padding:28px;
  box-shadow:0 20px 55px rgba(36,87,230,.18);
}
.pill { display:inline-block; border:1px solid rgba(127,157,255,.2); border-radius:999px;
  background:rgba(79,111,235,.12); color:#c5d3ff; padding:8px 12px; margin:4px 5px 4px 0; font-size:.82rem; }
.small-muted { color:#9caed0; font-size:.88rem; }
div.stButton > button, div.stFormSubmitButton > button {
  border-radius:12px; font-weight:700; border:1px solid rgba(255,255,255,.18);
  background:linear-gradient(105deg,#4267f5,#6c83ff 55%,#3f70ed); color:white;
  transition:transform .2s ease, box-shadow .2s ease;
}
div.stButton > button:hover, div.stFormSubmitButton > button:hover {
  transform:translateY(-2px); box-shadow:0 10px 25px rgba(61,94,234,.3); color:white;
}
[data-testid="stMetric"] {
  background:rgba(17,29,57,.75); border:1px solid rgba(169,192,255,.15);
  border-radius:16px; padding:16px;
}
[data-testid="stMetricValue"] { color:#f0f4ff; }
input, textarea { border-radius:10px!important; }
hr { border-color:rgba(169,192,255,.14); }
footer {visibility:hidden;}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def now():
    return datetime.now().isoformat(timespec="seconds")


@contextmanager
def db_connection():
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with db_connection() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_no TEXT UNIQUE NOT NULL,
            holder_name TEXT NOT NULL,
            pin_hash TEXT NOT NULL,
            balance REAL NOT NULL DEFAULT 0 CHECK(balance >= 0),
            failed_attempts INTEGER NOT NULL DEFAULT 0,
            locked_until TEXT,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            tx_type TEXT NOT NULL,
            amount REAL NOT NULL CHECK(amount > 0),
            balance_after REAL NOT NULL,
            note TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(account_id) REFERENCES accounts(id)
        );
        CREATE INDEX IF NOT EXISTS idx_transactions_account_date
        ON transactions(account_id, created_at DESC);
        """)
        if conn.execute("SELECT COUNT(*) AS n FROM accounts").fetchone()["n"] == 0:
            demo = [
                ("1001001001", "Demo Customer", "1234", 25000.00),
                ("1001001002", "Alex Morgan", "4321", 12000.00),
            ]
            for account_no, name, pin, balance in demo:
                conn.execute(
                    """INSERT INTO accounts(account_no,holder_name,pin_hash,balance,created_at)
                       VALUES(?,?,?,?,?)""",
                    (account_no, name, generate_password_hash(pin), balance, now())
                )


def get_account(account_id):
    with db_connection() as conn:
        return conn.execute("SELECT * FROM accounts WHERE id=?", (account_id,)).fetchone()


def get_transactions(account_id, limit=100):
    with db_connection() as conn:
        return conn.execute(
            "SELECT * FROM transactions WHERE account_id=? ORDER BY id DESC LIMIT ?",
            (account_id, limit)
        ).fetchall()


def record_tx(conn, account_id, tx_type, amount, balance_after, note):
    conn.execute(
        """INSERT INTO transactions(account_id,tx_type,amount,balance_after,note,created_at)
           VALUES(?,?,?,?,?,?)""",
        (account_id, tx_type, round(amount, 2), round(balance_after, 2), note, now())
    )


def parse_amount(value):
    try:
        amount = round(float(value), 2)
        if amount <= 0:
            return None
        return amount
    except (TypeError, ValueError):
        return None


def create_account(name, pin):
    name = name.strip()
    if not 2 <= len(name) <= 80:
        return False, "Name must contain 2–80 characters.", None
    if not re.fullmatch(r"\d{4}", pin):
        return False, "PIN must contain exactly 4 digits.", None
    with db_connection() as conn:
        for _ in range(30):
            account_no = "2" + "".join(secrets.choice("0123456789") for _ in range(9))
            if not conn.execute("SELECT 1 FROM accounts WHERE account_no=?", (account_no,)).fetchone():
                break
        else:
            return False, "Could not generate an account number. Try again.", None
        cur = conn.execute(
            """INSERT INTO accounts(account_no,holder_name,pin_hash,balance,created_at)
               VALUES(?,?,?,?,?)""",
            (account_no, name, generate_password_hash(pin), 0.0, now())
        )
        return True, f"Account created. Save this account number: {account_no}", cur.lastrowid


def authenticate(account_no, pin):
    with db_connection() as conn:
        account = conn.execute("SELECT * FROM accounts WHERE account_no=?", (account_no.strip(),)).fetchone()
        if not account:
            return False, "Invalid account number or PIN.", None
        if account["locked_until"]:
            locked = datetime.fromisoformat(account["locked_until"])
            if datetime.now() < locked:
                return False, "Account temporarily locked after failed attempts. Please try again later.", None
            conn.execute("UPDATE accounts SET failed_attempts=0,locked_until=NULL WHERE id=?", (account["id"],))
        if not check_password_hash(account["pin_hash"], pin):
            attempts = account["failed_attempts"] + 1
            locked_until = None
            if attempts >= MAX_FAILED_ATTEMPTS:
                from datetime import timedelta
                locked_until = (datetime.now() + timedelta(minutes=5)).isoformat(timespec="seconds")
            conn.execute("UPDATE accounts SET failed_attempts=?,locked_until=? WHERE id=?",
                         (attempts, locked_until, account["id"]))
            return False, "Invalid account number or PIN. Too many failures temporarily lock the account.", None
        conn.execute("UPDATE accounts SET failed_attempts=0,locked_until=NULL WHERE id=?", (account["id"],))
        return True, "Login successful.", account["id"]


def do_deposit(account_id, amount):
    with db_connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        account = conn.execute("SELECT * FROM accounts WHERE id=?", (account_id,)).fetchone()
        new_balance = round(account["balance"] + amount, 2)
        conn.execute("UPDATE accounts SET balance=? WHERE id=?", (new_balance, account_id))
        record_tx(conn, account_id, "DEPOSIT", amount, new_balance, "Simulated cash deposit")
    return new_balance


def do_withdraw(account_id, amount):
    with db_connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        account = conn.execute("SELECT * FROM accounts WHERE id=?", (account_id,)).fetchone()
        today = date.today().isoformat()
        daily = conn.execute(
            """SELECT COALESCE(SUM(amount),0) AS total FROM transactions
               WHERE account_id=? AND tx_type='WITHDRAWAL' AND substr(created_at,1,10)=?""",
            (account_id, today)
        ).fetchone()["total"]
        if amount % 100 != 0:
            return False, "For this simulator, withdrawals must be multiples of ₹100.", None
        if amount > account["balance"]:
            return False, "Insufficient balance.", None
        if daily + amount > DAILY_WITHDRAWAL_LIMIT:
            return False, "Daily withdrawal limit of ₹20,000 exceeded.", None
        new_balance = round(account["balance"] - amount, 2)
        conn.execute("UPDATE accounts SET balance=? WHERE id=?", (new_balance, account_id))
        record_tx(conn, account_id, "WITHDRAWAL", amount, new_balance, "ATM cash withdrawal")
    return True, "Withdrawal successful.", new_balance


def do_transfer(sender_id, recipient_no, amount):
    with db_connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        sender = conn.execute("SELECT * FROM accounts WHERE id=?", (sender_id,)).fetchone()
        recipient = conn.execute("SELECT * FROM accounts WHERE account_no=?", (recipient_no.strip(),)).fetchone()
        if not recipient:
            return False, "Recipient account not found.", None
        if recipient["id"] == sender_id:
            return False, "You cannot transfer to your own account.", None
        if sender["balance"] < amount:
            return False, "Insufficient balance.", None
        sender_balance = round(sender["balance"] - amount, 2)
        recipient_balance = round(recipient["balance"] + amount, 2)
        conn.execute("UPDATE accounts SET balance=? WHERE id=?", (sender_balance, sender_id))
        conn.execute("UPDATE accounts SET balance=? WHERE id=?", (recipient_balance, recipient["id"]))
        record_tx(conn, sender_id, "TRANSFER OUT", amount, sender_balance, f"To account ending {recipient_no[-4:]}")
        record_tx(conn, recipient["id"], "TRANSFER IN", amount, recipient_balance, f"From account ending {sender['account_no'][-4:]}")
    return True, "Transfer successful.", sender_balance


init_db()

if "account_id" not in st.session_state:
    st.session_state.account_id = None
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"
if "notice" not in st.session_state:
    st.session_state.notice = None

st.markdown("""
<div style="display:flex;align-items:center;gap:12px;margin:0 0 26px 0">
  <div style="width:43px;height:43px;border-radius:13px;background:linear-gradient(135deg,#7b9aff,#4267f5);display:grid;place-items:center;font-weight:900;font-size:22px;box-shadow:0 8px 25px #4267f544">V</div>
  <div><div style="font-family:Manrope,sans-serif;font-size:1.55rem;font-weight:800;line-height:1.1">VaultATM</div><div class="small-muted">AUTOMATED ATM TRANSACTION SIMULATOR</div></div>
</div>
""", unsafe_allow_html=True)

if st.session_state.notice:
    kind, msg = st.session_state.notice
    getattr(st, kind)(msg)
    st.session_state.notice = None

if not st.session_state.account_id:
    left, right = st.columns([1.1, 0.9], gap="large")
    with left:
        st.markdown('<div class="hero-kicker">SMART · SIMPLE · SIMULATED</div>', unsafe_allow_html=True)
        st.markdown('<div class="hero-title">Your money.<br><span class="hero-gradient">Your control.</span></div>', unsafe_allow_html=True)
        st.markdown('<p class="subtle">A modern ATM experience built with Python and Streamlit. Practice secure account access, deposits, withdrawals and transfers in a demo environment.</p>', unsafe_allow_html=True)
        st.markdown('<span class="pill">● PIN protection</span><span class="pill">● Account registration</span><span class="pill">● Transaction history</span>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.info("Educational simulator only — no real bank account or real money is involved.")
    with right:
        login_tab, signup_tab = st.tabs(["🔐 Sign in", "＋ Create account"])
        with login_tab:
            st.markdown("### Welcome back")
            st.caption("Enter your demo account credentials.")
            with st.form("login_form", clear_on_submit=False):
                account_no = st.text_input("Account number", placeholder="e.g. 1001001001")
                pin = st.text_input("4-digit PIN", type="password", max_chars=4, placeholder="Enter your PIN")
                submitted = st.form_submit_button("Access ATM →", use_container_width=True)
            if submitted:
                ok, message, account_id = authenticate(account_no, pin)
                if ok:
                    st.session_state.account_id = account_id
                    st.session_state.page = "Dashboard"
                    st.rerun()
                else:
                    st.error(message)
            with st.expander("Demo credentials"):
                st.code("Account: 1001001001  |  PIN: 1234\nAccount: 1001001002  |  PIN: 4321")
        with signup_tab:
            st.markdown("### Create your account")
            st.caption("New demo account starts with ₹0.")
            with st.form("register_form", clear_on_submit=True):
                name = st.text_input("Full name", placeholder="Enter your name")
                new_pin = st.text_input("Create 4-digit PIN", type="password", max_chars=4)
                confirm_pin = st.text_input("Confirm PIN", type="password", max_chars=4)
                registered = st.form_submit_button("Create demo account →", use_container_width=True)
            if registered:
                if new_pin != confirm_pin:
                    st.error("PIN and confirmation do not match.")
                else:
                    ok, message, new_id = create_account(name, new_pin)
                    if ok:
                        st.session_state.account_id = new_id
                        st.session_state.notice = ("success", message)
                        st.session_state.page = "Dashboard"
                        st.rerun()
                    else:
                        st.error(message)
else:
    account = get_account(st.session_state.account_id)
    if not account:
        st.session_state.account_id = None
        st.rerun()

    with st.sidebar:
        st.markdown("## 🏦 VaultATM")
        st.caption("DEMO ACCOUNT")
        st.markdown(f"**{account['holder_name']}**")
        st.code(f"•••• {account['account_no'][-4:]}")
        st.divider()
        pages = ["Dashboard", "Withdraw cash", "Deposit cash", "Transfer funds", "Transaction history"]
        selected = st.radio("Navigation", pages, index=pages.index(st.session_state.page) if st.session_state.page in pages else 0)
        st.session_state.page = selected
        st.divider()
        st.caption("Available balance")
        st.markdown(f"### ₹{account['balance']:,.2f}")
        if st.button("Log out", use_container_width=True):
            st.session_state.account_id = None
            st.session_state.page = "Dashboard"
            st.rerun()

    page = st.session_state.page
    account = get_account(st.session_state.account_id)

    if page == "Dashboard":
        st.markdown(f"## Hello, {account['holder_name']} 👋")
        st.markdown('<p class="subtle">Here is your demo account overview.</p>', unsafe_allow_html=True)
        st.markdown(f'<div class="balance-card"><div style="color:#d2dcff;font-size:.85rem;letter-spacing:1.4px;font-weight:700">AVAILABLE BALANCE</div><div style="font-size:clamp(2.5rem,5vw,3.7rem);font-weight:800;margin:10px 0">₹{account["balance"]:,.2f}</div><div style="color:#d2dcff">VAULTATM · DEMO ACCOUNT &nbsp; · &nbsp; •••• {account["account_no"][-4:]}</div></div>', unsafe_allow_html=True)
        st.markdown("### Quick actions")
        cols = st.columns(4)
        actions = [("↗", "Withdraw cash"), ("＋", "Deposit cash"), ("⇄", "Transfer funds"), ("≡", "Transaction history")]
        for col, (symbol, label) in zip(cols, actions):
            with col:
                if st.button(f"{symbol}  {label}", use_container_width=True):
                    st.session_state.page = label
                    st.rerun()
        st.markdown("### Recent activity")
        txs = get_transactions(account["id"], 5)
        if txs:
            st.dataframe([{"Type": t["tx_type"], "Amount (₹)": f'{t["amount"]:,.2f}', "Balance after (₹)": f'{t["balance_after"]:,.2f}', "Date": t["created_at"].replace("T", " "), "Details": t["note"]} for t in txs], use_container_width=True, hide_index=True)
        else:
            st.info("No transactions yet. Make your first transaction to see activity here.")

    elif page == "Withdraw cash":
        st.markdown("## ↗ Withdraw cash")
        st.caption("Withdrawals must be in multiples of ₹100. Daily limit: ₹20,000.")
        st.metric("Available balance", f'₹{account["balance"]:,.2f}')
        with st.form("withdraw_form"):
            amount_input = st.number_input("Amount (₹)", min_value=100, max_value=100000, value=500, step=100)
            confirm = st.form_submit_button("Confirm withdrawal →", use_container_width=True)
        if confirm:
            ok, msg, balance = do_withdraw(account["id"], float(amount_input))
            if ok:
                st.success(f"{msg} New balance: ₹{balance:,.2f}")
                st.rerun()
            else:
                st.error(msg)

    elif page == "Deposit cash":
        st.markdown("## ＋ Deposit cash")
        st.caption("Simulated cash deposit. Maximum ₹1,00,000 per transaction.")
        st.metric("Available balance", f'₹{account["balance"]:,.2f}')
        with st.form("deposit_form"):
            amount_input = st.number_input("Amount (₹)", min_value=1.0, max_value=100000.0, value=500.0, step=100.0)
            confirm = st.form_submit_button("Confirm deposit →", use_container_width=True)
        if confirm:
            balance = do_deposit(account["id"], float(amount_input))
            st.success(f"Deposit successful. New balance: ₹{balance:,.2f}")
            st.rerun()

    elif page == "Transfer funds":
        st.markdown("## ⇄ Transfer funds")
        st.caption("Transfers work only between demo accounts in this simulator.")
        st.metric("Available balance", f'₹{account["balance"]:,.2f}')
        with st.form("transfer_form"):
            target = st.text_input("Recipient account number", placeholder="Enter 10-digit demo account number")
            amount_input = st.number_input("Amount (₹)", min_value=1.0, max_value=100000.0, value=500.0, step=100.0)
            confirm = st.form_submit_button("Confirm transfer →", use_container_width=True)
        if confirm:
            amount = parse_amount(amount_input)
            ok, msg, balance = do_transfer(account["id"], target, amount)
            if ok:
                st.success(f"{msg} New balance: ₹{balance:,.2f}")
                st.rerun()
            else:
                st.error(msg)

    elif page == "Transaction history":
        st.markdown("## ≡ Transaction history")
        st.caption("Latest 100 transactions for your account.")
        txs = get_transactions(account["id"], 100)
        if txs:
            st.dataframe([{"Type": t["tx_type"], "Amount (₹)": f'{t["amount"]:,.2f}', "Balance after (₹)": f'{t["balance_after"]:,.2f}', "Date": t["created_at"].replace("T", " "), "Details": t["note"]} for t in txs], use_container_width=True, hide_index=True)
            csv_data = "Type,Amount,Balance After,Date,Details\n" + "\n".join(
                ",".join('"' + str(v).replace('"', '""') + '"' for v in [t["tx_type"], f'{t["amount"]:.2f}', f'{t["balance_after"]:.2f}', t["created_at"], t["note"] or ""])
                for t in txs
            )
            st.download_button("⬇ Download transaction history CSV", csv_data, file_name="vaultatm_transactions.csv", mime="text/csv")
        else:
            st.info("No transactions yet.")

    st.markdown("---")
    st.caption("VaultATM is an educational simulation. Do not enter real banking credentials or use it for real-money transactions.")

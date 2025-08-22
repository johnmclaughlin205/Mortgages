import re
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Optional, Dict, Any
import pandas as pd
import streamlit as st

DB_PATH = Path("mortgage_pipeline.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    with closing(get_conn()) as conn, conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                last_name TEXT NOT NULL,
                first_name TEXT NOT NULL,
                street TEXT NOT NULL,
                city TEXT NOT NULL,
                state TEXT NOT NULL,
                zip_code TEXT NOT NULL,
                loan_amount REAL NOT NULL,
                estimated_value REAL NOT NULL,
                occupancy_type TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
                );
            """
        )
        
        conn.execute(
            """CREATE INDEX IF NOT EXISTS idx_customers_state ON customers(state);"""
        )
        
        conn.execute(
            """CREATE INDEX IF NOT EXISTS idx_customers_last_name ON customers(last_name);"""
        )
        
def insert_customer(rec: Dict[str, Any]):
    with closing(get_conn()) as conn, conn:
        conn.execute(
            """
            INSERT INTO customers
               (last_name, first_name, street, city, state, zip_code,
               loan_amount, estimated_value, occupancy_type)
            VALUES
               (:last_name, :first_name, :street, :city, :state, :zip_code,
               :loan_amount, :estimated_value, :occupancy_type)
             """,
             rec,
        )

def delete_customer(row_id: int):
    with closing(get_conn()) as conn, conn:
        conn.execute("DELETE FROM customers WHERE id = ?;", (row_id,))

def fetch_customers(filters: Optional[Dict[str, str]] = None) -> pd.DataFrame:
    query = "SELECT id, last_name, first_name, street, city, state, zip_code, loan_amount, estimated_value, occupancy_type, created_at FROM customers"
    params = []
    where = []
    if filters:
        if filters.get("name"):
            where.append("(last_name LIKE ? OR first_name LIKE ?)")
            like = f"%{filters['name']}%"
            params.extend([like, like])
        if filters.get("city"):
            where.append("city LIKE ?")
            params.append(f"%{filters['city']}%")
        if filters.get("state"):
            where.append("state = ?")
            params.append(filters["state"].upper().strip())
        if where:
            query += " WHERE " + " AND ".join(where)
    query += " ORDER BY created_at DESC, id DESC"
    with closing(get_conn()) as conn:
        df = pd.read_sql_query(query, conn, params=params)
    return df

    # ---------- Validation ----------
STATE_RE = re.compile(r"^[A-Za-z]{2}$")
ZIP_RE = re.compile(r"^\d{5}(-\d{4})?$")

def validate_inputs(d: Dict[str, Any]) -> Optional[str]:
    if not STATE_RE.match(d["state"]):
        return "State must be a 2-letter code (e.g., AZ, CA)."
    if not ZIP_RE.match(d["zip_code"]):
        return "Zip Code must be 5 digits or ZIP+4 (e.g., 85212 or 85212-1234)."
    if float(d["loan_amount"]) <= 0:
        return "Loan amount must be greater than 0."
    if float(d["estimated_value"]) <= 0:
        return "Estimated value must be greater than 0."
    return None

st.set_page_config(page_title="John's Pipeline", page_icon="MeinBrooklyn03.jpg🏦", layout="wide")

# Sleek CSS (glassmorphism + subtle animations)
st.markdown(
    """
    <style>
      /* Global */
      .stApp {
        background: radial-gradient(1200px 800px at 10% 10%, rgba(58, 155, 246, 0.50), rgba(22,0,0,200)) ,
                    radial-gradient(1000px 700px at 90% 30%, rgba(13, 248, 136, 0.110), rgba(32,0,0,10));
        font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, "Apple Color Emoji","Segoe UI Emoji";
      }
      /* Card look for containers */
      .glass {
        background: rgba(255,255,255,0.55);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255,255,255,0.35);
        border-radius: 18px;
        padding: 18px 20px;
        box-shadow: 0 10px 30px rgba(2,6,23,0.08);
      }
      .title {
        font-weight: 800;
        letter-spacing: -0.02em;
        margin-bottom: 6px;
      }
      .subtitle {
        opacity: 0.8;
        margin-bottom: 16px;
      }
      /* Buttons */
      .stButton>button {
        border-radius: 12px;
        border: 1px solid rgba(59,130,246,0.25);
        padding: 10px 16px;
        transition: transform .05s ease, box-shadow .2s ease;
      }
      .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 8px 20px rgba(59,130,246,0.25);
      }
      /* Inputs */
      .stTextInput>div>div>input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] input {
        border-radius: 10px !important;
      }
      /* Dataframe header */
      .stDataFrame thead tr th {
        background: rgba(59,130,246,0.10) !important;
      }
      /* Metric cards */
      .metric {
        border-radius: 16px; padding: 16px;
        border: 1px solid rgba(0,0,0,0.05);
        background: rgba(255,255,255,0.7);
      }
    </style>
    """,
    unsafe_allow_html=True,
)

init_db()

# Header
st.markdown('<div class="glass">', unsafe_allow_html=True)
st.markdown(
    """
    <div>
      <h1 class="title">🏦 John's Mortgage Pipeline</h1>
      <div class="subtitle">Add borrowers, filter your pipeline, and export data. Powered by Python.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Top metrics
df_all = fetch_customers()
total_customers = len(df_all)
total_loan = float(df_all["loan_amount"].sum()) if total_customers else 0.0
avg_ltv = None
if total_customers:
    # simple proxy; you can replace with actual loan/value ratio calculation per row
    ltv_series = (df_all["loan_amount"] / df_all["estimated_value"]).clip(upper=5)
    avg_ltv = (ltv_series.mean() * 100)

m1, m2, m3 = st.columns(3)
with m1:
    st.markdown('<div class="metric">', unsafe_allow_html=True)
    st.metric("Total Customers", f"{total_customers:,}")
    st.markdown('</div>', unsafe_allow_html=True)
with m2:
    st.markdown('<div class="metric">', unsafe_allow_html=True)
    st.metric("Sum of Loan Amounts", f"${total_loan:,.0f}")
    st.markdown('</div>', unsafe_allow_html=True)
with m3:
    st.markdown('<div class="metric">', unsafe_allow_html=True)
    st.metric("Avg. LTV (est.)", f"{avg_ltv:.1f}%" if avg_ltv is not None else "—")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
st.write("")

# Layout: Form (left) | Table + filters (right)
left, right = st.columns([0.95, 1.55], gap="large")

with left:
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    st.subheader("Add Customer")
    with st.form("add_customer_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        last_name = c1.text_input("Last Name*", placeholder="Doe")
        first_name = c2.text_input("First Name*", placeholder="Jane")

        street = st.text_input("Property Address (Street)*", placeholder="123 Main St")
        c3, c4, c5 = st.columns([1, 0.5, 0.8])
        city = c3.text_input("City*", placeholder="Phoenix")
        state = c4.text_input("State (2-letter)*", max_chars=2, placeholder="AZ")
        zip_code = c5.text_input("Zip Code*", placeholder="85212")

        c6, c7 = st.columns(2)
        loan_amount = c6.number_input("Loan Amount*", min_value=0.0, step=1000.0, format="%.2f")
        estimated_value = c7.number_input("Estimated Property Value*", min_value=0.0, step=1000.0, format="%.2f")

        occupancy_type = st.selectbox(
            "Occupancy Type*",
            ["Primary Residence", "Second Home", "Investment"],
            index=0
        )

        submitted = st.form_submit_button("➕ Add to Pipeline")
        if submitted:
            record = {
                "last_name": last_name.strip(),
                "first_name": first_name.strip(),
                "street": street.strip(),
                "city": city.strip(),
                "state": state.strip().upper(),
                "zip_code": zip_code.strip(),
                "loan_amount": float(loan_amount),
                "estimated_value": float(estimated_value),
                "occupancy_type": occupancy_type,
            }
            # Required fields check
            if any(not record[k] for k in ["last_name","first_name","street","city","state","zip_code"]):
                st.error("Please complete all required fields marked with *.")
            else:
                msg = validate_inputs(record)
                if msg:
                    st.error(msg)
                else:
                    try:
                        insert_customer(record)
                        st.success(f"Added {record['first_name']} {record['last_name']} ✔️")
                    except Exception as e:
                        st.error(f"Failed to insert record: {e}")
    st.markdown('</div>', unsafe_allow_html=True)

with right:
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    st.subheader("Pipeline")
    with st.expander("Filter", expanded=False):
        fc1, fc2, fc3 = st.columns([1, 0.5, 0.4])
        f_name = fc1.text_input("Search Name (first/last)")
        f_city = fc2.text_input("City")
        f_state = fc3.text_input("State", max_chars=2)
        apply = st.button("Apply Filters")
    filters = {}
    if apply:
        if f_name: filters["name"] = f_name.strip()
        if f_city: filters["city"] = f_city.strip()
        if f_state: filters["state"] = f_state.strip()

    df = fetch_customers(filters)
    show_cols = ["id","last_name","first_name","street","city","state","zip_code","loan_amount","estimated_value","occupancy_type","created_at"]
    if not df.empty:
        df_display = df[show_cols].copy()
        df_display["loan_amount"] = df_display["loan_amount"].map(lambda x: f"${x:,.0f}")
        df_display["estimated_value"] = df_display["estimated_value"].map(lambda x: f"${x:,.0f}")
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No records found. Add a customer on the left to get started.")

    st.write("")
    st.markdown("---")

    # Row deletion
    st.subheader("Delete a Row")
    if not df.empty:
        did = st.selectbox("Select Row ID to Delete", options=df["id"].tolist())
        if st.button("🗑️ Delete Selected Row", type="secondary"):
            try:
                delete_customer(int())
                st.success(f"Deleted row #{did}")
            except Exception as e:
                st.error(f"Delete failed: {e}")
    else:
        st.caption("Add data before attempting to delete rows.")

    st.write("")
    # Export CSV
    if not df.empty:
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Export Current View (CSV)",
            data=csv,
            file_name="mortgage_pipeline_customers.csv",
            mime="text/csv",
        )
    st.markdown('</div>', unsafe_allow_html=True)


# ---------- Footer ----------
st.write("")
st.caption("© Mortgage Pipeline • Built with Python, SQLite, & Streamlit")
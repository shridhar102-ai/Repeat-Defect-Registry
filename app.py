import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st
from datetime import datetime
import subprocess
import sys

st.set_page_config(page_title="Repeat Mistake Radar", layout="wide")

st.markdown("""
<style>
.stApp {background: #0E1117; color: #E6EDF7; --text-color: #E6EDF7;}
.tile {background: #1A1F2B; border: 1px solid #2A3142; border-radius: 12px;
       padding: 16px 18px;}
.tl {color: #B9CBE2; font-size: 13px;}
.tv {color: #F4F7FF; font-size: 28px; font-weight: 600; margin-top: 4px;}
h1, h2, h3 {color: #F4F7FF;}
[data-testid="stCaptionContainer"] {color: #B9CBE2;}
[data-testid="stDataFrame"] {color: #E6EDF7;}
.dtab {width: 100%; border-collapse: collapse; background: #1A1F2B;
       color: #FFFFFF; border: 1px solid #2A3142;}
.dtab th {background: #222938; color: #8B93A7; font-weight: 500;
          text-align: left !important; padding: 10px 14px; font-size: 13px;}
.dtab td {padding: 10px 14px; border-top: 1px solid #2A3142;}
.sug {background: #1A1F2B; border: 1px solid #2A3142; border-radius: 12px;
      padding: 14px 18px; margin-bottom: 12px;}
.sug .t {color: #FFFFFF; font-weight: 600; font-size: 15px;}
.sug .v {font-size: 12px; margin-left: 8px; padding: 2px 8px;
         border-radius: 8px;}
.sug .b {color: #C5CBD9; font-size: 14px; margin-top: 6px;}
</style>
""", unsafe_allow_html=True)

con = sqlite3.connect("data/defects.db")
df = pd.read_sql("SELECT * FROM defects", con)
con.close()

team = df["person"].nunique()
g = df.groupby("cluster_name").agg(
    defects=("id", "count"),
    people=("person", "nunique"),
).reset_index().rename(columns={"cluster_name": "mistake"})
g["share"] = g["people"] / team * 100
g["verdict"] = g["share"].apply(lambda s: "Process fix" if s >= 33 else "Coaching")
g = g.sort_values("defects", ascending=False)

total = len(df)
process_pct = g[g["verdict"] == "Process fix"]["defects"].sum() / total * 100
top_person = df["person"].value_counts().index[0]
top_count = df["person"].value_counts().iloc[0]

st.title("Repeat Defect Registry")
st.caption("Service delivery, last 90 days (fictional data)")
with st.expander("Try your own data: upload a defect CSV"):
    up = st.file_uploader(
        "CSV with the columns: date, person, step, description, severity",
        type="csv")
    if up is not None:
        up_df = pd.read_csv(up)
        need = ["date", "person", "step", "description", "severity"]
        missing = [c for c in need if c not in up_df.columns]
        if missing:
            st.error(f"Your file is missing these columns: {missing}")
        else:
            st.success(
                f"Looks good: {len(up_df)} rows from "
                f"{up_df['person'].nunique()} people. "
                "Preview of the first 5 rows:")
            st.markdown(
                up_df.head(5).to_html(index=False, classes="dtab", border=0),
                unsafe_allow_html=True)
            if st.button("Analyze this file"):
                up_df.to_csv("uploaded_defects.csv", index=False)
                steps = [
                    ["import_csv.py", "uploaded_defects.csv"],
                    ["embed_data.py"],
                    ["cluster_save.py"],
                    ["llm_name.py"],
                    ["llm_suggest.py"],
                ]
                ok = True
                with st.spinner("Analyzing. This takes a few minutes."):
                    for s in steps:
                        res = subprocess.run(
                            [sys.executable] + s,
                            capture_output=True, text=True)
                        if res.returncode != 0:
                            st.error(f"{s[0]} failed: {res.stderr[-800:]}")
                            ok = False
                            break
                if ok:
                    st.rerun()

def tile(col, label, value):
    col.markdown(
        f"<div class='tile'><div class='tl'>{label}</div>"
        f"<div class='tv'>{value}</div></div>",
        unsafe_allow_html=True,
    )

c1, c2, c3, c4 = st.columns(4)
tile(c1, "Total defects", total)
tile(c2, "Distinct mistakes", len(g))
tile(c3, "Process-driven", f"{process_pct:.0f}%")
tile(c4, "Top contributor", f"{top_person} ({top_count})")

st.subheader("Top defect categories")
choice = st.radio("Show", ["All", "Process fix", "Coaching"], horizontal=True)
view = g if choice == "All" else g[g["verdict"] == choice]
fig = px.bar(
    view, x="defects", y="mistake", orientation="h", color="verdict",
    color_discrete_map={"Process fix": "#4F8BF9", "Coaching": "#F5B942"},
    text="defects",
)
fig.update_layout(
    template="plotly_dark", height=380,
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font={"color": "#E6EDF7"},
    yaxis={
        "categoryorder": "total ascending",
        "title": "",
        "tickfont": {"color": "#D5E1F0"},
    },
    xaxis={
        "title": {"text": "Defects", "font": {"color": "#B9CBE2"}},
        "tickfont": {"color": "#D5E1F0"},
    },
    legend={"font": {"color": "#FFFFFF"}},
    legend_title_text="",
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Training Need Intervention")
st.caption("For coaching conversations, not for ranking people.")
who = df.groupby("person").agg(
    defects=("id", "count"),
    different_mistakes=("cluster_name", "nunique"),
).sort_values("defects", ascending=False).head(5).reset_index()
who.columns = ["Person", "Defects", "Different mistakes"]
st.markdown(who.to_html(index=False, classes="dtab", border=0),
            unsafe_allow_html=True)
st.subheader("Intelligent Recommendations")
st.caption("AI generated suggestions. We recommend reviewing them before taking action.")

con = sqlite3.connect("data/defects.db")
sg = pd.read_sql("SELECT mistake, suggestion FROM suggestions", con)
con.close()

m = view[["mistake", "defects", "verdict"]].merge(sg, on="mistake")
m = m.sort_values("defects", ascending=False)

con = sqlite3.connect("data/defects.db")
con.execute("""CREATE TABLE IF NOT EXISTS decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mistake TEXT, decision TEXT, decided_at TEXT)""")
cols = [r[1] for r in con.execute("PRAGMA table_info(decisions)")]
if "reviewer" not in cols:
    con.execute("ALTER TABLE decisions ADD COLUMN reviewer TEXT")
con.commit()
con.close()

def record(mistake, decision):
    reviewer = st.session_state.get("reviewer", "").strip()
    if reviewer == "":
        st.session_state["need_reviewer"] = True
        return
    st.session_state["need_reviewer"] = False
    c = sqlite3.connect("data/defects.db")
    c.execute(
        "INSERT INTO decisions (mistake, decision, decided_at, reviewer) "
        "VALUES (?, ?, ?, ?)",
        (mistake, decision,
         datetime.now().strftime("%Y-%m-%d %H:%M:%S"), reviewer))
    c.commit()
    c.close()

con = sqlite3.connect("data/defects.db")
latest = dict(con.execute(
    "SELECT mistake, decision FROM decisions WHERE id IN "
    "(SELECT MAX(id) FROM decisions GROUP BY mistake)").fetchall())
con.close()

st.text_input("Reviewer name", key="reviewer", placeholder="Your name")
if st.session_state.get("need_reviewer"):
    st.warning("Enter your name before approving or rejecting.")
for i, (_, r) in enumerate(m.iterrows()):
    is_process = r["verdict"] == "Process fix"
    color = "#4F8BF9" if is_process else "#F5B942"
    st.markdown(
        f"<div class='sug' style='border-left: 4px solid {color}'>"
        f"<span class='t'>{r['mistake']}</span>"
        f"<span class='v' style='background: {color}33; color: {color}'>"
        f"{r['verdict']}</span>"
        f"<div class='b'>{r['suggestion']}</div></div>",
        unsafe_allow_html=True,
    )
    b1, b2, b3 = st.columns([1, 1, 6])
    b1.button("Approve", key=f"approve_{i}", on_click=record,
              args=(r["mistake"], "Approved"))
    b2.button("Reject", key=f"reject_{i}", on_click=record,
              args=(r["mistake"], "Rejected"))
    b3.caption(f"Status: {latest.get(r['mistake'], 'Pending review')}")

st.subheader("Decision log")
con = sqlite3.connect("data/defects.db")
log = pd.read_sql(
    "SELECT decided_at AS Time, mistake AS Mistake, decision AS Decision, "
    "COALESCE(reviewer, '(not recorded)') AS Reviewer "
    "FROM decisions ORDER BY id DESC LIMIT 10", con)
con.close()
if log.empty:
    st.caption("No decisions yet.")
else:
    st.markdown(log.to_html(index=False, classes="dtab", border=0),
                unsafe_allow_html=True)
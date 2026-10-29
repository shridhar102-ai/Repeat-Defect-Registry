import sys
import shutil
import sqlite3
import pandas as pd

path = sys.argv[1] if len(sys.argv) > 1 else "sample_defects.csv"
df = pd.read_csv(path)

required = ["date", "person", "step", "description", "severity"]
missing = [c for c in required if c not in df.columns]
if missing:
    print("Your file is missing these columns:", missing)
    sys.exit(1)

df = df[required].dropna(subset=["description", "person"])
df["description"] = df["description"].astype(str).str.strip()
df = df[df["description"] != ""]

shutil.copy("data/defects.db", "data/defects_backup.db")

con = sqlite3.connect("data/defects.db")
con.execute("DROP TABLE IF EXISTS defects")
con.execute("""CREATE TABLE defects (
    id INTEGER PRIMARY KEY, date TEXT, person TEXT, step TEXT,
    description TEXT, severity TEXT, expected_cluster TEXT,
    cluster_id INTEGER, cluster_name TEXT)""")
df.to_sql("defects", con, if_exists="append", index=False)
con.commit()

n = con.execute("SELECT COUNT(*) FROM defects").fetchone()[0]
p = con.execute("SELECT COUNT(DISTINCT person) FROM defects").fetchone()[0]
print(f"Imported {n} defects from {p} people.")
con.close()
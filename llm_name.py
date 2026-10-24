import re
import sqlite3
import json
import ollama

con = sqlite3.connect("data/defects.db")

groups = {}
for (cid,) in con.execute("SELECT DISTINCT cluster_id FROM defects ORDER BY cluster_id"):
    rows = con.execute(
        "SELECT DISTINCT description FROM defects WHERE cluster_id = ? LIMIT 6",
        (cid,),
    ).fetchall()
    groups[str(cid)] = [r[0] for r in rows]

prompt = (
    "You are a seasoned quality analyst reviewing defects from a service desk. "
    "Below are groups of defect descriptions. For each group, give a short "
    "name (2 to 4 words, sentence case) for the underlying mistake. "
    "If two groups describe the same underlying mistake, give them exactly "
    "the same name. Reply only with JSON like {\"0\": \"name\", \"1\": \"name\"}.\n\n"
    + json.dumps(groups, indent=2)
    + "\n/no_think"
)

print("Asking the model... the first run can take a minute.")
resp = ollama.chat(
    model="qwen3:4b",
    messages=[{"role": "user", "content": prompt}],
    format="json",
    options={"temperature": 0},
)
names = json.loads(resp["message"]["content"])

cols = [r[1] for r in con.execute("PRAGMA table_info(defects)")]
if "cluster_name" not in cols:
    con.execute("ALTER TABLE defects ADD COLUMN cluster_name TEXT")
for key, name in names.items():
    digits = re.sub(r"\D", "", str(key))
    if digits == "":
        continue
    con.execute("UPDATE defects SET cluster_name = ? WHERE cluster_id = ?",
                (str(name), int(digits)))
con.commit()

print()
print("cluster  defects  name")
for cid, n, name in con.execute(
    "SELECT cluster_id, COUNT(*), cluster_name FROM defects "
    "GROUP BY cluster_id ORDER BY COUNT(*) DESC"
):
    print(f"{cid:<8} {n:<8} {name}")
print()
print("Distinct names:", len(set(names.values())))
con.close()
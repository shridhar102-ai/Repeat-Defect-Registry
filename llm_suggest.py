import re
import json
import sqlite3
import ollama

con = sqlite3.connect("data/defects.db")
team = con.execute("SELECT COUNT(DISTINCT person) FROM defects").fetchone()[0]

rows = con.execute(
    "SELECT cluster_name, COUNT(*), COUNT(DISTINCT person) FROM defects "
    "GROUP BY cluster_name ORDER BY COUNT(*) DESC"
).fetchall()

items = []
for i, (name, n, p) in enumerate(rows, start=1):
    verdict = "Process fix" if p / team * 100 >= 33 else "Coaching"
    examples = [r[0] for r in con.execute(
        "SELECT DISTINCT description FROM defects WHERE cluster_name = ? LIMIT 4",
        (name,))]
    items.append({"id": str(i), "mistake": name, "verdict": verdict,
                  "defects": n, "people_involved": p, "examples": examples})

prompt = (
    "You are a quality manager at a service desk. For each numbered mistake "
    "below, write one short suggestion of at most 35 words. If the verdict is "
    "Process fix, the mistake is spread across many people, so name a likely "
    "cause in the process, tool or instructions, and one fix. If the verdict "
    "is Coaching, it is concentrated in a few people, so suggest one coaching "
    "action. Reply only with JSON like {\"1\": \"text\", \"2\": \"text\"}.\n\n"
    + json.dumps(items, indent=2)
    + "\n/no_think"
)

print("Asking the model... Grab a coffee, this can take a minute.")
resp = ollama.chat(
    model="qwen3:4b",
    messages=[{"role": "user", "content": prompt}],
    format="json",
    options={"temperature": 0},
)
answer = json.loads(resp["message"]["content"])

con.execute("DROP TABLE IF EXISTS suggestions")
con.execute("CREATE TABLE suggestions "
            "(mistake TEXT PRIMARY KEY, verdict TEXT, suggestion TEXT)")

by_id = {}
for key, text in answer.items():
    digits = re.sub(r"\D", "", str(key))
    if digits:
        by_id[digits] = str(text)

print()
for it in items:
    text = by_id.get(it["id"], "No suggestion returned.")
    con.execute("INSERT INTO suggestions VALUES (?, ?, ?)",
                (it["mistake"], it["verdict"], text))
    print(f"{it['mistake']}  [{it['verdict']}]")
    print(f"   {text}")
    print()

con.commit()
con.close()
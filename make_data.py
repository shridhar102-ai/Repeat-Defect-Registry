import sqlite3, random, os
from datetime import date, timedelta

random.seed(42)

analysts = [f"Analyst {n:02d}" for n in range(1, 13)]

clusters = {
    "Wrong ticket category": {
        "count": 24, "step": "Logging",
        "people": [analysts[i] for i in (0, 1, 2, 3, 4, 5, 6, 9, 10, 11)],
        "weights": None,
        "texts": [
            "Incorrect category selected",
            "Mis-tagged as network issue, was access",
            "Billing queue used instead of access",
            "Ticket logged under wrong category",
            "Wrong queue chosen at logging",
            "Categorised as hardware, should be software",
        ],
    },
    "Missing verification": {
        "count": 18, "step": "Verification",
        "people": ["Analyst 04", "Analyst 09", "Analyst 02"],
        "weights": [8, 8, 2],
        "texts": [
            "Didn't confirm caller identity",
            "ID check skipped before password reset",
            "Customer not verified before account change",
            "Skipped security questions",
            "Verification step missed on callback",
            "Reset done without confirming identity",
        ],
    },
    "SLA timestamp not updated": {
        "count": 14, "step": "Closure",
        "people": [analysts[i] for i in (0, 1, 2, 4, 5, 6, 7, 9, 10)],
        "weights": None,
        "texts": [
            "SLA clock not updated",
            "Timestamp missing after callback",
            "Response time not recorded",
            "SLA timer left running after resolution",
            "Forgot to log first response time",
        ],
    },
    "Incomplete resolution notes": {
        "count": 9, "step": "Closure",
        "people": ["Analyst 04", "Analyst 12"],
        "weights": [7, 2],
        "texts": [
            "Resolution notes left blank",
            "Closure comment too brief to understand",
            "No fix steps recorded",
            "Notes just say done, no detail",
            "Incomplete resolution summary",
        ],
    },
    "Wrong escalation path": {
        "count": 6, "step": "Escalation",
        "people": [analysts[i] for i in (1, 3, 5, 7, 8)],
        "weights": None,
        "texts": [
            "Escalated to wrong team",
            "Sent to L3 instead of security",
            "Wrong escalation path used",
            "Escalation skipped for high severity",
            "Handed off to billing, should be access",
        ],
    },
}

os.makedirs("data", exist_ok=True)
con = sqlite3.connect("data/defects.db")
cur = con.cursor()
cur.execute("DROP TABLE IF EXISTS defects")
cur.execute("""
CREATE TABLE defects (
    id INTEGER PRIMARY KEY,
    date TEXT,
    person TEXT,
    step TEXT,
    description TEXT,
    severity TEXT,
    expected_cluster TEXT
)
""")

today = date.today()
rows = []
for name, c in clusters.items():
    for _ in range(c["count"]):
        person = random.choices(c["people"], weights=c["weights"])[0]
        d = today - timedelta(days=random.randint(0, 89))
        sev = random.choice(["Low", "Medium", "High"])
        rows.append((d.isoformat(), person, c["step"],
                     random.choice(c["texts"]), sev, name))

random.shuffle(rows)
cur.executemany(
    "INSERT INTO defects (date, person, step, description, severity, expected_cluster) "
    "VALUES (?, ?, ?, ?, ?, ?)", rows)
con.commit()

print("Total defects:", cur.execute("SELECT COUNT(*) FROM defects").fetchone()[0])
print()
for name, n in cur.execute(
        "SELECT expected_cluster, COUNT(*) FROM defects "
        "GROUP BY expected_cluster ORDER BY COUNT(*) DESC"):
    print(f"{n:3d}  {name}")
print()
for r in cur.execute("SELECT person, step, description FROM defects LIMIT 3"):
    print(r)
con.close()
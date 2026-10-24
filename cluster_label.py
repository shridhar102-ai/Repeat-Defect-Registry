import sqlite3

con = sqlite3.connect("data/defects.db")
team = con.execute("SELECT COUNT(DISTINCT person) FROM defects").fetchone()[0]
print("Team size in data:", team)
print()

print("defects  people  share  verdict       example")
rows = con.execute("""
    SELECT cluster_id, COUNT(*), COUNT(DISTINCT person), MIN(description)
    FROM defects GROUP BY cluster_id ORDER BY COUNT(*) DESC
""").fetchall()
for cid, n, p, ex in rows:
    share = 100 * p / team
    verdict = "Process fix" if share >= 33 else "Coaching"
    print(f"{n:<8} {p:<7} {share:>4.0f}%   {verdict:<13} {ex}")

print()
print("Coaching view: one person, several mistakes")
print("person       defects  different mistakes")
for person, n, k in con.execute("""
    SELECT person, COUNT(*), COUNT(DISTINCT cluster_id)
    FROM defects GROUP BY person ORDER BY COUNT(*) DESC LIMIT 4
"""):
    print(f"{person:<12} {n:<8} {k}")
con.close()
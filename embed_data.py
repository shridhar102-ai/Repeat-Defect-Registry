import sqlite3
import chromadb

con = sqlite3.connect("data/defects.db")
rows = con.execute("SELECT id, description, person FROM defects").fetchall()
con.close()

client = chromadb.PersistentClient(path="data/chroma")
try:
    client.delete_collection("defects")
except Exception:
    pass
col = client.create_collection("defects")

col.add(
    ids=[str(r[0]) for r in rows],
    documents=[r[1] for r in rows],
    metadatas=[{"person": r[2]} for r in rows],
)
print("Stored in vector DB:", col.count())

queries = [
    "put the ticket in the wrong queue",
    "forgot to confirm who the customer was",
]
for q in queries:
    print()
    print("SEARCH:", q)
    res = col.query(query_texts=[q], n_results=5)
    for doc, dist in zip(res["documents"][0], res["distances"][0]):
        print(f"  {dist:.2f}  {doc}")
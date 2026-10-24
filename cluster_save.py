import sqlite3
import numpy as np
import chromadb
from sklearn.cluster import AgglomerativeClustering

client = chromadb.PersistentClient(path="data/chroma")
col = client.get_collection("defects")
data = col.get(include=["embeddings"])
ids = data["ids"]
X = np.array(data["embeddings"])

labels = AgglomerativeClustering(
    n_clusters=None, distance_threshold=0.8,
    metric="cosine", linkage="average"
).fit_predict(X)

con = sqlite3.connect("data/defects.db")
cols = [r[1] for r in con.execute("PRAGMA table_info(defects)")]
if "cluster_id" not in cols:
    con.execute("ALTER TABLE defects ADD COLUMN cluster_id INTEGER")

con.executemany(
    "UPDATE defects SET cluster_id = ? WHERE id = ?",
    [(int(l), int(i)) for i, l in zip(ids, labels)],
)
con.commit()

print("cluster  defects  people  example")
for row in con.execute("""
    SELECT cluster_id, COUNT(*), COUNT(DISTINCT person), MIN(description)
    FROM defects GROUP BY cluster_id ORDER BY COUNT(*) DESC
"""):
    print(f"{row[0]:<8} {row[1]:<8} {row[2]:<7} {row[3]}")
con.close()
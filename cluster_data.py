import sqlite3
import numpy as np
import chromadb
from collections import Counter
from sklearn.cluster import AgglomerativeClustering

client = chromadb.PersistentClient(path="data/chroma")
col = client.get_collection("defects")
data = col.get(include=["embeddings", "documents"])

ids = data["ids"]
docs = data["documents"]
X = np.array(data["embeddings"])

con = sqlite3.connect("data/defects.db")
expected = {str(i): c for i, c in
            con.execute("SELECT id, expected_cluster FROM defects")}
con.close()

labels = AgglomerativeClustering(
    n_clusters=5, metric="cosine", linkage="average"
).fit_predict(X)

for k in range(5):
    members = [i for i, l in zip(ids, labels) if l == k]
    counts = Counter(expected[i] for i in members)
    print(f"GROUP {k + 1}: {len(members)} records")
    for label, n in counts.most_common():
        print(f"   {n:3d}  {label}")
    example = docs[ids.index(members[0])]
    print(f"   example: {example}")
    print()
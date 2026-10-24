import sqlite3
import numpy as np
import chromadb
from collections import Counter
from sklearn.cluster import AgglomerativeClustering

client = chromadb.PersistentClient(path="data/chroma")
col = client.get_collection("defects")
data = col.get(include=["embeddings"])

ids = data["ids"]
X = np.array(data["embeddings"])

con = sqlite3.connect("data/defects.db")
expected = {str(i): c for i, c in
            con.execute("SELECT id, expected_cluster FROM defects")}
con.close()

print("threshold  groups  mixed groups  purity")
for t in [0.8, 0.85, 0.9, 0.95, 1.0]:
    labels = AgglomerativeClustering(
        n_clusters=None, distance_threshold=t,
        metric="cosine", linkage="average"
    ).fit_predict(X)

    n_groups = len(set(labels))
    mixed = 0
    correct = 0
    for k in set(labels):
        members = [i for i, l in zip(ids, labels) if l == k]
        counts = Counter(expected[i] for i in members)
        if len(counts) > 1:
            mixed += 1
        correct += counts.most_common(1)[0][1]

    purity = 100 * correct / len(ids)
    print(f"{t:<10} {n_groups:<7} {mixed:<13} {purity:.0f}%")
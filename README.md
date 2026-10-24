# Repeat Defect Registry

Finds the defects a team keeps repeating, and tells you whether to fix the process or coach the people.

![Dashboard](docs/dashboard.png)

## The problem

In quality management, the same mistakes come back again and again. Two situations get mixed up:

- **One person making several different mistakes.** This points to coaching or workload.
- **Many people making the same mistake.** This points to a broken process, tool or instruction. Retraining people will not fix it.

Defect logs make this hard to see, because people describe one mistake in many different words. "Incorrect category selected", "Mis-tagged as network issue" and "Billing queue used instead of access" are the same mistake, and a normal Pareto chart counts them as three.

## What it does

1. Stores defect records in SQLite.
2. Embeds each description into ChromaDB and groups records by meaning, not wording.
3. Counts how many different people are behind each group. A mistake spread across a third or more of the team is labelled **Process fix**, otherwise **Coaching**.
4. Uses a local LLM (Qwen3 4B through Ollama) to name each group and draft one suggested action.
5. Lets a person **approve or reject** every suggestion. Each decision is saved with a timestamp in a decision log.

## Stack

Python, Streamlit, SQLite, ChromaDB, scikit-learn, Plotly, Ollama (qwen3:4b). Runs fully on a laptop, with no paid API.

## Run it

```
pip install -r requirements.txt
ollama pull qwen3:4b

python make_data.py       # creates 71 fictional defect records
python embed_data.py      # stores them in the vector database
python cluster_save.py    # groups them by meaning
python llm_name.py        # LLM names the groups
python llm_suggest.py     # LLM drafts a suggestion for each
streamlit run app.py
```

The other scripts (`cluster_data.py`, `cluster_v2.py`, `cluster_label.py`) are the experiments used to choose the grouping setting.

## Known limits

- The data is fictional and uses only about 28 distinct phrasings, so real logs will be messier.
- The grouping threshold was tuned on 71 records. A real deployment needs re-tuning.
- A small local model writes generic suggestions, so they are drafts for a person to review.
- The reviewer is a typed name, not a login, so anyone can enter any name and the same person can appear under different spellings. A real version needs sign-in and a fixed list of reviewers.
- Per-person counts are for coaching conversations, not for ranking people.
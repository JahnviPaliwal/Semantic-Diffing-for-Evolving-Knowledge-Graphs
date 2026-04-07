# Semantic Diffing for Evolving Knowledge Graphs

Track how entities and relationships in a knowledge graph evolve as new documents arrive.

## Setup

```bash
cd semantic_diffing
pip install -r requirements.txt
export GROQ_API_KEY=your_key_here
streamlit run app.py
```

## How It Works

1. Upload a **baseline document** (v1) and a **new document** (v2)
2. The LLM extracts entities and relationships from each
3. A NetworkX graph is built for each snapshot
4. The diff is computed: added/removed entities and relations are highlighted
5. A natural-language summary of changes is generated

## Sample Data

`data/doc_v1.txt` and `data/doc_v2.txt` are pre-loaded sample texts about a fictional company. Use the **"Load sample documents"** button in the sidebar.

## File Structure

| File | Purpose |
|---|---|
| `app.py` | Streamlit UI |
| `semantic_diff.py` | LLM-based entity/relation extraction + diff logic |
| `graph_utils.py` | NetworkX graph builder + Matplotlib visualiser |
| `data/` | Sample text documents |
| `requirements.txt` | Python dependencies |

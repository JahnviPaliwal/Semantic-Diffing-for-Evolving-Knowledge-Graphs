
# Semantic Diffing for Evolving Knowledge Graphs

A system for tracking structural changes in knowledge graphs as documents evolve over time. This project extracts entities and relationships from multiple document versions, constructs graph representations, and identifies semantic differences such as added or removed entities and relationships.

The system enables comparison between document snapshots and generates both structured graph diffs and natural-language summaries of detected changes.

---

# Overview

Knowledge graphs evolve as new information becomes available. Tracking changes between versions is critical in domains such as enterprise knowledge management, legal systems, compliance workflows, and technical documentation.

This project implements:

* Entity and relationship extraction from document versions
* Knowledge graph construction using NetworkX
* Graph-level semantic diffing
* Identification of added and removed nodes and edges
* Natural-language summarization of detected changes

---

# Key Features

* Extract entities and relationships from document text
* Build graph representations for multiple document versions
* Compare knowledge graph snapshots
* Detect added entities
* Detect removed entities
* Detect added relationships
* Detect removed relationships
* Generate structured graph diffs
* Produce natural-language summaries of changes
* Visualize knowledge graph snapshots

---

# How It Works

1. Upload two document versions:

   * Baseline document (v1)
   * Updated document (v2)

2. Each document is processed independently:

   * Text is parsed
   * Entities are extracted
   * Relationships are extracted

3. A knowledge graph is created for each version.

4. Graph diffing identifies:

   * New entities
   * Removed entities
   * New relationships
   * Removed relationships

5. A natural-language summary describes the detected changes.

---

# System Architecture

```text
                 ┌─────────────────────┐
                 │   Document v1       │
                 │   (Baseline)        │
                 └─────────┬───────────┘
                           │
                           ▼
                 ┌─────────────────────┐
                 │ Entity & Relation   │
                 │ Extraction (LLM)    │
                 └─────────┬───────────┘
                           │
                           ▼
                 ┌─────────────────────┐
                 │ Knowledge Graph v1  │
                 └─────────────────────┘


                 ┌─────────────────────┐
                 │   Document v2       │
                 │   (Updated)         │
                 └─────────┬───────────┘
                           │
                           ▼
                 ┌─────────────────────┐
                 │ Entity & Relation   │
                 │ Extraction (LLM)    │
                 └─────────┬───────────┘
                           │
                           ▼
                 ┌─────────────────────┐
                 │ Knowledge Graph v2  │
                 └─────────┬───────────┘
                           │
                           ▼
                 ┌─────────────────────┐
                 │ Graph Diff Engine   │
                 │ - Added Nodes       │
                 │ - Removed Nodes     │
                 │ - Added Edges       │
                 │ - Removed Edges     │
                 └─────────┬───────────┘
                           │
                           ▼
                 ┌─────────────────────┐
                 │ Change Summary      │
                 │ Natural Language    │
                 └─────────────────────┘
```

---

# Installation

Clone the repository:

```bash
git clone https://github.com/your-username/semantic_diffing.git
cd semantic_diffing
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Set the Groq API key:

Linux / macOS:

```bash
export GROQ_API_KEY=your_key_here
```

Windows:

```powershell
set GROQ_API_KEY=your_key_here
```

Run the application:

```bash
streamlit run app.py
```

---

# Input Format

Supported formats:

* `.txt` documents

Two versions are required:

* Baseline document (v1)
* Updated document (v2)

---

# Sample Data

Sample documents are included in the `data/` directory:

* `doc_v1.txt`
  Baseline version of a fictional company description.

* `doc_v2.txt`
  Updated version containing new entities and relationships.

These files allow quick testing of semantic diffing functionality.

---

# Project Structure

```text
semantic_diffing/
│
├── app.py
│   Entry point for execution
│
├── semantic_diff.py
│   Entity and relationship extraction
│   Graph diff computation
│
├── graph_utils.py
│   NetworkX graph construction
│   Graph visualization
│
├── data/
│   ├── doc_v1.txt
│   └── doc_v2.txt
│
├── requirements.txt
│   Python dependencies
│
└── README.md
```

---

# Core Modules

## semantic_diff.py

Responsible for:

* LLM-based entity extraction
* Relationship extraction
* Graph comparison logic
* Detection of semantic differences
* Generation of change summaries

Key operations:

* Extract entities
* Extract relationships
* Compute node differences
* Compute edge differences
* Generate structured diff output

---

## graph_utils.py

Responsible for:

* Building knowledge graphs using NetworkX
* Representing entities as nodes
* Representing relationships as edges
* Visualizing graph snapshots
* Highlighting added and removed elements

---

## app.py

Acts as the main execution script.

Responsible for:

* Loading document versions
* Triggering extraction pipeline
* Building graphs
* Running diff computation
* Displaying outputs

---

# Example Output (Graph Diff JSON)

```json
{
  "added_entities": [
    "AI Research Division",
    "Cloud Infrastructure Team"
  ],
  "removed_entities": [
    "Legacy Systems Department"
  ],
  "added_relationships": [
    {
      "source": "ABC Corporation",
      "relation": "launched",
      "target": "AI Research Division"
    }
  ],
  "removed_relationships": [
    {
      "source": "ABC Corporation",
      "relation": "maintains",
      "target": "Legacy Systems Department"
    }
  ]
}
```

---

# Example LLM Extraction Prompt

```text
You are an information extraction system.

Extract structured entities and relationships from the text.

Return output in JSON format using:

{
  "entities": [],
  "relationships": []
}

Rules:

1. Entities should represent meaningful objects such as:
   - Organizations
   - Departments
   - Products
   - Teams
   - Locations

2. Relationships should represent interactions between entities.

Text:

{DOCUMENT_TEXT}
```

---

# Example Diff Summary

```text
Changes detected between document versions:

- Two new entities were introduced: AI Research Division and Cloud Infrastructure Team.
- One entity was removed: Legacy Systems Department.
- A new relationship was added linking ABC Corporation to AI Research Division.
- A maintenance relationship with Legacy Systems Department was removed.
```

---

# Technologies Used

* Python
* NetworkX
* Matplotlib
* Large Language Models (LLMs)
* Groq API
* Natural Language Processing (NLP)
* Graph Theory

---

# Design Considerations

* Separate graphs are built per document version.
* Diffing operates at both node and edge levels.
* Structured outputs enable downstream analytics.
* Modular design allows extension to multi-version comparison.

---

# Limitations

* Extraction accuracy depends on LLM output quality.
* Large graphs may increase visualization complexity.
* Relationship normalization may require domain tuning.
* Currently supports two-version comparison only.

---

# Future Improvements

* Multi-version timeline diffing
* Graph history tracking
* Knowledge graph persistence
* Interactive graph exploration
* Graph database integration (Neo4j)
* Graph embedding similarity metrics
* Change severity scoring
* Support for additional document formats

---

# Use Cases

This system can be applied to:

* Enterprise knowledge tracking
* Policy change monitoring
* Technical documentation updates
* Compliance auditing
* Legal contract version comparison
* Organizational change tracking
* Knowledge management systems

ualization


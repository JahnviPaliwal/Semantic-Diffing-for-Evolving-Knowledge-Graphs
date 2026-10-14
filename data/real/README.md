# Real Versioned Documents Directory

This directory is designated for real-world document families, such as:
- Evolving legal agreements (Terms of Service, Master Services Agreements, End User License Agreements)
- Privacy Policies (GDPR / CCPA / HIPAA compliance updates)
- Regulatory filings and technical standards

## How to Add Your Own Real Documents

1. Place your sequential document versions in this folder (e.g. `policy_v1.txt`, `policy_v2.txt`, or `.pdf`/`.docx` equivalents).
2. Through the Web UI:
   - Navigate to `/projects`, create a new project (e.g. "Acme Terms of Service").
   - Upload each file sequentially to build the version history and inspect the temporal timeline.
3. Through Python / CLI:
   - Use the extraction manager:
     ```python
     from src.semantic_diff.extraction import ExtractionManager
     manager = ExtractionManager()
     text = manager.extract_text_from_file("data/real/policy_v1.txt")
     extraction = manager.extract_from_text(text, version_id="v1")
     ```

CLAUSE_EXTRACTION_SYSTEM = """You are a legal contract analyst. Your task is to parse a contract \
into its individual clauses and extract structured metadata.

You must return valid JSON and nothing else — no markdown, no explanation outside the JSON."""

CLAUSE_EXTRACTION_USER = """Analyze the following contract text and extract all clauses into a \
structured format.

For each clause, identify:
- **id**: A unique sequential identifier (e.g., "clause_1", "clause_2")
- **title**: The clause heading or a descriptive title if no heading exists
- **section_number**: The section/article number as written in the contract (e.g., "1", "2.1", \
"Article III")
- **content**: The full text of the clause
- **clause_type**: Categorize as one of: liability, indemnification, termination, notice, \
confidentiality, ip, force_majeure, sla, payment, warranty, data_protection, insurance, \
dispute_resolution, governing_law, assignment, amendment, general

Also extract:
- **contract_title**: The title of the contract
- **parties**: List of party names
- **effective_date**: The effective date if stated (null if not found)

Return a JSON object with this exact structure:
{{
  "contract_title": "...",
  "parties": ["Party A", "Party B"],
  "effective_date": "...",
  "clauses": [
    {{
      "id": "clause_1",
      "title": "...",
      "section_number": "...",
      "content": "...",
      "clause_type": "..."
    }}
  ]
}}

CONTRACT TEXT:
{contract_text}"""

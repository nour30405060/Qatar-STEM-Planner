# Q-STEM Planner AI – Prototype

A Streamlit prototype for a standards-based, curriculum-grounded AI co-planning and evaluation tool for STEM lesson planning among science teachers in Qatar.

## Main Features

- Upload textbook lesson pages as PDF.
- Read a local knowledge base of official standards/documents.
- Generate a STEM lesson plan grounded in uploaded lesson content.
- Allow teacher creative adaptation.
- Evaluate lesson plan quality using a STEM planning rubric.
- Export the generated plan and evaluation as a Word file.

## Setup

1. Install Python 3.10 or later.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Add your OpenAI API key.

Option A: Environment variable:
```bash
set OPENAI_API_KEY=your_key_here       # Windows Command Prompt
$env:OPENAI_API_KEY="your_key_here"    # PowerShell
export OPENAI_API_KEY=your_key_here    # Mac/Linux
```

Option B: Streamlit secrets file:
Create `.streamlit/secrets.toml`:
```toml
OPENAI_API_KEY="your_key_here"
```

4. Run the app:

```bash
streamlit run app.py
```

## Notes

This is a research prototype, not a commercial platform. The API key must remain private and must not be shared with teachers.

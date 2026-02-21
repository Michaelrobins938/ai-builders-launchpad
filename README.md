# Book 1 – The AI Builder's Launchpad

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Michaelrobins938/ai-builders-launchpad/blob/main/notebooks/book-01-bi-engine.ipynb)

From first prompt to first billable pipeline. This repo contains the reference implementation for **Book 1: The AI Builder's Launchpad** in the AI/LLM Mastery Program.

## What this repo includes

- A **Feedback Intelligence / BI Engine** pipeline that:  
  - Reads a CSV of customer emails  
  - Classifies and extracts structured signals with Claude  
  - Aggregates stats in Python  
  - Generates a Markdown executive report  
- A **Colab notebook** that runs the full pipeline in your browser  
- Sample data and a minimal environment setup for local runs

## Quickstart (10 seconds – Colab)

1. Open the notebook:

   - `notebooks/book-01-bi-engine.ipynb` (open in Colab)

2. In the first cell, set your API key:

   ```python
   import os
   os.environ["ANTHROPIC_API_KEY"] = "sk-ant-YOUR-KEY-HERE"
   ```

3. Run all cells to execute: **CSV → LLM → Markdown report**. 

## Local setup (VS Code / Cursor)

```bash
git clone https://github.com/Michaelrobins938/ai-builders-launchpad.git
cd ai-builders-launchpad

python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

Create `.env`:

```bash
echo "ANTHROPIC_API_KEY=sk-ant-your-key-here" > .env
```

Run the pipeline:

```bash
python pipeline.py --input data/sample_emails.csv --output reports/feedback_report.md
```

## Files

- `pipeline.py` – Full 5-node Feedback Intelligence pipeline (Triage → Extract → Aggregate → Synthesize → Format). 
- `models.py` (optional) – Pydantic models and system prompts (`TriageResult`, `FailureSignal`, etc.).  
- `data/sample_emails.csv` – Example input data with an `email` column. 
- `reports/` – Generated Markdown reports (ignored by git if you prefer).  
- `notebooks/book-01-bi-engine.ipynb` – Colab-ready version of the pipeline.  
- `requirements.txt` – Python dependencies.  
- `.env.example` – Environment variable template.

## How this maps to the book

- **Chapter 3–4** – Prompt design and pseudocode → see how system/user prompts become `TRIAGE_SYSTEM`, `EXTRACT_SYSTEM`, `SYNTHESIS_SYSTEM` in `pipeline.py`. 
- **Chapter 5** – Structured prompting and Pydantic → `TriageResult` and `FailureSignal` models validate LLM JSON before it reaches your database. 
- **Chapter 6** – Hallucination insurance → aggregation and synthesis use verified data only.  
- **Chapter 7–8** – Data hygiene and batch processing → CSV cleaning and iteration over rows in `run_pipeline(...)`. 
- **Chapter 9** – Shipping Day → This repo is the 4‑component handoff package: code, sample data, README, and run instructions. 

## For hiring managers

This project demonstrates:

- Practical **LLM orchestration** (multi-node pipeline, not just single prompts)  
- **Schema enforcement** and error handling via Pydantic  
- **Data engineering basics** (CSV cleaning, aggregation)  
- Clear **handoff documentation** suitable for production onboarding 

You can run the full pipeline in under 5 minutes and inspect the code to see how I design, document, and ship AI-powered analytics systems.

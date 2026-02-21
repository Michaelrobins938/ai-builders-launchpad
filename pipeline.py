#!/usr/bin/env python3
"""
Book 1: AI Builder's Launchpad - Feedback Intelligence Pipeline

A 5-node BI engine that processes customer emails and generates insights.

Usage:
    python pipeline.py --input data/sample_emails.csv --output reports/feedback_report.md
"""

import argparse
import json
import os
import re
from collections import Counter
from datetime import datetime
from typing import Optional

import anthropic
import pandas as pd
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError

load_dotenv()

TRIAGE_MODEL = "claude-3-5-haiku-latest"
SYNTHESIS_MODEL = "claude-3-5-haiku-latest"
COST_PER_1K = 0.00025

TRIAGE_SYSTEM = """You are a customer feedback analyst.
Classify the email into ONE category: [Billing, Technical, Feature Request, Refund, General].
Assign urgency: [High, Medium, Low].

Rules:
- HIGH urgency: customer mentions outage, data loss, legal threat, or time-critical issue
- Respond ONLY in this JSON format. No other text.

{
  "category": "<category>",
  "urgency": "<High | Medium | Low>",
  "one_line_summary": "<max 15 words>"
}"""

EXTRACT_SYSTEM = """You are a root-cause analyst.
Extract the specific product failure from this feedback.
Respond ONLY in JSON.

{
  "failure_type": "<specific system or feature that failed>",
  "customer_impact": "<what the customer could not do>",
  "frequency_signal": "<'first time' | 'recurring' | 'unspecified'>",
  "emotional_tone": "<frustrated | angry | neutral | satisfied>"
}"""

SYNTHESIS_SYSTEM = """You are a COO preparing a weekly feedback briefing.
Base ALL conclusions on the provided statistics.
Do not invent trends.
Use plain language.
Highlight top 3 actionable insights.
Keep the executive summary to 3 paragraphs max."""


class TriageResult(BaseModel):
    category: str = Field(..., description="Classification category")
    urgency: str = Field(..., description="Priority level: High, Medium, or Low")
    one_line_summary: str = Field(..., description="Brief summary of the issue")
    email_id: Optional[int] = None


class FailureSignal(BaseModel):
    failure_type: str = Field(..., description="Specific system or feature that failed")
    customer_impact: str = Field(..., description="What the customer could not do")
    frequency_signal: str = Field(
        ..., description="first time, recurring, or unspecified"
    )
    emotional_tone: str = Field(
        ..., description="frustrated, angry, neutral, or satisfied"
    )
    email_id: Optional[int] = None


def extract_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group())
    raise ValueError("No JSON found in response")


def triage_email(
    client: anthropic.Anthropic, email_text: str, email_id: int
) -> Optional[TriageResult]:
    try:
        response = client.messages.create(
            model=TRIAGE_MODEL,
            max_tokens=128,
            temperature=0,
            system=TRIAGE_SYSTEM,
            messages=[{"role": "user", "content": f"Classify: {email_text}"}],
        )
        data = extract_json(response.content[0].text)
        data["email_id"] = email_id
        return TriageResult(**data)
    except Exception as e:
        print(f"  Warning: Triage failed for email {email_id}: {e}")
        return None


def extract_failure(
    client: anthropic.Anthropic, email_text: str, email_id: int
) -> Optional[FailureSignal]:
    try:
        response = client.messages.create(
            model=TRIAGE_MODEL,
            max_tokens=128,
            temperature=0,
            system=EXTRACT_SYSTEM,
            messages=[{"role": "user", "content": email_text}],
        )
        data = extract_json(response.content[0].text)
        data["email_id"] = email_id
        return FailureSignal(**data)
    except Exception as e:
        print(f"  Warning: Extraction failed for email {email_id}: {e}")
        return None


def aggregate_results(triage_results: list[TriageResult]) -> dict:
    valid = [r for r in triage_results if r is not None]
    category_counts = Counter(r.category for r in valid)
    urgency_counts = Counter(r.urgency for r in valid)
    return {
        "total_emails": len(triage_results),
        "successful": len(valid),
        "failed": len(triage_results) - len(valid),
        "by_category": dict(category_counts),
        "by_urgency": dict(urgency_counts),
    }


def synthesize(
    client: anthropic.Anthropic, aggregated: dict, failure_signals: list[FailureSignal]
) -> str:
    stats_summary = f"""
Total emails analyzed: {aggregated["total_emails"]}
Success rate: {aggregated["successful"] / aggregated["total_emails"]:.1%}

Category breakdown:
{json.dumps(aggregated["by_category"], indent=2)}

Urgency breakdown:
{json.dumps(aggregated["by_urgency"], indent=2)}

Top failure signals from high-priority emails:
{json.dumps([fs.model_dump() for fs in failure_signals[:5]], indent=2)}
"""
    response = client.messages.create(
        model=SYNTHESIS_MODEL,
        max_tokens=1024,
        temperature=0,
        system=SYNTHESIS_SYSTEM,
        messages=[{"role": "user", "content": stats_summary}],
    )
    return response.content[0].text


def generate_report(
    aggregated: dict,
    synthesis: str,
    failure_signals: list[FailureSignal],
    total_records: int,
) -> str:
    report = f"""# Customer Feedback Intelligence Report

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M")}
**Total Emails Processed:** {aggregated["total_emails"]}
**Success Rate:** {aggregated["successful"] / aggregated["total_emails"]:.1%}

---

## Executive Summary

{synthesis}

---

## Category Breakdown

| Category | Count | Percentage |
|----------|-------|------------|
"""
    for cat, count in aggregated["by_category"].items():
        pct = count / aggregated["successful"] * 100
        report += f"| {cat} | {count} | {pct:.1f}% |\n"

    report += """
---

## Urgency Distribution

| Urgency | Count |
|---------|-------|
"""
    for urg, count in aggregated["by_urgency"].items():
        report += f"| {urg} | {count} |\n"

    report += """
---

## High-Priority Failure Signals

| Failure Type | Customer Impact | Frequency |
|--------------|-----------------|-----------|
"""
    for fs in failure_signals:
        report += (
            f"| {fs.failure_type} | {fs.customer_impact} | {fs.frequency_signal} |\n"
        )

    report += f"""
---

## Pipeline Metadata

- **Triage Model:** {TRIAGE_MODEL}
- **Synthesis Model:** {SYNTHESIS_MODEL}
- **Estimated Cost:** ${total_records * COST_PER_1K:.4f}

---

*Generated by Book 1: AI Builder's Launchpad - BI Engine*
"""
    return report


def run_pipeline(input_path: str, output_path: str) -> str:
    print(f"\n{'=' * 60}")
    print("BOOK 1: FEEDBACK INTELLIGENCE PIPELINE")
    print(f"{'=' * 60}\n")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key or api_key == "sk-ant-your-key-here":
        raise ValueError(
            "ANTHROPIC_API_KEY not set. Create a .env file or export the environment variable."
        )

    client = anthropic.Anthropic()

    print(f"[Node 0] Loading data from {input_path}...")
    df = pd.read_csv(input_path)
    df["email"] = df["email"].fillna("").str.strip()
    df = df[df["email"] != ""]
    print(f"  Loaded {len(df)} valid records\n")

    print("[Node 1] Running triage classification...")
    triage_results: list[Optional[TriageResult]] = []
    for idx, row in df.iterrows():
        result = triage_email(client, row["email"], int(row["email_id"]))
        triage_results.append(result)
        if (len(triage_results)) % 5 == 0:
            print(f"  Processed {len(triage_results)}/{len(df)}...")
    print(f"  Triage complete!\n")

    print("[Node 2] Extracting failure signals from high-priority emails...")
    valid_results = [r for r in triage_results if r is not None]
    high_priority = [r for r in valid_results if r.urgency == "High"]
    print(f"  Found {len(high_priority)} high-priority emails")

    failure_signals: list[FailureSignal] = []
    for result in high_priority:
        email_row = df[df["email_id"] == result.email_id].iloc[0]
        signal = extract_failure(client, email_row["email"], result.email_id)
        if signal:
            failure_signals.append(signal)
    print(f"  Extracted {len(failure_signals)} failure signals\n")

    print("[Node 3] Aggregating statistics (Python - Tier 1)...")
    aggregated = aggregate_results(triage_results)
    print(f"  Total: {aggregated['total_emails']}")
    print(f"  Successful: {aggregated['successful']}")
    print(f"  Failed: {aggregated['failed']}\n")

    print("[Node 4] Synthesizing executive insights...")
    synthesis = synthesize(client, aggregated, failure_signals)
    print("  Synthesis complete!\n")

    print("[Node 5] Generating Markdown report...")
    report = generate_report(aggregated, synthesis, failure_signals, len(df))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"  Report saved to {output_path}\n")

    print(f"{'=' * 60}")
    print("PIPELINE COMPLETE")
    print(f"{'=' * 60}")
    print(f"Records processed: {len(df)}")
    print(f"Estimated cost: ${len(df) * COST_PER_1K:.4f}")
    print(f"Output: {output_path}\n")

    return report


def main():
    parser = argparse.ArgumentParser(
        description="Book 1: Feedback Intelligence Pipeline"
    )
    parser.add_argument(
        "--input", "-i", default="data/sample_emails.csv", help="Input CSV path"
    )
    parser.add_argument(
        "--output",
        "-o",
        default="reports/feedback_report.md",
        help="Output Markdown path",
    )
    args = parser.parse_args()

    run_pipeline(args.input, args.output)


if __name__ == "__main__":
    main()

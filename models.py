from pydantic import BaseModel, Field
from typing import Optional

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


class AggregatedStats(BaseModel):
    total_emails: int
    successful: int
    failed: int
    by_category: dict
    by_urgency: dict

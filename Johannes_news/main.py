#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
immigration_news_watcher.py

Local prototype: scans Google News RSS for immigration/visa topics involving an origin
country and a destination country, fetches article text, applies rule-based or LLM
reasoning, and outputs a controlled JSON payload for your timeline engine.

Licensed for your project use. No scraping of paywalled content is attempted; this
script relies on RSS discovery + respectful extraction.
"""

import debugpy

# Let VS Code attach on port 5678
debugpy.listen(("0.0.0.0", 5678))
print("⏳ Waiting for debugger attach on port 5678...")
debugpy.wait_for_client()
print("✅ Debugger attached, continuing execution...")

import argparse
import json
import re
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

import feedparser
import requests
import trafilatura
from dateutil import parser as dtparser
from pydantic import BaseModel, Field, validator

# -------- Configuration --------

IMMIGRATION_KEYWORDS = [
    "immigration", "migrate", "migration", "emigration", "visa", "residence permit",
    "work permit", "student visa", "work visa", "blue card", "green card",
    "family reunification", "asylum", "naturalisation", "biometric", "appointment",
    "backlog", "suspension", "moratorium", "ban", "cap", "quota", "intake paused",
    "processing time", "embassy", "consulate", "VFS", "TLScontact",
    "health insurance", "proof of funds", "bank account", "blocked account",
    "financial requirement", "schengen", "border control"
]

# Map keywords to pipeline stages & default action bias
STAGE_MAP = {
    "visa": ["visa", "residence permit", "work permit", "student visa", "blue card", "green card",
             "family reunification", "embassy", "consulate", "appointment", "backlog",
             "suspension", "moratorium", "ban", "cap", "quota", "intake paused", "processing time",
             "schengen", "border control", "VFS", "TLScontact", "biometric"],
    "insurance": ["health insurance", "insurance"],
    "bank_account": ["bank account", "blocked account"],
    "proof_of_finance": ["proof of funds", "financial requirement", "bank statement"],
}

DEFAULT_TIMELINE_STAGES = ["visa", "insurance", "bank_account", "proof_of_finance"]

# -------- Data models (output contract) --------

class Source(BaseModel):
    title: str
    url: str
    published_at: Optional[str] = None
    publisher: Optional[str] = None

class Impact(BaseModel):
    stage: str  # "visa" | "insurance" | "bank_account" | "proof_of_finance"
    action: str  # "accelerate" | "delay" | "monitor"
    days_delta: int = 0
    rationale: str

    @validator("stage")
    def validate_stage(cls, v):
        allowed = set(DEFAULT_TIMELINE_STAGES)
        if v not in allowed:
            raise ValueError(f"stage must be one of {allowed}")
        return v

    @validator("action")
    def validate_action(cls, v):
        allowed = {"accelerate", "delay", "monitor"}
        if v not in allowed:
            raise ValueError(f"action must be one of {allowed}")
        return v

class Alert(BaseModel):
    id: str
    detected_at: str
    origin_country: str
    destination_country: str
    concern_level: str  # "low" | "medium" | "high"
    summary: str
    impacted_stages: List[Impact]
    sources: List[Source]

class AlertsEnvelope(BaseModel):
    version: str = "v1"
    run_id: str
    generated_at: str
    origin_country: str
    destination_country: str
    since_utc: str
    alerts: List[Alert]

# -------- Helpers --------

def build_google_news_rss_queries(origin: str, destination: str) -> List[str]:
    """
    Build a small set of focused Google News RSS queries combining countries and immigration keywords.
    We keep the number modest to avoid duplicates; dedup happens later anyway.
    """
    def q(s: str) -> str:
        # Encode for URL (very simple; requests will re-encode)
        return s.replace(" ", "+")
    base = "https://news.google.com/rss/search"
    # A few combined queries; Google News automatically expands related words.
    core_terms = [
        f'"visa" OR "residence permit" OR "work permit" OR "student visa"',
        f'"immigration" OR "migration" OR "emigration"',
        f'"embassy" OR "consulate" OR "appointment" OR "backlog"',
        f'"ban" OR "suspension" OR "moratorium" OR "quota" OR "cap" OR "intake paused"',
        f'"health insurance" OR "proof of funds" OR "blocked account" OR "bank account"',
    ]
    queries = []
    # Pair each core set with both countries once; this keeps it concise but relevant.
    for terms in core_terms:
        # Country pairing inside the same query keeps results tight
        search = f'({terms}) AND ("{origin}" OR "{destination}")'
        queries.append(f"{base}?q={q(search)}&hl=en-US&gl=US&ceid=US:en")
    return queries

def fetch_rss_entries(url: str) -> List[Dict[str, Any]]:
    feed = feedparser.parse(url)
    return getattr(feed, "entries", []) or []

def within_since(pubdate: Optional[str], since_dt: datetime) -> bool:
    if not pubdate:
        return True  # keep if unknown
    try:
        dt = dtparser.parse(pubdate)
        if not dt.tzinfo:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt >= since_dt
    except Exception:
        return True

def extract_text(url: str, timeout: int = 15) -> str:
    """
    Best-effort article text extraction using trafilatura.
    """
    try:
        downloaded = trafilatura.fetch_url(url, timeout=timeout)
        if not downloaded:
            return ""
        extracted = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
        return extracted or ""
    except Exception:
        return ""

def guess_stages_from_text(text: str) -> List[str]:
    text_low = text.lower()
    hit_stages = set()
    for stage, kws in STAGE_MAP.items():
        for kw in kws:
            if kw in text_low:
                hit_stages.add(stage)
                break
    if not hit_stages:
        # immigration/visa topics generally lean toward "visa"
        hit_stages.add("visa")
    return sorted(hit_stages)

def simple_rule_based_reasoner(title: str, text: str, origin: str, destination: str) -> Dict[str, Any]:
    """
    Heuristic triage if LLM is disabled/unavailable.
    Returns {concern_level, impacts[], summary}
    """
    body = (title + "\n\n" + text).lower()
    summary = title.strip()
    # concern
    high_triggers = ["ban", "suspend", "suspension", "moratorium", "halt", "pause", "stopped", "stop processing", "intake paused"]
    medium_triggers = ["backlog", "delay", "long wait", "longer wait", "processing time", "quota", "cap", "strike"]
    concern = "low"
    if any(w in body for w in high_triggers):
        concern = "high"
    elif any(w in body for w in medium_triggers):
        concern = "medium"

    stages = guess_stages_from_text(body)
    impacts = []
    for st in stages:
        if concern == "high":
            action = "accelerate" if st in ("visa", "proof_of_finance") else "monitor"
            delta = 30 if action == "accelerate" else 0
            rationale = "Potential suspension/ban/paused intake detected; start earlier or secure slots."
        elif concern == "medium":
            action = "accelerate" if st == "visa" else "monitor"
            delta = 14 if action == "accelerate" else 0
            rationale = "Processing delays or quotas indicated; consider starting earlier."
        else:
            action = "monitor"
            delta = 0
            rationale = "Relevant but no clear immediate risk."
        impacts.append({
            "stage": st,
            "action": action,
            "days_delta": delta,
            "rationale": rationale
        })
    return {"concern_level": concern, "impacts": impacts, "summary": summary}

# -------- Optional: Gemini reasoning via google-generativeai --------

def llm_reasoner_gemini(text: str, model_name: str = "gemini-1.5-pro") -> Optional[Dict[str, Any]]:
    """
    Uses google-generativeai (hosted by Google) with GOOGLE_API_KEY.
    Produces structured JSON: {concern_level, impacts[], summary}
    """
    try:
        import google.generativeai as genai
        from google.generativeai import types

        import os
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return None
        genai.configure(api_key=api_key)
        sys_inst = (
            "You are an analyst for a relocation timeline assistant. "
            "Given a news article, decide if it materially affects migration steps "
            "(visa, insurance, bank_account, proof_of_finance). "
            "Return strict JSON with keys: concern_level in ['low','medium','high'], "
            "impacts (list of {stage, action in ['accelerate','delay','monitor'], days_delta (int), rationale}), "
            "summary (<=35 words). Be concise and pragmatic."
        )
        prompt = f"""Article:
{text}

Output schema:
{{
  "concern_level": "low|medium|high",
  "impacts": [{{"stage":"visa|insurance|bank_account|proof_of_finance","action":"accelerate|delay|monitor","days_delta":int,"rationale":"string"}}],
  "summary": "string max 35 words"
}}
Return ONLY the JSON object."""

        model = genai.GenerativeModel(model_name, system_instruction=sys_inst)
        resp = model.generate_content(prompt, generation_config=types.GenerationConfig(
            temperature=0.2, max_output_tokens=300
        ))
        cand = resp.candidates[0].content.parts[0].text if resp.candidates else ""
        # Strip code fences if present
        cand = re.sub(r"^```json\s*|\s*```$", "", cand.strip(), flags=re.IGNORECASE | re.MULTILINE)
        data = json.loads(cand)
        # Lightweight validation
        if "concern_level" in data and "impacts" in data and "summary" in data:
            return data
        return None
    except Exception:
        return None

# -------- Main pipeline --------

def run_pipeline(origin: str, destination: str, since_days: int, use_llm: bool,
                 model_name: str, max_articles: int) -> AlertsEnvelope:
    since_dt = datetime.now(timezone.utc) - timedelta(days=since_days)
    queries = build_google_news_rss_queries(origin, destination)

    seen_urls = set()
    stories = []

    for q in queries:
        entries = fetch_rss_entries(q)
        for e in entries:
            link = e.get("link") or e.get("id") or ""
            if not link or link in seen_urls:
                continue
            seen_urls.add(link)

            published = e.get("published") or e.get("pubDate") or e.get("updated")
            if not within_since(published, since_dt):
                continue

            title = e.get("title", "").strip()
            publisher = (e.get("source", {}) or {}).get("title") or e.get("source") or ""
            stories.append({
                "title": title,
                "url": link,
                "published": published,
                "publisher": publisher,
            })

    # Sort newest first and trim
    def sort_key(s):
        try:
            return dtparser.parse(s.get("published") or "") or datetime.min.replace(tzinfo=timezone.utc)
        except Exception:
            return datetime.min.replace(tzinfo=timezone.utc)
    stories.sort(key=lambda s: sort_key(s), reverse=True)
    if max_articles > 0:
        stories = stories[:max_articles]

    alerts: List[Alert] = []
    for s in stories:
        text = extract_text(s["url"])
        # Fall back to title for reasoning if extraction failed
        reasoning_text = (s["title"] + "\n\n" + text).strip()

        if use_llm:
            llm_out = llm_reasoner_gemini(reasoning_text, model_name=model_name)
        else:
            llm_out = None

        if llm_out:
            concern_level = llm_out.get("concern_level", "low")
            impacts_in = llm_out.get("impacts", [])
            summary = llm_out.get("summary", s["title"])[:300]
            impacts: List[Impact] = []
            for it in impacts_in:
                try:
                    impacts.append(Impact(**it))
                except Exception:
                    # Skip malformed impact entries
                    continue
            if not impacts:
                # Fallback stages if the LLM refused to commit
                for st in guess_stages_from_text(reasoning_text):
                    impacts.append(Impact(stage=st, action="monitor", days_delta=0,
                                          rationale="LLM output incomplete; monitoring recommended."))
        else:
            rb = simple_rule_based_reasoner(s["title"], text, origin, destination)
            concern_level = rb["concern_level"]
            impacts = [Impact(**it) for it in rb["impacts"]]
            summary = rb["summary"]

        alert = Alert(
            id=str(uuid.uuid4()),
            detected_at=datetime.now(timezone.utc).isoformat(),
            origin_country=origin,
            destination_country=destination,
            concern_level=concern_level,
            summary=summary,
            impacted_stages=impacts,
            sources=[Source(
                title=s["title"],
                url=s["url"],
                published_at=s.get("published"),
                publisher=s.get("publisher"),
            )]
        )
        alerts.append(alert)

    envelope = AlertsEnvelope(
        run_id=str(uuid.uuid4()),
        generated_at=datetime.now(timezone.utc).isoformat(),
        origin_country=origin,
        destination_country=destination,
        since_utc=since_dt.isoformat(),
        alerts=alerts
    )
    return envelope

def main():
    parser = argparse.ArgumentParser(description="Immigration news watcher → timeline recommendations")
    parser.add_argument("--origin", required=True, help="Origin country, e.g. 'India'")
    parser.add_argument("--destination", required=True, help="Destination country, e.g. 'Germany'")
    parser.add_argument("--since_days", type=int, default=3, help="Look back this many days (default 3)")
    parser.add_argument("--use_llm", type=lambda x: x.lower() in ("true","1","yes","y"), default=False,
                        help="Enable Gemini reasoning (default false)")
    parser.add_argument("--model", default="gemini-1.5-pro", help="Gemini model name if --use_llm true")
    parser.add_argument("--max_articles", type=int, default=40, help="Max articles to analyze (default 40)")
    parser.add_argument("--out_file", default="alerts.json", help="Where to write the JSON output")
    args = parser.parse_args()

    env = run_pipeline(
        origin=args.origin,
        destination=args.destination,
        since_days=args.since_days,
        use_llm=args.use_llm,
        model_name=args.model,
        max_articles=args.max_articles,
    )
    with open(args.out_file, "w", encoding="utf-8") as f:
        json.dump(json.loads(env.json()), f, ensure_ascii=False, indent=2)

    print(f"Wrote {args.out_file} with {len(env.alerts)} alert(s).")

if __name__ == "__main__":
    main()

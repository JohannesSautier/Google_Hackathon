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
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

import feedparser
import trafilatura
from dateutil import parser as dtparser
from pydantic import BaseModel, validator

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

# -------- Data models --------

class Source(BaseModel):
    title: str
    url: str
    published_at: Optional[str] = None
    publisher: Optional[str] = None

class Impact(BaseModel):
    stage: str
    action: str
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
    concern_level: str
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
    def q(s: str) -> str:
        return s.replace(" ", "+")
    base = "https://news.google.com/rss/search"
    core_terms = [
        f'"visa" OR "residence permit" OR "work permit" OR "student visa"',
        f'"immigration" OR "migration" OR "emigration"',
        f'"embassy" OR "consulate" OR "appointment" OR "backlog"',
        f'"ban" OR "suspension" OR "moratorium" OR "quota" OR "cap" OR "intake paused"',
        f'"health insurance" OR "proof of funds" OR "blocked account" OR "bank account"',
    ]
    queries = []
    for terms in core_terms:
        search = f'({terms}) AND ("{origin}" OR "{destination}")'
        queries.append(f"{base}?q={q(search)}&hl=en-US&gl=US&ceid=US:en")
    return queries

def fetch_rss_entries(url: str):
    feed = feedparser.parse(url)
    return getattr(feed, "entries", []) or []

def within_since(pubdate: Optional[str], since_dt: datetime) -> bool:
    if not pubdate:
        return True
    try:
        dt = dtparser.parse(pubdate)
        if not dt.tzinfo:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt >= since_dt
    except Exception:
        return True

def extract_text(url: str, timeout: int = 15) -> str:
    try:
        downloaded = trafilatura.fetch_url(url, timeout=timeout)
        if not downloaded:
            return ""
        extracted = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
        return extracted or ""
    except Exception:
        return ""

def contains_relevant_keywords(text: str) -> bool:
    """Pre-filter: only keep articles with immigration/visa keywords."""
    text_low = text.lower()
    return any(kw in text_low for kw in IMMIGRATION_KEYWORDS)

def guess_stages_from_text(text: str) -> List[str]:
    text_low = text.lower()
    hit_stages = set()
    for stage, kws in STAGE_MAP.items():
        for kw in kws:
            if kw in text_low:
                hit_stages.add(stage)
                break
    if not hit_stages:
        hit_stages.add("visa")
    return sorted(hit_stages)

def simple_rule_based_reasoner(title: str, text: str, origin: str, destination: str) -> Dict[str, Any]:
    body = (title + "\n\n" + text).lower()
    summary = title.strip()
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
            rationale = "Potential suspension/ban/paused intake detected."
        elif concern == "medium":
            action = "accelerate" if st == "visa" else "monitor"
            delta = 14 if action == "accelerate" else 0
            rationale = "Processing delays or quotas indicated."
        else:
            action = "monitor"
            delta = 0
            rationale = "Relevant but no immediate risk."
        impacts.append({
            "stage": st,
            "action": action,
            "days_delta": delta,
            "rationale": rationale
        })
    return {"concern_level": concern, "impacts": impacts, "summary": summary}

# -------- Optional: Gemini reasoning --------

def llm_reasoner_gemini(text: str, model_name: str = "gemini-1.5-pro") -> Optional[Dict[str, Any]]:
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
            "ONLY consider news about immigration, visas, residence permits, "
            "embassies/consulates, proof of finance, health insurance, or banking. "
            "Ignore news about TikTok, social media, gaming, politics unrelated to immigration, "
            "and ignore countries other than the specified origin/destination. "
            "Return JSON: concern_level (low|medium|high), impacts "
            "(list of {stage, action, days_delta, rationale}), summary."
        )
        prompt = f"""Article:
{text}

Output schema:
{{
  "concern_level": "low|medium|high",
  "impacts": [{{"stage":"visa|insurance|bank_account|proof_of_finance","action":"accelerate|delay|monitor","days_delta":int,"rationale":"string"}}],
  "summary": "string"
}}
Return ONLY the JSON object."""
        model = genai.GenerativeModel(model_name, system_instruction=sys_inst)
        resp = model.generate_content(prompt, generation_config=types.GenerationConfig(
            temperature=0.2, max_output_tokens=300
        ))
        cand = resp.candidates[0].content.parts[0].text if resp.candidates else ""
        cand = re.sub(r"^```json\s*|\s*```$", "", cand.strip(), flags=re.MULTILINE)
        data = json.loads(cand)
        if "concern_level" in data and "impacts" in data and "summary" in data:
            # Post-filter stages
            valid_stages = set(DEFAULT_TIMELINE_STAGES)
            data["impacts"] = [i for i in data["impacts"] if i.get("stage") in valid_stages]
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
        combined_text = (s["title"] + "\n\n" + text).strip()

        # 🔹 Pre-filter: drop irrelevant stories early
        if not contains_relevant_keywords(combined_text):
            continue

        if use_llm:
            llm_out = llm_reasoner_gemini(combined_text, model_name=model_name)
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
                    continue
            if not impacts:
                for st in guess_stages_from_text(combined_text):
                    impacts.append(Impact(stage=st, action="monitor", days_delta=0,
                                          rationale="LLM output incomplete."))
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
    parser.add_argument("--origin", required=True)
    parser.add_argument("--destination", required=True)
    parser.add_argument("--since_days", type=int, default=3)
    parser.add_argument("--use_llm", type=lambda x: x.lower() in ("true","1","yes","y"), default=False)
    parser.add_argument("--model", default="gemini-1.5-pro")
    parser.add_argument("--max_articles", type=int, default=40)
    parser.add_argument("--out_file", default="alerts.json")
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

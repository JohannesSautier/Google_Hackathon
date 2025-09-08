#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
immigration_formalities_pairwatch.py

Purpose
-------
Track ONLY immigration/border/consular formalities for a specific country pair,
and produce *actionable* guidance for the traveler going FROM destination TO origin
(e.g., Germany -> India). Uses a layered approach:
  1) LLM (or strict rules fallback) quickly screens HEADLINES.
  2) If kept, fetch & extract full TEXT; LLM checks a formalities checklist.
  3) Rate each article (relevance/actionability) and output a tight JSON.

Notes
-----
- No paywall scraping; relies on Google News RSS queries + respectful extraction.
- If no LLM keys are present, falls back to careful rule-based heuristics.
- Direction is explicit and enforced; results are *only* for the two countries.

CLI
---
python immigration_formalities_pairwatch.py \
  --origin "India" \
  --destination "Germany" \
  --direction "destination_to_origin" \
  --since_days 5 \
  --max_articles 40 \
  --use_llm false \
  --out_file "pair_alerts.json"

Licensed for your project use.
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
from typing import List, Dict, Any, Optional, Tuple

from pydantic import field_validator

import feedparser
import trafilatura
from dateutil import parser as dtparser
from pydantic import BaseModel, Field, validator

# --------------------------- Configuration ---------------------------

PAIR_TERMS = [
    # Core immigration/consular/border terms (keep *tight*)
    "immigration", "emigration", "migration",
    "visa", "residence permit", "work permit", "student visa",
    "entry requirements", "exit requirements",
    "border control", "passport control",
    "airport immigration", "Schengen", "ETIAS", "EES",
    "consulate", "embassy", "VFS", "TLScontact",
    "biometric", "biometrics", "fingerprints",
    "police clearance", "PCC", "apostille",
    "health insurance", "travel insurance",
    "blocked account", "proof of funds", "financial requirement",
    "appointment", "backlog", "processing time", "suspension",
    "moratorium", "ban", "quota", "cap", "strike",
]

# What we consider "formalities" in the direction DESTINATION -> ORIGIN
FORMALITY_TYPES = {
    "exit_destination",   # exit/boarding checks in the *destination* country
    "entry_origin",       # entry/immigration at the *origin* country on arrival
    "transit",            # third-country transit formalities
    "carrier_rules",      # airline/airport carrier document checks
}

FORMALITY_CATEGORIES = {
    "visa", "residence_permit", "passport_validity", "biometrics",
    "appointment", "insurance", "proof_of_funds", "police_clearance",
    "registration_deregistration", "border_control", "health_certificate",
}

ACTIONS = {"new_requirement", "changed_requirement", "suspension", "resumed", "delay", "reminder"}

# RSS query depth
RSS_CORES = [
    '"visa" OR "residence permit" OR "entry requirements" OR "exit requirements"',
    '"immigration" OR "border control" OR "passport control" OR "airport immigration"',
    '"consulate" OR "embassy" OR "VFS" OR "TLScontact" OR "appointment"',
    '"biometric" OR "police clearance" OR "apostille" OR "proof of funds" OR "blocked account"',
    '"Schengen" OR "ETIAS" OR "EES"',
]

# --------------------------- Data models -----------------------------

class Source(BaseModel):
    title: str
    url: str
    published_at: Optional[str] = None
    publisher: Optional[str] = None

class FormalityImpact(BaseModel):
    segment: str = Field(description="exit_destination | entry_origin | transit | carrier_rules")
    category: str = Field(description="e.g., visa, biometrics, insurance, proof_of_funds, ...")
    action: str = Field(description="new_requirement | changed_requirement | suspension | resumed | delay | reminder")
    who_applies: Optional[str] = Field(default=None, description="Nationality/permit class/visa category if stated")
    effective_date: Optional[str] = None
    deadline: Optional[str] = None
    details: str
    recommended_actions: List[str] = Field(default_factory=list)

    @field_validator("segment", mode="before")
    def _segment_ok(cls, v): 
        if v not in FORMALITY_TYPES: 
            raise ValueError(f"segment must be one of {sorted(FORMALITY_TYPES)}")
        return v

    @field_validator("category", mode="before")
    def _category_ok(cls, v):
        if v not in FORMALITY_CATEGORIES:
            raise ValueError(f"category must be one of {sorted(FORMALITY_CATEGORIES)}")
        return v

    @field_validator("action", mode="before")
    def _action_ok(cls, v):
        if v not in ACTIONS:
            raise ValueError(f"action must be one of {sorted(ACTIONS)}")
        return v

class LayerScores(BaseModel):
    headline_keep: bool
    headline_reason: str
    headline_score: int = Field(ge=0, le=100)
    text_keep: bool
    text_reason: str
    relevance_score: int = Field(ge=0, le=100)
    actionability_score: int = Field(ge=0, le=100)
    risk_level: str = Field(description="low | medium | high")

class PairAlert(BaseModel):
    id: str
    detected_at: str
    origin_country: str
    destination_country: str
    direction: str  # "destination_to_origin" only for now
    concern_level: str  # "low|medium|high" (copies risk_level)
    summary: str
    formalities: List[FormalityImpact]
    scores: LayerScores
    sources: List[Source]

class Envelope(BaseModel):
    version: str = "v2"
    run_id: str
    generated_at: str
    origin_country: str
    destination_country: str
    direction: str
    since_utc: str
    alerts: List[PairAlert]
    # A concise traveler-focused rollup
    final_guidance: Dict[str, Any]

# --------------------------- Helpers --------------------------------

def _q(s: str) -> str:
    return s.replace(" ", "+")

def build_pair_queries(origin: str, destination: str) -> List[str]:
    """
    Build very strict Google News RSS queries that *force* the country pair
    to appear, reducing unrelated noise (e.g., US/TikTok).
    """
    base = "https://news.google.com/rss/search"
    pairs = [
        f'"{origin}" AND "{destination}"',
        f'"{destination}" AND "{origin}"',
        f'"Embassy of {destination}" AND "{origin}"',
        f'"Embassy of {origin}" AND "{destination}"',
        f'"Consulate" AND ("{origin}" AND "{destination}")',
    ]
    urls = []
    for core in RSS_CORES:
        for pair in pairs:
            search = f'({core}) AND ({pair})'
            urls.append(f"{base}?q={_q(search)}&hl=en-US&gl=US&ceid=US:en")
    # De-duplicate while preserving order
    seen, deduped = set(), []
    for u in urls:
        if u not in seen:
            deduped.append(u); seen.add(u)
    return deduped

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

def extract_text(url: str, timeout: int = 20) -> str:
    try:
        downloaded = trafilatura.fetch_url(url, timeout=timeout)
        if not downloaded:
            return ""
        extracted = trafilatura.extract(
            downloaded,
            include_comments=False,
            include_tables=False,
            with_metadata=False
        )
        return extracted or ""
    except Exception:
        return ""

def _has_any_kw(s: str, kws: List[str]) -> bool:
    sl = s.lower()
    return any(k.lower() in sl for k in kws)

def _strict_pair_check(s: str, origin: str, destination: str) -> bool:
    sl = s.lower()
    return (origin.lower() in sl) and (destination.lower() in sl)

# --------------------------- LLM plumbing ----------------------------

def _try_gemini():
    try:
        import os, google.generativeai as genai
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            return None
        genai.configure(api_key=key)
        return genai
    except Exception:
        return None

def _gemini_complete(client, sys_inst: str, prompt: str, model="gemini-1.5-flash") -> Optional[str]:
    try:
        model = client.GenerativeModel(model)
        resp = model.generate_content(f"{sys_inst}\n\n{prompt}")
        return resp.text
    except Exception:
        return None

def _clean_json_block(s: str) -> Optional[dict]:
    if not s:
        return None
    txt = s.strip()
    # Remove backticked fences if present
    txt = re.sub(r"^```json\s*|\s*```$", "", txt, flags=re.MULTILINE).strip()
    try:
        return json.loads(txt)
    except Exception:
        # Try to find first JSON object in text
        m = re.search(r"\{[\s\S]*\}", txt)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                return None
    return None

# --------------------------- Layer 1: Headline screen ----------------

def headline_screen(title: str, origin: str, destination: str) -> Tuple[bool, str, int]:
    """
    Prefer LLM to judge if the headline is *about formalities* for this pair.
    Output: keep?, reason, score(0..100)
    """
    client = _try_openai()
    sys_inst = (
        "You judge news headlines for immigration/visa/border/consular FORMALITIES. "
        "Keep ONLY if it concerns *procedural requirements* (visa, entry/exit rules, "
        "appointments, embassy/VFS/TLS, biometrics, proof of funds, Schengen/ETIAS/EES) "
        f"AND clearly involves both countries: {origin} and {destination}. "
        "Ignore politics/tech/social media/gaming/business unless they *change a border/consular rule*. "
        "Return compact JSON: {keep:boolean, reason:string, score:int 0-100}."
    )
    user = f"Headline: {title}\nPair: {origin} <-> {destination}\nReturn ONLY JSON."
    if client:
        out = _openai_complete(client, sys_inst, user)
        data = _clean_json_block(out)
        if data and isinstance(data.get("keep"), bool):
            return bool(data["keep"]), data.get("reason",""), int(data.get("score", 0))

    # ---- Rule fallback
    keep = _has_any_kw(title, PAIR_TERMS) and _strict_pair_check(title, origin, destination)
    score = 70 if keep else 10
    reason = "Pair+keyword match" if keep else "Missing pair/formalities cues"
    return keep, reason, score

# --------------------------- Layer 2: Text checklist -----------------

CHECKLIST = [
    "Mentions BOTH countries explicitly",
    "Relates to IMMIGRATION/BORDER/CONSULAR formalities (not general news)",
    "Contains a concrete REQUIREMENT or PROCESS change (visa/entry/exit/biometrics/etc.)",
    "Has when/where it APPLIES (who, date/effective period, category)",
    "Actionable next steps for traveler (e.g., book biometrics, carry PCC, insurance)",
]

def text_assess(title: str, text: str, origin: str, destination: str, direction: str) -> Tuple[bool, str, int, int, str, List[FormalityImpact]]:
    """
    Prefer LLM to validate checklist + extract formalities.
    Returns: keep?, reason, relevance_score, actionability_score, risk_level, formalities[]
    """
    client = _try_openai()
    sys_inst = (
        "You are an immigration formalities analyst. Evaluate the article STRICTLY for the given pair "
        f"({origin} & {destination}) and DIRECTION: traveler going FROM destination TO origin."
        "\nFocus ONLY on: exit_destination, entry_origin, transit, carrier_rules.\n"
        "If the article doesn't clearly impact those formalities, reject it."
        "\nExtract concise, actionable formalities. Keep to the two countries."
        "\nReturn JSON with fields:"
        """
{
  "keep": true|false,
  "reason": "string",
  "relevance_score": 0-100,
  "actionability_score": 0-100,
  "risk_level": "low|medium|high",
  "formalities": [
    {
      "segment": "exit_destination|entry_origin|transit|carrier_rules",
      "category": "visa|residence_permit|passport_validity|biometrics|appointment|insurance|proof_of_funds|police_clearance|registration_deregistration|border_control|health_certificate",
      "action": "new_requirement|changed_requirement|suspension|resumed|delay|reminder",
      "who_applies": "string or null",
      "effective_date": "ISO date or null",
      "deadline": "ISO date or null",
      "details": "short, concrete details",
      "recommended_actions": ["short imperative bullets"]
    }
  ]
}
        """
        "IMPORTANT: Do not invent facts; if unsure, set keep=false."
    )
    user = (
        f"TITLE: {title}\n\nARTICLE:\n{text[:12000]}\n\n"
        f"PAIR: {origin} & {destination}\nDIRECTION: {direction}\n"
        f"CHECKLIST: {CHECKLIST}\nReturn ONLY JSON."
    )
    if client:
        out = _openai_complete(client, sys_inst, user)
        data = _clean_json_block(out)
        if data and isinstance(data.get("keep"), bool):
            keep = bool(data["keep"])
            reason = data.get("reason", "")
            rel = int(max(0, min(100, int(data.get("relevance_score", 0)))))
            act = int(max(0, min(100, int(data.get("actionability_score", 0)))))
            risk = data.get("risk_level", "low")
            formalities = []
            for it in data.get("formalities", []):
                try:
                    formalities.append(FormalityImpact(**it))
                except Exception:
                    continue
            return keep, reason, rel, act, risk, formalities

    # ---- Rule fallback (tight and conservative)
    body = (title + "\n" + (text or "")).lower()
    if not (_strict_pair_check(body, origin, destination) and _has_any_kw(body, PAIR_TERMS)):
        return False, "Fails pair/formalities check", 10, 10, "low", []

    formalities = []
    # Extremely conservative pattern cues:
    def add(segment, category, action, details, recs):
        try:
            formalities.append(FormalityImpact(
                segment=segment,
                category=category,
                action=action,
                details=details,
                recommended_actions=recs
            ))
        except Exception:
            pass

    # Visa/entry/exit cues
    if "visa" in body or "entry requirement" in body or "entry requirements" in body:
        add("entry_origin", "visa", "reminder",
            "Article mentions visa/entry formalities impacting the pair.",
            ["Verify visa type and validity", "Carry supporting documents at arrival"]
        )
    if "exit" in body or "departure" in body or "boarding denied" in body:
        add("exit_destination", "border_control", "reminder",
            "Possible departure/exit checks referenced.",
            ["Arrive early for exit controls", "Keep permit/overstay records clean"]
        )
    if "biometric" in body or "fingerprint" in body:
        add("entry_origin", "biometrics", "changed_requirement",
            "Biometric capture likely required/expanded.",
            ["Budget extra time for biometrics at arrival"]
        )
    if "insurance" in body:
        add("entry_origin", "insurance", "reminder",
            "Travel/health insurance referenced for entry.",
            ["Carry policy certificate meeting origin rules"]
        )
    if "proof of funds" in body or "blocked account" in body:
        add("entry_origin", "proof_of_funds", "reminder",
            "Financial sufficiency referenced.",
            ["Carry bank statements or acceptable proof"]
        )

    # Score heuristics
    rel = 65 if formalities else 40
    act = 60 if formalities else 30
    risk = "medium" if any(f.action in {"suspension", "changed_requirement"} for f in formalities) else "low"
    return True, "Rule-based keep", rel, act, risk, formalities

# --------------------------- Pipeline --------------------------------

def run_pipeline(origin: str, destination: str, direction: str, since_days: int, use_llm: bool,
                 max_articles: int) -> Envelope:
    assert direction == "destination_to_origin", "Only destination_to_origin supported in this version."

    since_dt = datetime.now(timezone.utc) - timedelta(days=since_days)
    queries = build_pair_queries(origin, destination)

    seen_urls = set()
    raw_stories: List[Dict[str, Any]] = []

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
            title = (e.get("title") or "").strip()
            publisher = None
            src = e.get("source") or {}
            if isinstance(src, dict):
                publisher = src.get("title")
            elif isinstance(src, str):
                publisher = src
            raw_stories.append({
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
    raw_stories.sort(key=lambda s: sort_key(s), reverse=True)
    if max_articles > 0:
        raw_stories = raw_stories[:max_articles]

    alerts: List[PairAlert] = []

    for s in raw_stories:
        title = s["title"]
        # Layer 1: headline screen
        keep_h, reason_h, score_h = headline_screen(title, origin, destination)
        if not keep_h:
            continue

        # Fetch full text
        text = extract_text(s["url"])
        combined = (title + "\n\n" + (text or "")).strip()

        # Quick hard filter to avoid junk slipping in
        if not _strict_pair_check(combined, origin, destination) or not _has_any_kw(combined, PAIR_TERMS):
            continue

        # Layer 2: text assessment
        keep_t, reason_t, rel, act, risk, formalities = text_assess(title, text, origin, destination, direction)
        if not keep_t:
            continue

        # Build output
        scores = LayerScores(
            headline_keep=True,
            headline_reason=reason_h,
            headline_score=score_h,
            text_keep=True,
            text_reason=reason_t,
            relevance_score=rel,
            actionability_score=act,
            risk_level=risk
        )

        summary = title[:280]
        alert = PairAlert(
            id=str(uuid.uuid4()),
            detected_at=datetime.now(timezone.utc).isoformat(),
            origin_country=origin,
            destination_country=destination,
            direction=direction,
            concern_level=risk,
            summary=summary,
            formalities=formalities,
            scores=scores,
            sources=[Source(
                title=s["title"],
                url=s["url"],
                published_at=s.get("published"),
                publisher=s.get("publisher"),
            )]
        )
        alerts.append(alert)

    # Build final traveler guidance (compact, deduplicated)
    def _rollup_formalities(items: List[FormalityImpact]) -> Dict[str, List[str]]:
        out: Dict[str, List[str]] = {
            "exit_destination": [],
            "entry_origin": [],
            "transit": [],
            "carrier_rules": [],
        }
        seen = set()
        for it in items:
            line = f"[{it.category}/{it.action}] {it.details}"
            if it.who_applies:
                line += f" (Who: {it.who_applies})"
            if it.effective_date:
                line += f" (Effective: {it.effective_date})"
            if it.deadline:
                line += f" (Deadline: {it.deadline})"
            key = (it.segment, line)
            if key in seen:
                continue
            seen.add(key)
            out[it.segment].append(line)
        return out

    all_formalities = [f for a in alerts for f in a.formalities]
    rollup = _rollup_formalities(all_formalities)

    # A minimal set of “do now” steps distilled from recommended_actions
    do_now: List[str] = []
    seen_step = set()
    for a in alerts:
        for f in a.formalities:
            for step in (f.recommended_actions or []):
                if step not in seen_step:
                    do_now.append(step); seen_step.add(step)

    env = Envelope(
        run_id=str(uuid.uuid4()),
        generated_at=datetime.now(timezone.utc).isoformat(),
        origin_country=origin,
        destination_country=destination,
        direction=direction,
        since_utc=(datetime.now(timezone.utc) - timedelta(days=since_days)).isoformat(),
        alerts=alerts,
        final_guidance={
            "direction": direction,
            "summary_counts": {
                "alerts": len(alerts),
                "exit_destination_items": len(rollup["exit_destination"]),
                "entry_origin_items": len(rollup["entry_origin"]),
                "transit_items": len(rollup["transit"]),
                "carrier_rule_items": len(rollup["carrier_rules"]),
            },
            "exit_destination": rollup["exit_destination"],
            "entry_origin": rollup["entry_origin"],
            "transit": rollup["transit"],
            "carrier_rules": rollup["carrier_rules"],
            "do_now": do_now[:12],  # cap
        }
    )
    return env

# --------------------------- CLI main --------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Pair-specific immigration formalities watcher (destination → origin)."
    )
    parser.add_argument("--origin", required=True, help="Origin country (arrival country)")
    parser.add_argument("--destination", required=True, help="Destination country (departure country)")
    parser.add_argument("--direction", default="destination_to_origin", choices=["destination_to_origin"])
    parser.add_argument("--since_days", type=int, default=5)
    parser.add_argument("--use_llm", type=lambda x: x.lower() in ("true","1","yes","y"), default=True,
                        help="If keys unavailable, the script auto-falls back to rules.")
    parser.add_argument("--max_articles", type=int, default=40)
    parser.add_argument("--out_file", default="pair_alerts.json")
    args = parser.parse_args()

    env = run_pipeline(
        origin=args.origin,
        destination=args.destination,
        direction=args.direction,
        since_days=args.since_days,
        use_llm=args.use_llm,
        max_articles=args.max_articles
    )
    with open(args.out_file, "w", encoding="utf-8") as f:
        json.dump(json.loads(env.json()), f, ensure_ascii=False, indent=2)

    print(f"Wrote {args.out_file} with {len(env.alerts)} alert(s).")
    if env.alerts:
        print("Final guidance (compact):")
        print(json.dumps(env.final_guidance, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

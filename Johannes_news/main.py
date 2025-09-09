#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
immigration_time_risk_datapoints.py

Purpose
-------
Scan news for a specific country pair (traveler goes FROM destination TO origin),
detect TIME-RISK to immigration/consular formalities (e.g., processing delays,
backlogs, strikes, intake pauses, slot scarcity, closures), and output a list of
datapoints in your exact required schema:

{
  "dataPoints": [
    { ...INFORMATIONAL... },
    { ...PROPOSAL (if risk warrants)... }
  ]
}

Notes
-----
- LLM: Google Gemini (set GEMINI_API_KEY). Falls back to rule-based if unset.
- Source: Google News RSS (no paywalls scraped).
- Relevance is *pair strict* and *time-risk focused*.
- The "country" in relevantFor is the ISO-3 code of the **origin** (arrival / immigrate-to country).
- Supports optional input process plan JSON (current start/end dates for steps).
  If omitted, uses a small hardcoded plan you can replace later.

CLI
---
python immigration_time_risk_datapoints.py \
  --origin "Germany" \
  --destination "India" \
  --since_days 5 \
  --max_articles 40 \
  --use_llm true \
  --out_file "datapoints.json" \
  [--process_file process_plan.json]
"""

import argparse
import json
import os
import re
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

import feedparser
import trafilatura
from dateutil import parser as dtparser

# ------------- Config: time-risk focus keywords --------------

TIME_RISK_TERMS = [
    "processing time", "longer processing", "delays", "delay", "backlog",
    "appointment unavailable", "no slots", "slot scarcity", "VFS outage",
    "TLScontact outage", "system outage", "strike", "walkout", "industrial action",
    "moratorium", "intake paused", "suspension", "halt processing",
    "embassy closed", "consulate closed", "biometrics delay", "visa center closed",
    "peak season", "surge in applications", "quota reached", "cap reached",
]

PAIR_TERMS = [
    "immigration", "visa", "residence permit", "entry requirements", "exit requirements",
    "border control", "passport control", "airport immigration", "Schengen", "ETIAS", "EES",
    "consulate", "embassy", "VFS", "TLScontact", "biometric", "biometrics", "fingerprints",
    "appointment", "backlog", "processing time", "suspension", "moratorium", "quota", "cap", "strike",
]

# Output enums you specified
PROCESS_TYPES = {"VISA_APPLICATION", "INSURANCE", "PROOFFINANCE", "BANKACCOUNT"}
SOURCE_TYPE_NEWS = "NEWS_API"

# ------------- Hardcoded plan (used if --process_file not provided) -------------
# You can change these dates; format must be ISO-8601 with 'Z'
def _default_process_plan(now_utc: datetime) -> Dict[str, Dict[str, str]]:
    return {
        "VISA_APPLICATION": {
            "startDate": _dt_to_iso(now_utc + timedelta(days=7)),
            "endDate":   _dt_to_iso(now_utc + timedelta(days=37)),
        },
        "INSURANCE": {
            "startDate": _dt_to_iso(now_utc + timedelta(days=10)),
            "endDate":   _dt_to_iso(now_utc + timedelta(days=12)),
        },
        "PROOFFINANCE": {
            "startDate": _dt_to_iso(now_utc + timedelta(days=5)),
            "endDate":   _dt_to_iso(now_utc + timedelta(days=8)),
        },
        "BANKACCOUNT": {
            "startDate": _dt_to_iso(now_utc + timedelta(days=3)),
            "endDate":   _dt_to_iso(now_utc + timedelta(days=6)),
        },
    }

# ------------- Utilities --------------

def _dt_to_iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

def _iso_to_dt(s: str) -> Optional[datetime]:
    try:
        dt = dtparser.parse(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None

_COUNTRY_TO_ALPHA3 = {
    # add more as needed
    "germany": "DEU",
    "india": "IND",
    "united states": "USA",
    "united kingdom": "GBR",
    "france": "FRA",
    "spain": "ESP",
    "italy": "ITA",
    "canada": "CAN",
    "australia": "AUS",
    "netherlands": "NLD",
    "belgium": "BEL",
    "switzerland": "CHE",
    "austria": "AUT",
    "ireland": "IRL",
    "poland": "POL",
    "portugal": "PRT",
}

def _alpha3(country_name: str) -> str:
    if not country_name:
        return "XXX"
    k = country_name.strip().lower()
    if k in _COUNTRY_TO_ALPHA3:
        return _COUNTRY_TO_ALPHA3[k]
    # fallback heuristic
    letters = re.sub(r"[^A-Za-z]", "", country_name.upper())
    return (letters[:3] or "XXX").ljust(3, "X")

def _q(s: str) -> str:
    return s.replace(" ", "+")

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)

def _unique_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"

def _has_any_kw(s: str, kws: List[str]) -> bool:
    sl = s.lower()
    return any(k.lower() in sl for k in kws)

def _strict_pair_check(s: str, origin: str, destination: str) -> bool:
    sl = s.lower()
    return (origin.lower() in sl) and (destination.lower() in sl)

def build_pair_queries(origin: str, destination: str) -> List[str]:
    base = "https://news.google.com/rss/search"
    RSS_CORES = [
        '"visa" OR "residence permit" OR "entry requirements" OR "exit requirements"',
        '"immigration" OR "border control" OR "passport control" OR "airport immigration"',
        '"consulate" OR "embassy" OR "VFS" OR "TLScontact" OR "appointment"',
        '"biometric" OR "police clearance" OR "proof of funds" OR "blocked account"',
        '"Schengen" OR "ETIAS" OR "EES"',
    ]
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
    # de-dup
    seen, deduped = set(), []
    for u in urls:
        if u not in seen:
            deduped.append(u)
            seen.add(u)
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
            with_metadata=False,
        )
        return extracted or ""
    except Exception:
        return ""

# ------------- Gemini plumbing --------------

def _try_gemini():
    try:
        import google.generativeai as genai
    except Exception:
        return None
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        return None
    try:
        genai.configure(api_key=key)
        return genai
    except Exception:
        return None

def _gemini_complete(client, sys_inst: str, prompt: str, model="gemini-1.5-flash") -> Optional[str]:
    try:
        m = client.GenerativeModel(model, system_instruction=sys_inst)
        resp = m.generate_content(prompt)
        return getattr(resp, "text", None)
    except Exception:
        return None

def _json_from_text(s: Optional[str]) -> Any:
    if not s:
        return None
    txt = s.strip()
    # strip fenced JSON if present
    txt = re.sub(r"^```json\s*|\s*```$", "", txt, flags=re.MULTILINE).strip()
    try:
        return json.loads(txt)
    except Exception:
        # try first {...} or [...]
        m = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", txt)
        if m:
            try:
                return json.loads(m.group(1))
            except Exception:
                return None
    return None

# ------------- LLM: informational summary + process type --------------

def llm_informational_summary(title: str, text: str, origin: str, destination: str) -> Dict[str, Any]:
    """
    Returns:
      {
        "summary": str,        # <= 400 chars
        "processType": "...",  # VISA_APPLICATION | INSURANCE | PROOFFINANCE | BANKACCOUNT
        "confidence": float    # 0..1
      }
    """
    client = _try_gemini()
    if not client:
        # fallback summary
        body = (title + ". " + (text[:600] or "")).strip()
        summary = (body[:400] + ("..." if len(body) > 400 else ""))
        return {"summary": summary or title, "processType": "VISA_APPLICATION", "confidence": 0.60}

    sys_inst = (
        "Summarize immigration/consular FORMALITY news for a traveler pair. "
        "Return a compact summary (<=400 chars), pick a processType among "
        "VISA_APPLICATION, INSURANCE, PROOFFINANCE, BANKACCOUNT, and give confidence 0..1. "
        "Only consider formalities relevant to visas/consulate/appointments/biometrics/finance/insurance."
    )
    user = f"""PAIR: {origin} & {destination}
TITLE: {title}
ARTICLE:
{text[:3000]}

Return ONLY JSON:
{{
  "summary": "string (<=400 chars)",
  "processType": "VISA_APPLICATION|INSURANCE|PROOFFINANCE|BANKACCOUNT",
  "confidence": 0.0-1.0
}}"""
    out = _gemini_complete(client, sys_inst, user)
    data = _json_from_text(out)
    if isinstance(data, dict) and data.get("summary") and data.get("processType") in PROCESS_TYPES:
        try:
            conf = float(data.get("confidence", 0.6))
            conf = max(0.0, min(1.0, conf))
        except Exception:
            conf = 0.6
        return {
            "summary": str(data["summary"])[:400],
            "processType": str(data["processType"]),
            "confidence": conf,
        }
    # fallback
    body = (title + ". " + (text[:600] or "")).strip()
    summary = (body[:400] + ("..." if len(body) > 400 else ""))
    return {"summary": summary or title, "processType": "VISA_APPLICATION", "confidence": 0.60}

# ------------- LLM: deep time-risk analysis --------------

def llm_article_time_threat(title: str, text: str, origin: str, destination: str) -> Optional[Dict[str, Any]]:
    """
    Returns (or None if not confident):
      {
        "keep": bool,
        "threat_score": 0-100,
        "urgency_days": 0-60,                 # recommend bringing actions forward (+) or delay (-)? -> We use positive for bring-forward, convert to negative shiftDays
        "risk_level": "low|medium|high",
        "reason": "short justification",
        "evidence_type": "official|media|rumor|unspecified",
        "signals": [ ... ]                    # e.g., backlog, strike, moratorium, slot_scarcity
      }
    """
    client = _try_gemini()
    if not client:
        # Conservative rule fallback
        body = (title + "\n" + (text or "")).lower()
        if not (_has_any_kw(body, TIME_RISK_TERMS) and _strict_pair_check(body, origin, destination)):
            return None
        signals = [t.replace(" ", "_") for t in TIME_RISK_TERMS if t in body][:4]
        return {
            "keep": True,
            "threat_score": 65,
            "urgency_days": 14,
            "risk_level": "medium",
            "reason": "Pair+time-risk terms detected (rule-based).",
            "evidence_type": "media",
            "signals": signals or ["backlog"],
        }

    sys_inst = (
        "You are an immigration TIME-RISK analyst. Determine whether this article impacts the TIMELINE of visa/permit/appointment/"
        "biometrics/consular-center operations for the traveler pair (two countries). Focus ONLY on *time* impact: "
        "longer processing times, backlogs, appointment scarcity, strikes, moratoria/halts, closures, biometrics delays. "
        "If there is time risk, recommend 'urgency_days' the traveler should bring steps forward. "
        "If not confident, set keep=false. Return ONLY JSON."
    )
    schema = """{
  "keep": true|false,
  "threat_score": 0-100,
  "urgency_days": 0-60,
  "risk_level": "low|medium|high",
  "reason": "short justification",
  "evidence_type": "official|media|rumor|unspecified",
  "signals": ["backlog"|"strike"|"moratorium"|"closure"|"slot_scarcity"|"system_outage"|"quota_cap"|"biometrics_delay"...]
}"""
    user = f"""PAIR: {origin} & {destination}
TITLE: {title}

ARTICLE:
{text[:12000]}

Schema:
{schema}
Return ONLY JSON."""
    out = _gemini_complete(client, sys_inst, user)
    data = _json_from_text(out)
    if isinstance(data, dict) and isinstance(data.get("keep"), bool):
        # normalize
        try:
            ts = int(max(0, min(100, int(data.get("threat_score", 0)))))
        except Exception:
            ts = 0
        try:
            ud = int(max(0, min(60, int(data.get("urgency_days", 0)))))
        except Exception:
            ud = 0
        rl = str(data.get("risk_level", "low"))
        reason = str(data.get("reason", ""))[:400]
        ev = str(data.get("evidence_type", "unspecified"))
        sigs = list(data.get("signals") or [])[:8]
        return {
            "keep": bool(data.get("keep")),
            "threat_score": ts,
            "urgency_days": ud,
            "risk_level": rl,
            "reason": reason,
            "evidence_type": ev,
            "signals": sigs,
        }
    return None

# ------------- Mapper: formalities category → processType -------------

def _guess_process_type(title: str, text: str) -> str:
    body = (title + "\n" + (text or "")).lower()
    if "insurance" in body:
        return "INSURANCE"
    if "blocked account" in body or "proof of funds" in body or "financial requirement" in body:
        return "PROOFFINANCE"
    if "bank account" in body:
        return "BANKACCOUNT"
    return "VISA_APPLICATION"

# ------------- Datapoint builders ------------------------------------

def build_informational_datapoint(source_uri: str,
                                  retrieved_at_iso: str,
                                  origin_alpha3: str,
                                  summary: str,
                                  process_type: str,
                                  confidence: float) -> Dict[str, Any]:
    return {
        "dataPointId": _unique_id("dp_info"),
        "dataType": "INFORMATIONAL",
        "sourceType": SOURCE_TYPE_NEWS,
        "sourceURI": source_uri,
        "retrievedAt": retrieved_at_iso,
        "relevantFor": {
            "processType": process_type,
            "stepKey": "",
            "country": origin_alpha3,
        },
        "rawContent": summary,
        "confidenceScore": round(float(confidence), 4),
    }

def build_proposal_datapoint(source_uri: str,
                             retrieved_at_iso: str,
                             origin_alpha3: str,
                             summary: str,
                             process_type: str,
                             confidence: float,
                             shift_days: int,
                             new_start: Optional[str],
                             new_end: Optional[str],
                             reason: str) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"shiftDays": shift_days}
    if new_start:
        payload["startDate"] = new_start
    if new_end:
        payload["endDate"] = new_end
    return {
        "dataPointId": _unique_id("dp_prop"),
        "dataType": "PROPOSAL",
        "sourceType": SOURCE_TYPE_NEWS,
        "sourceURI": source_uri,
        "retrievedAt": retrieved_at_iso,
        "relevantFor": {
            "processType": process_type,
            "stepKey": "",
            "country": origin_alpha3,
        },
        "rawContent": summary,
        "confidenceScore": round(float(confidence), 4),
        "proposal": {
            "targetStepKey": process_type,
            "action": "UPDATE_STEP_STATUS",
            "payload": payload,
            "reason": reason[:600],
        }
    }

# ------------- Pipeline ----------------------------------------------

def run_pipeline(origin: str,
                 destination: str,
                 since_days: int,
                 use_llm: bool,
                 max_articles: int,
                 process_plan: Dict[str, Dict[str, str]],
                 model: str = "gemini-1.5-flash") -> Dict[str, Any]:

    if use_llm and not _try_gemini():
        # No key present; silently downgrade to rules
        print("⚠️ GEMINI_API_KEY not set or Gemini import failed; falling back to rule-based processing.")
        use_llm = False

    since_dt = _now_utc() - timedelta(days=since_days)
    queries = build_pair_queries(origin, destination)

    seen_urls = set()
    stories: List[Dict[str, Any]] = []
    for q in queries:
        entries = fetch_rss_entries(q)
        for e in entries:
            link = e.get("link") or e.get("id") or ""
            if not link or link in seen_urls:
                continue
            published = e.get("published") or e.get("pubDate") or e.get("updated")
            if not within_since(published, since_dt):
                continue
            title = (e.get("title") or "").strip()
            # Keep raw; we'll tighten later
            stories.append({
                "title": title,
                "url": link,
                "published": published,
                "publisher": (e.get("source") or {}).get("title") if isinstance(e.get("source"), dict) else e.get("source"),
            })
            seen_urls.add(link)

    # Sort newest first
    def sort_key(s):
        try:
            return dtparser.parse(s.get("published") or "") or datetime.min.replace(tzinfo=timezone.utc)
        except Exception:
            return datetime.min.replace(tzinfo=timezone.utc)
    stories.sort(key=lambda s: sort_key(s), reverse=True)
    if max_articles > 0:
        stories = stories[:max_articles]

    origin_alpha3 = _alpha3(origin)
    retrieved_at_iso = _dt_to_iso(_now_utc())
    datapoints: List[Dict[str, Any]] = []

    for s in stories:
        title = s["title"]
        # Early headline gate: must be pair + time/formalities hint
        if not (_strict_pair_check(title, origin, destination) and (_has_any_kw(title, TIME_RISK_TERMS) or _has_any_kw(title, PAIR_TERMS))):
            continue

        text = extract_text(s["url"])
        combined = (title + "\n\n" + (text or "")).strip()
        if not _strict_pair_check(combined, origin, destination):
            continue

        # 1) INFORMATIONAL (summary + classification)
        info = llm_informational_summary(title, text, origin, destination) if use_llm else {
            "summary": (title + ". " + (text[:350] or ""))[:400],
            "processType": _guess_process_type(title, text),
            "confidence": 0.6,
        }
        process_type = info["processType"] if info["processType"] in PROCESS_TYPES else _guess_process_type(title, text)
        info_dp = build_informational_datapoint(
            source_uri=s["url"],
            retrieved_at_iso=retrieved_at_iso,
            origin_alpha3=origin_alpha3,
            summary=info["summary"],
            process_type=process_type,
            confidence=info["confidence"],
        )
        datapoints.append(info_dp)

        # 2) PROPOSAL (only if time-risk is present)
        risk = llm_article_time_threat(title, text, origin, destination) if use_llm else llm_article_time_threat(title, text, origin, destination)
        # (call is same; function handles fallback)
        if risk and risk.get("keep"):
            urgency_days = int(risk.get("urgency_days", 0))
            threat_score = int(risk.get("threat_score", 0))
            risk_level = str(risk.get("risk_level", "low"))
            reason = f"{risk.get('reason','')} (signals: {', '.join(risk.get('signals', []))})".strip()

            # Convert to proposal payload
            # We define: positive urgency_days => bring forward by that many days => shiftDays = -urgency_days
            shift_days = -urgency_days if urgency_days > 0 else 0

            # If we know planned dates, compute new startDate (and carry endDate if meaningful)
            plan = process_plan.get(process_type, {})
            cur_start = _iso_to_dt(plan.get("startDate", "")) if isinstance(plan, dict) else None
            cur_end = _iso_to_dt(plan.get("endDate", "")) if isinstance(plan, dict) else None
            new_start_iso = _dt_to_iso(cur_start - timedelta(days=urgency_days)) if (cur_start and urgency_days > 0) else None
            new_end_iso = _dt_to_iso(cur_end) if cur_end else None  # we don't auto-change end; your engine can recalc

            # Confidence for proposal: scale by threat_score + evidence type
            base_conf = max(0.5, min(0.95, (threat_score / 100.0) * 0.9 + 0.05))
            if str(risk.get("evidence_type","")).lower() == "official":
                base_conf = min(0.98, base_conf + 0.1)

            prop_dp = build_proposal_datapoint(
                source_uri=s["url"],
                retrieved_at_iso=retrieved_at_iso,
                origin_alpha3=origin_alpha3,
                summary=info["summary"],
                process_type=process_type,
                confidence=base_conf,
                shift_days=shift_days,
                new_start=new_start_iso,
                new_end=new_end_iso,
                reason=reason or "Time-risk to process timing inferred from article.",
            )
            datapoints.append(prop_dp)

    return {"dataPoints": datapoints}

# ------------- Main ---------------------------------------------------

def load_process_plan(path: Optional[str]) -> Dict[str, Dict[str, str]]:
    if not path:
        return _default_process_plan(_now_utc())
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Expect either {"processes": {...}} or direct dict
        if isinstance(data, dict) and "processes" in data and isinstance(data["processes"], dict):
            return data["processes"]
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return _default_process_plan(_now_utc())

def main():
    parser = argparse.ArgumentParser(description="Immigration time-risk → datapoints (destination → origin).")
    parser.add_argument("--origin", required=True, help="Arrival country (you immigrate to this country).")
    parser.add_argument("--destination", required=True, help="Departure country (you leave from here).")
    parser.add_argument("--since_days", type=int, default=5)
    parser.add_argument("--max_articles", type=int, default=40)
    parser.add_argument("--use_llm", type=lambda x: x.lower() in ("true","1","yes","y"), default=True)
    parser.add_argument("--process_file", default=None, help="Optional JSON file with process plan.")
    parser.add_argument("--model", default="gemini-1.5-flash")
    parser.add_argument("--out_file", default="datapoints.json")
    args = parser.parse_args()

    process_plan = load_process_plan(args.process_file)
    result = run_pipeline(
        origin=args.origin,
        destination=args.destination,
        since_days=args.since_days,
        use_llm=args.use_llm,
        max_articles=args.max_articles,
        process_plan=process_plan,
        model=args.model,
    )

    with open(args.out_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Wrote {args.out_file} with {len(result.get('dataPoints', []))} dataPoint(s).")

if __name__ == "__main__":
    main()

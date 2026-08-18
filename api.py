from fastapi import FastAPI, UploadFile, File, Form, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import sys
import os
import pandas as pd
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from athena.data_loader import PRGIDataLoader
from athena.pipeline import AthenaVerificationPipeline
from athena.certificate import generate_verification_certificate
from athena.app_tracker import ApplicationTracker

app = FastAPI(title="Athena API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_loader: Optional[PRGIDataLoader] = None
_pipeline: Optional[AthenaVerificationPipeline] = None
_tracker: Optional[ApplicationTracker] = None


def get_services():
    global _loader, _pipeline, _tracker
    if _loader is None:
        _loader = PRGIDataLoader.get_instance("prgi_titles.csv")
    if _pipeline is None:
        _pipeline = AthenaVerificationPipeline(_loader)
    if _tracker is None:
        _tracker = ApplicationTracker.get_instance()
    return _loader, _pipeline, _tracker


class VerifyRequest(BaseModel):
    title: str
    language: str = ""
    periodicity: str = ""
    state: str = ""
    district: str = ""
    publisher: str = ""
    owner: str = ""


class SubmitAppRequest(BaseModel):
    title: str
    language: str
    periodicity: str
    state: str
    district: str
    applicant_name: str
    organization: str
    email: str
    phone: str


class DecisionRequest(BaseModel):
    status: str  # APPROVED, REJECTED, MODIFICATION_REQUESTED
    remarks: str


class FlagDerogatoryRequest(BaseModel):
    term: str
    source: str = "COMMUNITY_FLAG"


import math

def safe_val(v):
    if v is None:
        return None
    if isinstance(v, (dict,)):
        return {str(k): safe_val(val) for k, val in v.items()}
    if isinstance(v, (list, tuple, set)):
        return [safe_val(elem) for elem in v]
    try:
        val_f = float(v)
        if math.isnan(val_f) or math.isinf(val_f):
            return 0.0
        if isinstance(v, (int, float)):
            return v
        return val_f
    except (ValueError, TypeError):
        return v


@app.get("/api/health")
def health():
    loader, _, tracker = get_services()
    return {
        "status": "ok",
        "database_titles_count": len(loader.df),
        "applications_count": len(tracker.get_all_applications())
    }


@app.post("/api/verify")
def verify(req: VerifyRequest):
    _, pipeline, _ = get_services()
    result = pipeline.verify_title(
        proposed_title=req.title,
        language=req.language,
        periodicity=req.periodicity,
        state=req.state,
        district=req.district,
        publisher=req.publisher,
        owner=req.owner,
    )

    candidates = []
    for c in result.get("top_candidates", [])[:10]:
        candidates.append({
            "sn": c.get("sn"),
            "title": c.get("matched_title", ""),
            "language": c.get("language", ""),
            "state": c.get("state", ""),
            "periodicity": c.get("periodicity", ""),
            "owner": c.get("owner", ""),
            "score": safe_val(c.get("final_similarity_score", c.get("score", 0.0))),
            "soundex_match": c.get("soundex_match", False),
        })

    compliance = result.get("compliance", {})
    violations = [
        {"rule": v.get("rule", ""), "severity": v.get("severity", ""), "detail": v.get("detail", "")}
        for v in compliance.get("violations", [])
    ]

    alternatives = [
        {"title": a.get("title", ""), "reason": a.get("reason", "")}
        for a in result.get("smart_alternatives", [])
    ]

    stage3 = result.get("stage3_results", {})
    influential_words = stage3.get("influential_words", [])
    attention = stage3.get("attention_weights", {})
    graph_data = stage3.get("graph_data", {"nodes": [], "edges": []})

    return safe_val({
        "status": result["status"],
        "status_desc": result["status_desc"],
        "acceptance_probability": result["acceptance_probability"],
        "rejection_probability": result["rejection_probability"],
        "highest_similarity": result["highest_similarity"],
        "total_latency_ms": result.get("total_latency_ms", 0.0),
        "stage0": result.get("stage0_results", {
            "flagged": False,
            "confidence_score": 0.0,
            "time_ms": 0.0,
            "flagged_tokens": []
        }),
        "stage1": {
            "flagged": result["stage1_results"]["flagged"],
            "max_score": result["stage1_results"]["max_score"],
            "time_ms": result["stage1_results"]["time_ms"],
        },
        "stage2": {
            "flagged": result["stage2_results"]["flagged"],
            "max_score": result["stage2_results"]["max_score"],
            "time_ms": result["stage2_results"]["time_ms"],
        },
        "top_candidates": candidates,
        "violations": violations,
        "recommendations": result.get("recommendations", []),
        "smart_alternatives": alternatives,
        "influential_words": influential_words,
        "attention_weights": attention,
        "graph_data": graph_data,
        "raw_audit": result
    })


@app.get("/api/applications")
def list_applications():
    _, _, tracker = get_services()
    return tracker.get_all_applications()


@app.post("/api/applications/submit")
def submit_application(req: SubmitAppRequest):
    _, pipeline, tracker = get_services()
    audit = pipeline.verify_title(
        proposed_title=req.title,
        language=req.language,
        periodicity=req.periodicity,
        state=req.state,
        district=req.district,
        publisher=req.applicant_name,
        owner=req.organization
    )
    app_id = tracker.submit_application(
        title=req.title,
        language=req.language,
        periodicity=req.periodicity,
        state=req.state,
        district=req.district,
        applicant_name=req.applicant_name,
        organization=req.organization,
        email=req.email,
        phone=req.phone,
        audit_result=audit
    )
    return {
        "app_id": app_id,
        "status": audit["status"],
        "auto_probability": audit["acceptance_probability"],
        "message": "Application logged successfully into PRGI Registry."
    }


@app.get("/api/applications/{app_id}")
def get_application(app_id: str):
    _, _, tracker = get_services()
    app_data = tracker.get_application(app_id)
    if not app_data:
        raise HTTPException(status_code=404, detail=f"Application '{app_id}' not found")
    return app_data


@app.post("/api/applications/{app_id}/decision")
def application_decision(app_id: str, req: DecisionRequest):
    _, _, tracker = get_services()
    updated = tracker.update_application_status(app_id, req.status, req.remarks)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Application '{app_id}' not found")
    return {"status": "success", "app_id": app_id, "new_status": req.status}


@app.get("/api/certificate/{app_id}", response_class=HTMLResponse)
def get_certificate_html(app_id: str):
    _, _, tracker = get_services()
    app_data = tracker.get_application(app_id)
    if not app_data or not app_data.get("audit_data"):
        raise HTTPException(status_code=404, detail="Certificate unavailable")
    html_code = generate_verification_certificate(app_data["audit_data"])
    return HTMLResponse(content=html_code)


@app.get("/api/analytics")
def get_analytics():
    loader, _, _ = get_services()
    df = loader.df

    # Languages
    lang_counts = df["language"].fillna("Unknown").value_counts().head(10).to_dict()
    languages = [{"name": k, "count": int(v)} for k, v in lang_counts.items()]

    # Periodicity
    per_counts = df["periodicity"].fillna("Unknown").value_counts().head(8).to_dict()
    periodicities = [{"name": k, "count": int(v)} for k, v in per_counts.items()]

    # States
    state_counts = df["publication_state"].fillna("Unknown").value_counts().head(10).to_dict()
    states = [{"name": k, "count": int(v)} for k, v in state_counts.items()]

    # High frequency words
    w_list = []
    for t in loader.titles[:5000]:
        w_list.extend([w for w in t.split() if len(w) > 3])
    keywords = [{"word": k, "count": int(v)} for k, v in Counter(w_list).most_common(10)]

    return {
        "total_titles": len(df),
        "languages": languages,
        "periodicities": periodicities,
        "states": states,
        "keywords": keywords,
    }


@app.get("/api/explorer")
def search_explorer(q: str = Query("", max_length=100), limit: int = 100):
    loader, _, _ = get_services()
    df = loader.df
    if not q.strip():
        sub = df.head(limit)
    else:
        sq = q.strip().upper()
        mask = (
            df["clean_title"].str.contains(sq, na=False) |
            df["owner"].fillna("").astype(str).str.upper().str.contains(sq, na=False) |
            df["registration_number"].fillna("").astype(str).str.upper().str.contains(sq, na=False)
        )
        sub = df[mask].head(limit)

    records = []
    for _, r in sub.iterrows():
        records.append({
            "sn": int(r["sn"]) if pd.notnull(r.get("sn")) else 0,
            "title": str(r["title"]),
            "registration_number": str(r.get("registration_number", "")),
            "registration_date": str(r.get("registration_date", "")),
            "language": str(r.get("language", "")),
            "periodicity": str(r.get("periodicity", "")),
            "publisher": str(r.get("publisher", "")),
            "owner": str(r.get("owner", "")),
            "publication_state": str(r.get("publication_state", "")),
            "publication_district": str(r.get("publication_district", "")),
        })
    return {"count": len(records), "records": records}


@app.post("/api/derogatory/flag")
def flag_derogatory_term(req: FlagDerogatoryRequest):
    from athena.derogatory_shield import DerogatoryShield
    shield = DerogatoryShield.get_instance()
    success = shield.add_seed_term(req.term, req.source)
    return {
        "status": "success" if success else "exists_or_invalid",
        "term": req.term,
        "total_seed_terms": len(shield.seed_terms),
        "message": f"Term '{req.term}' added to Stage 0 Derogatory Shield seed database with auto fuzzy expansion."
    }


@app.get("/api/derogatory/list")
def list_derogatory_terms():
    from athena.derogatory_shield import DerogatoryShield
    shield = DerogatoryShield.get_instance()
    return {
        "count": len(shield.seed_terms),
        "seed_terms": sorted(list(shield.seed_terms))
    }

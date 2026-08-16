import re

# Statutory restricted keywords under Emblems & Names Act and PRGI Guidelines
EMBLEM_RESTRICTED_WORDS = [
    "POLICE", "CBI", "CID", "CRIME BRANCH", "ANTI CORRUPTION", "VIGILANCE",
    "RASHTRAPATI", "PRESIDENT OF INDIA", "PRIME MINISTER", "PMO", "RAJ BHAVAN",
    "LOK SABHA", "RAJYA SABHA", "PARLIAMENT", "VIDHAN SABHA", "SUPREME COURT",
    "HIGH COURT", "JUDICIARY", "ASHOK CHAKRA", "BHARAT RATNA", "GOVERNMENT",
    "SARKAR", "GOVT", "ARMY", "NAVY", "AIR FORCE", "DEFENCE OF INDIA",
    "NATIONAL EMBLEM", "UNITED NATIONS", "WHO", "UNESCO", "INTERPOL"
]

PERIODICITY_TERMS = [
    "DAILY", "WEEKLY", "FORTNIGHTLY", "MONTHLY", "BIMONTHLY", "QUARTERLY",
    "ANNUAL", "YEARLY", "BIANNUAL", "EVENING", "MORNING", "DAINIK", "SAPTAHIK",
    "PAKHIK", "MASIK", "VARSHIK", "SANDHYA", "PRABHAT", "ROZANA"
]

GENERIC_DISALLOWED_PREFIX_SUFFIX = [
    "THE", "TODAY", "NEWS", "SAMAY", "TIMES", "EXPRESS", "BULLETIN", "INDIA", "BHARAT"
]

class PRGIRulesEngine:
    def __init__(self):
        pass

    def evaluate_compliance(self, title: str, language: str = "", periodicity: str = "", state: str = "", candidates: list = None) -> dict:
        violations = []
        warnings = []
        recommendations = []
        
        clean_title = re.sub(r"[^\w\s]", " ", title.upper())
        words = clean_title.split()
        
        # 1. Check Emblems and Names Act restrictions
        for restricted in EMBLEM_RESTRICTED_WORDS:
            pattern = rf"\b{re.escape(restricted)}\b"
            if re.search(pattern, clean_title):
                violations.append({
                    "rule": "Emblems & Names Act Violation",
                    "severity": "CRITICAL",
                    "detail": f"Title contains prohibited/restricted government symbol or entity word: '{restricted}'."
                })
                recommendations.append(f"Remove government or statutory term '{restricted}' from proposed title.")

        # 2. Check Periodicity Manipulation Rule
        # If proposed title has periodicity prefix/suffix and base title exists in candidates
        title_without_periodicity_words = [w for w in words if w not in PERIODICITY_TERMS]
        base_title = " ".join(title_without_periodicity_words).strip()
        
        if any(w in PERIODICITY_TERMS for w in words):
            for cand in (candidates or [])[:5]:
                cand_title = re.sub(r"[^\w\s]", " ", cand.get("matched_title", "").upper()).strip()
                cand_words = [w for w in cand_title.split() if w not in PERIODICITY_TERMS]
                cand_base = " ".join(cand_words).strip()
                
                if base_title and cand_base and (base_title == cand_base or base_title in cand_title):
                    violations.append({
                        "rule": "Periodicity Prefix/Suffix Disallowance",
                        "severity": "HIGH",
                        "detail": f"Adding or removing periodicity words (e.g., '{[w for w in words if w in PERIODICITY_TERMS]}') to registered title '{cand.get('matched_title')}' is not permissible."
                    })
                    recommendations.append(f"Modify the distinctive core title beyond adding periodicity markers.")
                    break

        # 3. Check Same State / Same Language Collision
        if candidates and state and language:
            for cand in candidates[:3]:
                c_state = str(cand.get("state", "")).strip().upper()
                c_lang = str(cand.get("language", "")).strip().upper()
                req_state = state.strip().upper()
                req_lang = language.strip().upper()
                
                if cand.get("stage1_score", 0) > 0.85 or cand.get("semantic_similarity", 0) > 0.85:
                    if req_state and c_state and (req_state in c_state or c_state in req_state):
                        if req_lang and c_lang and (req_lang in c_lang or c_lang in req_lang):
                            violations.append({
                                "rule": "Same State & Language Conflict",
                                "severity": "HIGH",
                                "detail": f"Title matches closely with '{cand.get('matched_title')}' registered in the same state ({cand.get('state')}) and language ({cand.get('language')})."
                            })

        # 4. Check Short Title / Single Word Generic Warning
        if len(words) == 1 and len(clean_title) < 4:
            warnings.append({
                "rule": "Single Word Short Title",
                "severity": "MEDIUM",
                "detail": "Very short single-letter or 2-3 letter titles have high collision rates and strict registration requirements."
            })
            recommendations.append("Consider adding a unique qualifier word to make the title distinctive.")

        is_compliant = len([v for v in violations if v["severity"] == "CRITICAL"]) == 0 and len([v for v in violations if v["severity"] == "HIGH"]) == 0

        return {
            "is_compliant": is_compliant,
            "violations": violations,
            "warnings": warnings,
            "recommendations": list(set(recommendations))
        }

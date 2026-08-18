import re

# Statutory restricted keywords under Emblems & Names Act and PRGI Guidelines (Requirement 3a)
EMBLEM_RESTRICTED_WORDS = [
    "POLICE", "CRIME", "CORRUPTION", "CBI", "CID", "ARMY", "ANTI CORRUPTION", "VIGILANCE",
    "RASHTRAPATI", "PRESIDENT OF INDIA", "PRIME MINISTER", "PMO", "RAJ BHAVAN",
    "LOK SABHA", "RAJYA SABHA", "PARLIAMENT", "VIDHAN SABHA", "SUPREME COURT",
    "HIGH COURT", "JUDICIARY", "ASHOK CHAKRA", "BHARAT RATNA", "GOVERNMENT",
    "SARKAR", "GOVT", "NAVY", "AIR FORCE", "DEFENCE OF INDIA",
    "NATIONAL EMBLEM", "UNITED NATIONS", "WHO", "UNESCO", "INTERPOL"
]

PERIODICITY_TERMS = [
    "DAILY", "WEEKLY", "FORTNIGHTLY", "MONTHLY", "BIMONTHLY", "QUARTERLY",
    "ANNUAL", "YEARLY", "BIANNUAL", "EVENING", "MORNING", "DAINIK", "SAPTAHIK",
    "PAKHIK", "MASIK", "VARSHIK", "SANDHYA", "PRABHAT", "ROZANA"
]

GENERIC_DISALLOWED_PREFIX_SUFFIX = [
    "THE", "TODAY", "NEWS", "SAMAY", "TIMES", "EXPRESS", "BULLETIN", "INDIA", "BHARAT", "SAMACHAR"
]

class PRGIRulesEngine:
    def __init__(self, data_loader=None):
        self.data_loader = data_loader

    def evaluate_compliance(
        self,
        title: str,
        language: str = "",
        periodicity: str = "",
        state: str = "",
        candidates: list = None,
        prior_conflicts: list = None
    ) -> dict:
        violations = []
        warnings = []
        recommendations = []
        
        clean_title = re.sub(r"[^\w\s]", " ", title.upper())
        clean_title = re.sub(r"\s+", " ", clean_title).strip()
        words = clean_title.split()
        
        # 1. Check Emblems and Names Act / Prohibited Words (Requirement 3a & 3b)
        for restricted in EMBLEM_RESTRICTED_WORDS:
            pattern = rf"\b{re.escape(restricted)}\b"
            if re.search(pattern, clean_title):
                violations.append({
                    "rule": "Disallowed Statutory Word Violation",
                    "severity": "CRITICAL",
                    "detail": f"Title contains prohibited statutory term: '{restricted}' (Prohibited under PRGI Guidelines & Emblems Act)."
                })
                recommendations.append(f"Remove prohibited term '{restricted}' from proposed title.")

        # 2. Check Periodicity Manipulation Rule (Requirement 3e)
        # If proposed title has periodicity prefix/suffix and base title exists in candidates
        title_without_periodicity_words = [w for w in words if w not in PERIODICITY_TERMS]
        base_title = " ".join(title_without_periodicity_words).strip()
        
        if any(w in PERIODICITY_TERMS for w in words):
            for cand in (candidates or [])[:5]:
                cand_title = re.sub(r"[^\w\s]", " ", cand.get("matched_title", "").upper()).strip()
                cand_words = [w for w in cand_title.split() if w not in PERIODICITY_TERMS]
                cand_base = " ".join(cand_words).strip()
                
                if base_title and cand_base and (base_title == cand_base or base_title in cand_title or cand_base in base_title):
                    violations.append({
                        "rule": "Periodicity Prefix/Suffix Disallowance",
                        "severity": "HIGH",
                        "detail": f"Adding or removing periodicity words (e.g. '{[w for w in words if w in PERIODICITY_TERMS]}') to existing registered title '{cand.get('matched_title')}' is strictly prohibited."
                    })
                    recommendations.append("Modify the distinctive core title beyond adding periodicity markers.")
                    break

        # 3. Check Combination of Existing Registered Titles (Requirement 3c)
        if self.data_loader and len(words) >= 2:
            db_titles_set = set(self.data_loader.titles)
            # Check all binary splits of words
            for split_idx in range(1, len(words)):
                part1 = " ".join(words[:split_idx])
                part2 = " ".join(words[split_idx:])
                
                # Normalize parts by also checking without 'THE'
                p1_clean = re.sub(r"^THE\s+", "", part1)
                p2_clean = re.sub(r"^THE\s+", "", part2)
                
                p1_match = part1 in db_titles_set or p1_clean in db_titles_set
                p2_match = part2 in db_titles_set or p2_clean in db_titles_set
                
                if p1_match and p2_match:
                    violations.append({
                        "rule": "Combined Existing Titles Disallowance",
                        "severity": "CRITICAL",
                        "detail": f"Title is formed by combining two distinct registered titles: '{part1}' and '{part2}' (Violation of Requirement 3c)."
                    })
                    recommendations.append(f"Do not combine existing registered titles ('{part1}' + '{part2}') into a single new title.")
                    break

        # 4. Check Prior Live Application Conflicts (Requirement 5b & Expected Solution c)
        if prior_conflicts:
            for conflict in prior_conflicts[:2]:
                violations.append({
                    "rule": "Prior Active Application Conflict",
                    "severity": "HIGH",
                    "detail": f"Title closely matches prior application '{conflict.get('title')}' (ID: {conflict.get('app_id')}, Status: {conflict.get('status')}) submitted on {conflict.get('submission_timestamp')}."
                })
                recommendations.append(f"Title collides with active application '{conflict.get('app_id')}'. Choose a distinctive title.")

        # 5. Check Same State / Same Language Collision
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

        # 6. Check Short Title / Single Word Generic Warning
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

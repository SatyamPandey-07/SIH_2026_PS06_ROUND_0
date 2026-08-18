import time
import re
from athena.data_loader import PRGIDataLoader
from athena.stage1_phonetic import Stage1PhoneticMatcher
from athena.stage2_semantic import Stage2SemanticMatcher
from athena.stage3_graph_xai import Stage3GraphAndXAI
from athena.rules_engine import PRGIRulesEngine, EMBLEM_RESTRICTED_WORDS, PERIODICITY_TERMS
from athena.app_tracker import ApplicationTracker
from athena.derogatory_shield import DerogatoryShield

DISTINCTIVE_QUALIFIERS = [
    "Horizon", "Chetna", "Darpan", "Insight", "Sentinel",
    "Manthan", "Sankalp", "Deepak", "Sandesh", "Vani",
    "Pratibha", "Prakash", "Kiran", "Post", "Times", "Chronicle", "Observer"
]

GENERIC_PUBLICATION_TERMS = {
    "CHRONICLE", "OBSERVER", "HORIZON", "DARPAN", "CHETNA", "MANTHAN", "SANKALP",
    "DEEPAK", "SANDESH", "VANI", "INSIGHT", "SENTINEL", "PRATIBHA", "PRAKASH", "KIRAN",
    "TIMES", "NEWS", "EXPRESS", "BULLETIN", "INDIA", "BHARAT", "GAZETTE", "POST",
    "DAILY", "WEEKLY", "FORTNIGHTLY", "MONTHLY", "DAINIK", "SAPTAHIK", "MASIK", "SAMAY",
    "PATRIKA", "SAMPARK", "HERALD", "TRIBUNE", "MIRROR", "LEADER", "DISPATCH", "SAMACHAR"
}

BRAND_PREFIXES = ["Nav", "Vindhya", "Prabhat", "Apex", "Subh", "Naya", "Avani", "Uday"]

class AthenaVerificationPipeline:
    def __init__(self, data_loader: PRGIDataLoader = None):
        self.loader = data_loader or PRGIDataLoader.get_instance()
        self.stage0 = DerogatoryShield.get_instance()
        self.stage1 = Stage1PhoneticMatcher(self.loader)
        self.stage2 = Stage2SemanticMatcher(self.loader)
        self.stage3 = Stage3GraphAndXAI(self.loader)
        self.rules = PRGIRulesEngine(self.loader)
        self.tracker = ApplicationTracker.get_instance()

    def generate_smart_alternatives(self, proposed_title: str, language: str = "", periodicity: str = "", state: str = "") -> list:
        """
        Generates unique, compliant title alternatives that avoid existing registered titles and PRGI restrictions.
        Pre-verifies generated titles so they pass verification with high approval probability.
        """
        clean_words = re.findall(r"\b\w+\b", proposed_title)
        
        # 1. Filter restricted & periodicity words
        unrestricted_words = [
            w for w in clean_words
            if w.upper() not in EMBLEM_RESTRICTED_WORDS and w.upper() not in PERIODICITY_TERMS
        ]
        
        # 2. Isolate core brand words (excluding generic publication suffixes)
        core_words = [
            w for w in unrestricted_words
            if w.upper() not in GENERIC_PUBLICATION_TERMS
        ]
        
        if core_words:
            core_brand = " ".join(core_words).title()
        elif unrestricted_words:
            core_brand = " ".join(unrestricted_words).title()
        else:
            core_brand = "Samachar"
            
        full_base = " ".join(unrestricted_words).title() if unrestricted_words else core_brand

        alternatives = []
        seen_titles = {proposed_title.upper().strip()}

        def check_candidate(cand_title):
            """Run the full verify_title pipeline. Returns (status, prob) or None if already seen/registered."""
            cand_upper = cand_title.upper().strip()
            if cand_upper in seen_titles or cand_upper in self.loader.titles:
                return None
            seen_titles.add(cand_upper)
            result = self.verify_title(
                proposed_title=cand_title,
                language=language,
                periodicity=periodicity,
                state=state,
                _skip_alternatives=True
            )
            return result["status"], result["acceptance_probability"], result["highest_similarity"]

        st_clean = state.strip().title() if state and state.strip() else ""

        approved = []   # status == APPROVED
        fallback = []   # status == UNDER_REVIEW (shown if < 4 APPROVEDs found)

        def _try(cand, reason_tpl):
            r = check_candidate(cand)
            if r is None:
                return
            status, prob, sim = r
            if status == "APPROVED":
                approved.append({"title": cand, "reason": reason_tpl.format(prob=prob, sim=sim*100)})
            elif status == "UNDER_REVIEW" and len(fallback) < 4:
                fallback.append({
                    "title": cand,
                    "reason": f"⚠️ Under Review ({prob}% probability, {sim*100:.1f}% similarity) — {reason_tpl.format(prob=prob, sim=sim*100)}"
                })

        # Strategy 1: Regional + core brand
        if st_clean:
            _try(f"{st_clean} {core_brand}", f"Regional qualifier '{st_clean}' distinguishes your brand by jurisdiction ({{prob}}% approval prob).")

        # Strategy 2: Core brand + qualifier
        for qual in DISTINCTIVE_QUALIFIERS:
            if len(approved) >= 4: break
            if qual.upper() in [w.upper() for w in clean_words]: continue
            _try(f"{core_brand} {qual}", f"Qualifier '{qual}' after your core brand reduces collision risk ({{prob}}% approval prob).")

        # Strategy 3: Prefix + core brand
        for pfx in BRAND_PREFIXES:
            if len(approved) >= 4: break
            _try(f"{pfx} {core_brand}", f"Prefix '{pfx}' creates a uniquely repositioned identity ({{prob}}% approval prob).")

        # Strategy 4: Prefix + core brand + qualifier
        for pfx in BRAND_PREFIXES:
            if len(approved) >= 4: break
            for qual in DISTINCTIVE_QUALIFIERS:
                if len(approved) >= 4: break
                if qual.upper() in [w.upper() for w in clean_words]: continue
                _try(f"{pfx} {core_brand} {qual}", f"Three-word compound '{pfx}·{core_brand}·{qual}' for maximum distinctiveness ({{prob}}% approval prob).")

        # Strategy 5: Regional + qualifier only (drop colliding core brand)
        if len(approved) < 4 and st_clean:
            for qual in DISTINCTIVE_QUALIFIERS:
                if len(approved) >= 4: break
                if qual.upper() in [w.upper() for w in clean_words]: continue
                _try(f"{st_clean} {qual}", f"Regional + qualifier form avoids the colliding core word entirely ({{prob}}% approval prob).")

        # Strategy 6: Prefix × qualifier grid (last resort — core brand dropped)
        if len(approved) < 4:
            for pfx in BRAND_PREFIXES:
                if len(approved) >= 4: break
                for qual in DISTINCTIVE_QUALIFIERS:
                    if len(approved) >= 4: break
                    _try(f"{pfx} {qual}", f"Fresh two-word brand with zero collision risk ({{prob}}% approval prob).")

        # Fill remaining slots with best UNDER_REVIEW candidates
        combined = approved + [f for f in fallback if f["title"] not in {a["title"] for a in approved}]
        return combined[:4]



    def verify_title(
        self,
        proposed_title: str,
        language: str = "",
        periodicity: str = "",
        state: str = "",
        district: str = "",
        publisher: str = "",
        owner: str = "",
        _skip_alternatives: bool = False
    ) -> dict:
        t0 = time.time()
        
        # 0. Run Stage 0 (Derogatory Content Shield)
        t_s0_0 = time.time()
        s0_res = self.stage0.check_title(proposed_title)
        s0_time_ms = (time.time() - t_s0_0) * 1000.0

        # Check active submitted applications tracker (Requirement 5b / Expected Solution c)
        prior_conflicts = self.tracker.check_prior_applications(proposed_title)

        # 1. Run Stage 1 (Fast Phonetic & Fuzzy)
        t_s1_0 = time.time()
        s1_res = self.stage1.match(proposed_title, top_k=10)
        s1_time_ms = (time.time() - t_s1_0) * 1000.0

        # 2. Run Stage 2 (Multilingual Semantic Similarity)
        t_s2_0 = time.time()
        s2_res = self.stage2.match(proposed_title, top_k=10)
        s2_time_ms = (time.time() - t_s2_0) * 1000.0

        # Merge candidate matches from Stage 1 & Stage 2
        combined_candidates = []
        seen_sns = set()

        for c in s1_res["candidates"]:
            seen_sns.add(c["sn"])
            c_dict = dict(c)
            c_dict["match_source"] = "Stage 1 (Phonetic/Fuzzy)"
            combined_candidates.append(c_dict)

        for c in s2_res["candidates"]:
            if c["sn"] not in seen_sns:
                seen_sns.add(c["sn"])
                c_dict = dict(c)
                c_dict["match_source"] = "Stage 2 (Semantic)"
                combined_candidates.append(c_dict)
            else:
                for existing in combined_candidates:
                    if existing["sn"] == c["sn"]:
                        existing["semantic_similarity"] = c["semantic_similarity"]
                        existing["stage2_flagged"] = c["is_flagged"]

        # Sort candidates by combined similarity
        for c in combined_candidates:
            s1_score = c.get("stage1_score", 0.0)
            s2_score = c.get("semantic_similarity", 0.0)
            c["final_similarity_score"] = round(max(s1_score, s2_score * 0.95), 4)

        combined_candidates.sort(key=lambda x: x["final_similarity_score"], reverse=True)

        # 3. Run Stage 3 (Graph & Explainability)
        xai_res = self.stage3.explain_title(proposed_title, combined_candidates)
        graph_data = self.stage3.build_subgraph_for_candidates(proposed_title, combined_candidates)

        # 4. Run PRGI Statutory Rules Check
        rules_res = self.rules.evaluate_compliance(
            title=proposed_title,
            language=language,
            periodicity=periodicity,
            state=state,
            candidates=combined_candidates,
            prior_conflicts=prior_conflicts
        )

        if s0_res["flagged"]:
            rules_res["violations"].append({
                "rule": "CONTENT_VIOLATION",
                "severity": "CRITICAL" if s0_res["status"] == "REJECTED" else "WARNING",
                "detail": f"Stage 0 Shield: Derogatory/offensive pattern detected (Confidence: {s0_res['confidence_score'] * 100:.0f}%). Flagged tokens: {s0_res['flagged_tokens']}"
            })
            rules_res["is_compliant"] = False

        # 5. Compute Final Probability Score & Status
        max_s1 = s1_res["max_score"]
        max_s2 = s2_res["max_score"]
        highest_similarity = max(max_s1, max_s2)

        # Non-linear Acceptance Penalty curve
        if highest_similarity <= 0.50:
            uniqueness_penalty = highest_similarity * 20.0
        elif highest_similarity <= 0.75:
            uniqueness_penalty = 10.0 + (highest_similarity - 0.50) * 120.0
        else:
            uniqueness_penalty = 40.0 + (highest_similarity - 0.75) * 240.0

        rule_penalty = 0.0
        for v in rules_res["violations"]:
            if v["severity"] == "CRITICAL":
                rule_penalty += 80.0
            elif v["severity"] == "HIGH":
                rule_penalty += 50.0
            elif v["severity"] == "MEDIUM":
                rule_penalty += 25.0
                
        for w in rules_res["warnings"]:
            rule_penalty += 10.0

        raw_prob = 100.0 - (uniqueness_penalty + rule_penalty)
        
        # Enforce PS06 Expected Solution (a) Constraint:
        # "If a title has a similarity score of 80%, the verification probability shall not be more than 100% - 80% = 20%"
        max_allowed_prob = max(0.0, 100.0 - (highest_similarity * 100.0))
        acceptance_probability = max(0.0, min(raw_prob, max_allowed_prob))
        acceptance_probability = round(acceptance_probability, 1)

        # Determine Decision Status
        if s0_res["status"] == "REJECTED":
            acceptance_probability = 0.0
            status = "REJECTED"
            status_desc = "Content Violation: Title contains derogatory or offensive terms flagged by Stage 0 Shield."
            status_color = "red"
        elif acceptance_probability >= 70.0 and rules_res["is_compliant"]:
            status = "APPROVED"
            status_desc = "High probability of approval. Title is distinctive and compliant with statutory PRGI rules."
            status_color = "green"
        elif acceptance_probability >= 30.0 and not any(v["severity"] == "CRITICAL" for v in rules_res["violations"]):
            status = "UNDER_REVIEW"
            status_desc = "Moderate risk of collision or guideline warning. Manual registrar evaluation recommended."
            status_color = "orange"
        else:
            status = "REJECTED"
            status_desc = "High probability of rejection due to existing duplicate titles or statutory guideline violations."
            status_color = "red"

        # Actionable Recommendations
        recommendations = list(rules_res["recommendations"])
        if highest_similarity > 0.75 and combined_candidates:
            top_match = combined_candidates[0]["matched_title"]
            recommendations.append(f"Title has {highest_similarity*100:.1f}% similarity with existing registered title '{top_match}'.")
            
        smart_alternatives = []
        if status in ["REJECTED", "UNDER_REVIEW"] and not _skip_alternatives and s0_res["status"] != "REJECTED":
            smart_alternatives = self.generate_smart_alternatives(proposed_title, language=language, periodicity=periodicity, state=state)

        total_time_ms = (time.time() - t0) * 1000.0

        return {
            "proposed_title": proposed_title,
            "status": status,
            "status_desc": status_desc,
            "status_color": status_color,
            "acceptance_probability": acceptance_probability,
            "rejection_probability": round(100.0 - acceptance_probability, 1),
            "highest_similarity": round(highest_similarity, 4),
            "stage0_results": {
                "flagged": s0_res["flagged"],
                "confidence_score": s0_res["confidence_score"],
                "time_ms": round(s0_time_ms, 2),
                "flagged_tokens": s0_res["flagged_tokens"]
            },
            "stage1_results": {
                "flagged": s1_res["flagged"],
                "max_score": s1_res["max_score"],
                "time_ms": round(s1_time_ms, 2),
                "candidates_count": len(s1_res["candidates"])
            },
            "stage2_results": {
                "flagged": s2_res["flagged"],
                "max_score": s2_res["max_score"],
                "time_ms": round(s2_time_ms, 2),
                "candidates_count": len(s2_res["candidates"])
            },
            "stage3_results": {
                "token_importance": xai_res["token_importance"],
                "attention_weights": xai_res["attention_weights"],
                "influential_words": xai_res["influential_words"],
                "graph_data": graph_data
            },
            "compliance": rules_res,
            "top_candidates": combined_candidates[:10],
            "recommendations": recommendations,
            "smart_alternatives": smart_alternatives,
            "prior_conflicts": prior_conflicts,
            "total_latency_ms": round(total_time_ms, 2)
        }

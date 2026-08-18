import time
import re
from athena.data_loader import PRGIDataLoader
from athena.stage1_phonetic import Stage1PhoneticMatcher
from athena.stage2_semantic import Stage2SemanticMatcher
from athena.stage3_graph_xai import Stage3GraphAndXAI
from athena.rules_engine import PRGIRulesEngine, EMBLEM_RESTRICTED_WORDS, PERIODICITY_TERMS
from athena.app_tracker import ApplicationTracker

DISTINCTIVE_QUALIFIERS = [
    "Chronicle", "Observer", "Horizon", "Darpan", "Chetna",
    "Manthan", "Sankalp", "Deepak", "Sandesh", "Vani",
    "Insight", "Sentinel", "Pratibha", "Prakash", "Kiran"
]

class AthenaVerificationPipeline:
    def __init__(self, data_loader: PRGIDataLoader = None):
        self.loader = data_loader or PRGIDataLoader.get_instance()
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
        safe_words = [
            w for w in clean_words
            if w.upper() not in EMBLEM_RESTRICTED_WORDS and w.upper() not in PERIODICITY_TERMS
        ]
        
        base_term = " ".join(safe_words).title() if safe_words else "Samachar"
        alternatives = []
        
        def is_verified_approved(cand_title):
            cand_clean = re.sub(r"[^\w\s]", " ", cand_title.upper()).strip()
            if cand_clean in self.loader.titles:
                return False, None
            s1_c = self.stage1.match(cand_title, top_k=5)
            s2_c = self.stage2.match(cand_title, top_k=5)
            max_s = max(s1_c["max_score"], s2_c["max_score"])
            if max_s > 0.75:
                return False, None
            rules_c = self.rules.evaluate_compliance(cand_title, language=language, periodicity=periodicity, state=state, candidates=s1_c["candidates"])
            if not rules_c["is_compliant"] or rules_c["violations"]:
                return False, None
            return True, max_s

        if state and state.strip():
            st_clean = state.strip().title()
            regional_alt = f"{st_clean} {base_term}".strip()
            ok, sim = is_verified_approved(regional_alt)
            if ok:
                alternatives.append({
                    "title": regional_alt,
                    "reason": f"Regional qualifier '{st_clean}' establishes distinct local identity and passes statutory verification."
                })

        for qual in DISTINCTIVE_QUALIFIERS:
            candidate_alt = f"{base_term} {qual}".strip()
            ok, sim = is_verified_approved(candidate_alt)
            if ok:
                alternatives.append({
                    "title": candidate_alt,
                    "reason": f"Distinctive qualifier '{qual}' added to establish brand uniqueness while passing PRGI compliance."
                })
            if len(alternatives) >= 4:
                break
                
        return alternatives[:4]

    def verify_title(
        self,
        proposed_title: str,
        language: str = "",
        periodicity: str = "",
        state: str = "",
        district: str = "",
        publisher: str = "",
        owner: str = ""
    ) -> dict:
        t0 = time.time()
        
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
        if acceptance_probability >= 70.0 and rules_res["is_compliant"]:
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
        if status in ["REJECTED", "UNDER_REVIEW"]:
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

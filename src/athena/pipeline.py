import time
from athena.data_loader import PRGIDataLoader
from athena.stage1_phonetic import Stage1PhoneticMatcher
from athena.stage2_semantic import Stage2SemanticMatcher
from athena.stage3_graph_xai import Stage3GraphAndXAI
from athena.rules_engine import PRGIRulesEngine

class AthenaVerificationPipeline:
    def __init__(self, data_loader: PRGIDataLoader = None):
        self.loader = data_loader or PRGIDataLoader.get_instance()
        self.stage1 = Stage1PhoneticMatcher(self.loader)
        self.stage2 = Stage2SemanticMatcher(self.loader)
        self.stage3 = Stage3GraphAndXAI(self.loader)
        self.rules = PRGIRulesEngine()

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
            candidates=combined_candidates
        )

        # 5. Compute Final Probability Score & Status
        max_s1 = s1_res["max_score"]
        max_s2 = s2_res["max_score"]
        highest_similarity = max(max_s1, max_s2)

        # Calculation of Acceptance Probability (Uniqueness & Compliance)
        # 100% means perfectly unique and compliant, 0% means direct collision / violation
        uniqueness_penalty = highest_similarity * 80.0
        
        rule_penalty = 0.0
        for v in rules_res["violations"]:
            if v["severity"] == "CRITICAL":
                rule_penalty += 75.0
            elif v["severity"] == "HIGH":
                rule_penalty += 45.0
            elif v["severity"] == "MEDIUM":
                rule_penalty += 20.0
                
        for w in rules_res["warnings"]:
            rule_penalty += 10.0

        acceptance_probability = max(0.0, min(100.0, 100.0 - (uniqueness_penalty + rule_penalty)))
        acceptance_probability = round(acceptance_probability, 1)

        # Determine Decision Status
        if acceptance_probability >= 75.0 and rules_res["is_compliant"]:
            status = "APPROVED"
            status_desc = "High probability of approval. Title is unique and compliant with PRGI guidelines."
            status_color = "green"
        elif acceptance_probability >= 45.0:
            status = "UNDER_REVIEW"
            status_desc = "Moderate risk of collision or guideline warning. Manual review recommended."
            status_color = "orange"
        else:
            status = "REJECTED"
            status_desc = "High probability of rejection due to existing duplicate titles or PRGI guideline violations."
            status_color = "red"

        # Actionable Recommendations
        recommendations = list(rules_res["recommendations"])
        if highest_similarity > 0.80 and combined_candidates:
            top_match = combined_candidates[0]["matched_title"]
            recommendations.append(f"Title has {highest_similarity*100:.1f}% similarity with existing registered title '{top_match}'.")
            # Suggest alternative variants
            base_tokens = [t for t in proposed_title.split() if len(t) > 2]
            if base_tokens:
                recs_tokens = " ".join(base_tokens)
                recommendations.append(f"Alternative: Try combining '{recs_tokens}' with a distinct local region or niche descriptor.")

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
            "total_latency_ms": round(total_time_ms, 2)
        }

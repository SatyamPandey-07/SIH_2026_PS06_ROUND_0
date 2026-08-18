import re
import jellyfish
from rapidfuzz import fuzz, distance
from athena.data_loader import PRGIDataLoader

GENERIC_PUBLICATION_TERMS = {
    "CHRONICLE", "OBSERVER", "HORIZON", "DARPAN", "CHETNA", "MANTHAN", "SANKALP",
    "DEEPAK", "SANDESH", "VANI", "INSIGHT", "SENTINEL", "PRATIBHA", "PRAKASH", "KIRAN",
    "TIMES", "NEWS", "EXPRESS", "BULLETIN", "INDIA", "BHARAT", "GAZETTE", "POST",
    "DAILY", "WEEKLY", "FORTNIGHTLY", "MONTHLY", "DAINIK", "SAPTAHIK", "MASIK", "SAMAY",
    "REVIEW", "JOURNAL", "DIGEST", "FORUM", "SAMACHAR", "PATRIKA", "VOICE", "MIRROR",
    "LEDGER", "MONITOR", "DISPATCH", "HERALD", "TRIBUNE", "REPORT", "MAGAZINE", "RECORD",
    "PRABHAT", "SANDHYA", "SHODH", "PRAVAH", "TARANG", "JYOTI", "VIKAS", "SANGAM"
}

class Stage1PhoneticMatcher:
    def __init__(self, data_loader: PRGIDataLoader = None):
        self.loader = data_loader or PRGIDataLoader.get_instance()
        
    def _clean(self, text: str) -> str:
        if not text:
            return ""
        t = re.sub(r"[^\w\s]", " ", text.upper())
        return re.sub(r"\s+", " ", t).strip()

    def _ngram_similarity(self, s1: str, s2: str, n: int = 3) -> float:
        if len(s1) < n or len(s2) < n:
            return 1.0 if s1 == s2 else 0.0
        ng1 = {s1[i:i+n] for i in range(len(s1) - n + 1)}
        ng2 = {s2[i:i+n] for i in range(len(s2) - n + 1)}
        if not ng1 or not ng2:
            return 0.0
        return len(ng1 & ng2) / len(ng1 | ng2)

    def match(self, proposed_title: str, top_k: int = 10):
        clean_input = self._clean(proposed_title)
        if not clean_input:
            return {"flagged": False, "candidates": [], "max_score": 0.0}
            
        words = clean_input.split()
        
        # 1. Phonetic candidate generation
        candidate_indices = set()
        
        try:
            sx = jellyfish.soundex(clean_input)
            mp = jellyfish.metaphone(clean_input)
            ny = jellyfish.nysiis(clean_input)
            
            candidate_indices.update(self.loader.soundex_map.get(sx, []))
            candidate_indices.update(self.loader.metaphone_map.get(mp, []))
            candidate_indices.update(self.loader.nysiis_map.get(ny, []))
            
            for w in words:
                if len(w) > 2:
                    sx_w = jellyfish.soundex(w)
                    mp_w = jellyfish.metaphone(w)
                    candidate_indices.update(self.loader.soundex_map.get(sx_w, [])[:300])
                    candidate_indices.update(self.loader.metaphone_map.get(mp_w, [])[:300])
        except Exception:
            pass
            
        # If candidate pool is too small, check full database with rapid ratio
        if len(candidate_indices) < 50:
            first_char = clean_input[0] if clean_input else ""
            char_candidates = [
                i for i, t in enumerate(self.loader.titles)
                if t and t[0] == first_char
            ]
            candidate_indices.update(char_candidates[:500])

        candidates = []
        flagged = False
        
        w1 = set(words)
        core1 = {w for w in w1 if w not in GENERIC_PUBLICATION_TERMS}
        if not core1:
            core1 = set(w1)

        for idx in candidate_indices:
            row = self.loader.df.iloc[idx]
            db_title = row["clean_title"]
            if not db_title:
                continue
                
            w2 = set(db_title.split())
            core2 = {w for w in w2 if w not in GENERIC_PUBLICATION_TERMS}
            if not core2:
                core2 = set(w2)
                
            # Levenshtein distance
            lev_dist = distance.Levenshtein.distance(clean_input, db_title)
            
            # Jaro-Winkler similarity
            jw_sim = jellyfish.jaro_winkler_similarity(clean_input, db_title)
            
            # Soundex & Metaphone match
            try:
                soundex_match = (jellyfish.soundex(clean_input) == jellyfish.soundex(db_title))
                metaphone_match = (jellyfish.metaphone(clean_input) == jellyfish.metaphone(db_title))
            except Exception:
                soundex_match, metaphone_match = False, False
                
            ngram_sim = self._ngram_similarity(clean_input, db_title, n=3)
            
            fuzz_ratio = fuzz.ratio(clean_input, db_title) / 100.0
            token_sort_ratio = fuzz.token_sort_ratio(clean_input, db_title) / 100.0
            token_set_ratio = fuzz.token_set_ratio(clean_input, db_title) / 100.0

            token_jaccard = len(w1 & w2) / max(1, len(w1 | w2))
            core_overlap = core1 & core2
            
            # Check phonetic/spelling similarity between core words
            core_phonetic_overlap = False
            for w_a in core1:
                for w_b in core2:
                    lev_w = distance.Levenshtein.distance(w_a, w_b)
                    fz_w = fuzz.ratio(w_a, w_b)
                    sx_w_match = (jellyfish.soundex(w_a) == jellyfish.soundex(w_b))
                    mp_w_match = (jellyfish.metaphone(w_a) == jellyfish.metaphone(w_b))
                    
                    if (
                        w_a == w_b
                        or (mp_w_match and lev_w <= 2)
                        or (sx_w_match and mp_w_match and lev_w <= 3)
                        or lev_w <= 1
                        or fz_w >= 82.0
                    ):
                        core_phonetic_overlap = True
                        break
                if core_phonetic_overlap:
                    break

            len_ratio = min(len(clean_input), len(db_title)) / max(len(clean_input), len(db_title))

            # Multi-word scoring logic
            if len(words) >= 2 or len(w2) >= 2:
                if core_overlap or core_phonetic_overlap:
                    combined_score = max(
                        fuzz_ratio,
                        token_sort_ratio,
                        0.95 if (lev_dist <= 2 and abs(len(clean_input) - len(db_title)) <= 2) else 0.0,
                        0.90 if (soundex_match and metaphone_match) else 0.0,
                        0.88 if (core_phonetic_overlap and lev_dist <= 3) else 0.0
                    )
                else:
                    # No core word match (only shared generic word or zero overlap)
                    if token_jaccard > 0:
                        # Scaled by actual token jaccard overlap
                        combined_score = min(token_sort_ratio * token_jaccard, 0.25)
                    else:
                        # Completely distinct titles
                        combined_score = min(fuzz_ratio * 0.25, 0.15)
            else:
                # Single word titles
                combined_score = max(
                    fuzz_ratio,
                    jw_sim if len_ratio > 0.7 else fuzz_ratio,
                    0.95 if (lev_dist <= 1) else 0.0,
                    0.90 if (soundex_match and metaphone_match) else 0.0
                )

            # Flagging rules
            is_flagged = (
                (soundex_match or metaphone_match) and combined_score >= 0.80
            ) or (lev_dist < 3 and min(len(clean_input), len(db_title)) > 4 and (token_jaccard >= 0.5 or core_phonetic_overlap)) or (fuzz_ratio >= 0.85) or (token_sort_ratio >= 0.85 and (token_jaccard >= 0.5 or core_phonetic_overlap))
            
            if is_flagged:
                flagged = True
                
            candidates.append({
                "sn": int(row["sn"]),
                "matched_title": row["title"],
                "registration_number": row.get("registration_number", ""),
                "registration_date": row.get("registration_date", ""),
                "language": row.get("language", ""),
                "periodicity": row.get("periodicity", ""),
                "publisher": row.get("publisher", ""),
                "owner": row.get("owner", ""),
                "state": row.get("publication_state", ""),
                "district": row.get("publication_district", ""),
                "levenshtein_distance": int(lev_dist),
                "jaro_winkler": round(float(jw_sim), 4),
                "soundex_match": soundex_match,
                "metaphone_match": metaphone_match,
                "ngram_similarity": round(float(ngram_sim), 4),
                "fuzz_ratio": round(float(fuzz_ratio), 4),
                "stage1_score": round(float(combined_score), 4),
                "is_flagged": is_flagged
            })
            
        candidates.sort(key=lambda x: (x["is_flagged"], x["stage1_score"], -x["levenshtein_distance"]), reverse=True)
        top_candidates = candidates[:top_k]
        
        max_score = top_candidates[0]["stage1_score"] if top_candidates else 0.0
        
        return {
            "flagged": flagged,
            "max_score": max_score,
            "candidates": top_candidates,
            "total_candidates_evaluated": len(candidates)
        }

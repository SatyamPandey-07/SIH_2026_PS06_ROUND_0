import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from athena.data_loader import PRGIDataLoader

# Cross-lingual and semantic equivalence dictionary for Indian & English publication terms
SEMANTIC_SYNONYMS = {
    "DAILY": ["DAINIK", "ROZANA", "DINAKARI", "DINA", "PRATIDIN", "DIARIO"],
    "WEEKLY": ["SAPTAHIK", "VAARIK", "HAFTAVAR", "VARAPATHRIKA"],
    "MONTHLY": ["MASIK", "MAHINA", "MASIKA"],
    "NEWS": ["SAMACHAR", "KHABAR", "VRITTA", "VARTA", "SANDESH", "BATMI", "NEWSLETTER", "BULLETIN"],
    "TIMES": ["KAAL", "SAMAY", "YUG", "ERA", "CHRONICLE"],
    "INDIA": ["BHARAT", "HINDUSTAN", "HIND", "DESH", "DESHAM"],
    "NATIONAL": ["RASHTRIYA", "QAUMI", "DESHIYA", "BHARATIYA"],
    "MIRROR": ["DARPAN", "AINA", "PRATIBIMB"],
    "VOICE": ["AWAAZ", "VANI", "DHVANI", "SWARA", "KURAL"],
    "MORNING": ["PRABHAT", "SAVERA", "USHA", "MORNING", "BHOR", "SUBH"],
    "EXPRESS": ["DRUT", "GATI", "VEG", "MAIL"],
    "POST": ["PATRIKA", "DAK", "SANDESH", "VAARTHA"],
    "TRIBUNE": ["MANCH", "PEETH"],
    "HERALD": ["DOOT", "SANDESHI"],
    "LEADER": ["NETA", "AGRANI", "NAYAK"],
    "LIGHT": ["JYOTI", "PRAKASH", "DEEP", "ROSHNI", "KIRAN", "UJALA"],
    "PEOPLE": ["JAN", "LOK", "PRAJA", "JANTA", "AWAAM"],
    "WORLD": ["DUNIYA", "JAGAT", "VISHWA", "SANSAR"],
    "TRUTH": ["SATYA", "SACH", "HAQ"],
    "CRIME": ["APRADH", "GUNAH", "JURM"],
    "BUSINESS": ["VYAPAR", "KAROBAR", "UDYOG", "COMMERCE", "TRADE"],
    "SPORTS": ["KHEL", "KRIDA"],
}

# Inverted mapping
WORD_TO_CONCEPT = {}
for concept, synonyms in SEMANTIC_SYNONYMS.items():
    WORD_TO_CONCEPT[concept] = concept
    for syn in synonyms:
        WORD_TO_CONCEPT[syn] = concept

class Stage2SemanticMatcher:
    def __init__(self, data_loader: PRGIDataLoader = None):
        self.loader = data_loader or PRGIDataLoader.get_instance()
        self.vectorizer = None
        self.tfidf_matrix = None
        self._init_embeddings()

    def _normalize_semantics(self, text: str) -> str:
        if not text:
            return ""
        words = re.findall(r"\b[A-Za-z]+\b", text.upper())
        canonical_words = []
        for w in words:
            concept = WORD_TO_CONCEPT.get(w, w)
            canonical_words.append(concept)
        return " ".join(canonical_words)

    def _init_embeddings(self):
        print("[Stage2] Initializing Multilingual Semantic Vector Index...")
        # Prepare normalized canonical corpus
        corpus = [
            f"{t} {self._normalize_semantics(t)}"
            for t in self.loader.titles
        ]
        # Char-wb + word n-grams for rich subword and morphological representations
        self.vectorizer = TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(3, 5),
            min_df=1,
            max_features=50000,
            sublinear_tf=True
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(corpus)
        print(f"[Stage2] Vector index ready with {self.tfidf_matrix.shape[0]} titles.")

    def match(self, proposed_title: str, top_k: int = 10, threshold: float = 0.80):
        if not proposed_title.strip():
            return {"flagged": False, "max_score": 0.0, "candidates": []}

        norm_title = f"{proposed_title.upper()} {self._normalize_semantics(proposed_title)}"
        query_vec = self.vectorizer.transform([norm_title])
        
        # Fast sparse dot product (cosine similarity since TF-IDF is L2 normalized)
        sim_scores = (self.tfidf_matrix * query_vec.T).toarray().flatten()
        
        # Find top candidates
        top_indices = np.argpartition(sim_scores, -top_k)[-top_k:]
        top_indices = top_indices[np.argsort(-sim_scores[top_indices])]
        
        candidates = []
        flagged = False
        
        query_words = set(re.findall(r"\b\w+\b", proposed_title.upper()))
        
        for idx in top_indices:
            score = float(sim_scores[idx])
            if score < 0.30:
                continue
                
            row = self.loader.df.iloc[idx]
            db_words = set(re.findall(r"\b\w+\b", str(row["clean_title"])))
            
            # Word coverage penalty: calculate Jaccard word overlap and query coverage
            common_words = db_words & query_words
            union_words = db_words | query_words
            jaccard = len(common_words) / max(1, len(union_words))
            query_cov = len(common_words) / max(1, len(query_words))
            
            # If word sets are not identical, scale raw TF-IDF score by Jaccard and word coverage
            if jaccard < 1.0:
                coverage_factor = 0.35 + 0.65 * jaccard
                score = score * coverage_factor

            is_flagged = score >= threshold
            if is_flagged:
                flagged = True
                
            candidates.append({
                "sn": int(row["sn"]),
                "matched_title": row["title"],
                "registration_number": row.get("registration_number", ""),
                "language": row.get("language", ""),
                "periodicity": row.get("periodicity", ""),
                "publisher": row.get("publisher", ""),
                "owner": row.get("owner", ""),
                "state": row.get("publication_state", ""),
                "district": row.get("publication_district", ""),
                "semantic_similarity": round(score, 4),
                "is_flagged": is_flagged
            })
            
        max_score = candidates[0]["semantic_similarity"] if candidates else 0.0
        
        return {
            "flagged": flagged,
            "max_score": max_score,
            "candidates": candidates[:top_k]
        }

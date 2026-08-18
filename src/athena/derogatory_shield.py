import sqlite3
import re
import os
from typing import List, Dict, Any, Tuple
import phonetics

LEET_MAP = {
    '0': 'o', '1': 'i', '3': 'e', '4': 'a', '5': 's',
    '7': 't', '8': 'b', '@': 'a', '$': 's', '!': 'i',
    '+': 't', 'v': 'u'
}

DEFAULT_SEED_TERMS = [
    # English offensive / derogatory terms
    "hate", "racist", "terror", "terrorist", "nazi", "slur", "scam",
    "fraud", "kill", "murder", "blast", "violence", "porn", "xxx",
    "adult", "sex", "cheat", "bastard", "idiot", "scoundrel", "fake",
    # Hindi / Hinglish derogatory terms
    "gunda", "chor", "chori", "fraudster", "kamina", "harami", "kutte",
    "bhadwa", "dalal", "mafia", "terrorist", "bakwas", "jhootha",
    "feku", "dacoit", "goonda", "dhamaka", "hatya"
]


def normalize_leetspeak(text: str) -> str:
    cleaned = text.lower()
    for leet_char, real_char in LEET_MAP.items():
        cleaned = cleaned.replace(leet_char, real_char)
    # Remove special punctuation
    cleaned = re.sub(r'[^a-zA-Z\s]', '', cleaned)
    return cleaned.strip()


def levenshtein_distance(s1: str, s2: str) -> int:
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]


class DerogatoryShield:
    _instance = None

    def __init__(self, db_path: str = "derogatory_seeds.db"):
        self.db_path = db_path
        self._init_db()
        self.reload_seeds()

    @classmethod
    def get_instance(cls, db_path: str = "derogatory_seeds.db"):
        if cls._instance is None:
            cls._instance = DerogatoryShield(db_path)
        return cls._instance

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS seed_terms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                term TEXT UNIQUE NOT NULL,
                category TEXT DEFAULT 'DEROGATORY',
                source TEXT DEFAULT 'SYSTEM',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Insert defaults if table is empty
        cursor.execute("SELECT COUNT(*) FROM seed_terms")
        if cursor.fetchone()[0] == 0:
            for term in DEFAULT_SEED_TERMS:
                cursor.execute("INSERT OR IGNORE INTO seed_terms (term, source) VALUES (?, 'SEED')", (term.lower(),))
            conn.commit()
        conn.close()

    def reload_seeds(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT term FROM seed_terms")
        rows = cursor.fetchall()
        conn.close()
        self.seed_terms = set(r[0].lower() for r in rows)
        # Precompute phonetic representations
        self.phonetic_seeds = {}
        for t in self.seed_terms:
            try:
                sndx = phonetics.soundex(t)
                metap = phonetics.dmetaphone(t)[0]
                self.phonetic_seeds[t] = (sndx, metap)
            except Exception:
                pass

    def add_seed_term(self, term: str, source: str = "COMMUNITY_FLAG") -> bool:
        clean_term = normalize_leetspeak(term).lower()
        if not clean_term:
            return False
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT OR IGNORE INTO seed_terms (term, source) VALUES (?, ?)", (clean_term, source))
            conn.commit()
            success = cursor.rowcount > 0
        finally:
            conn.close()
        self.reload_seeds()
        return success

    def check_title(self, title: str) -> Dict[str, Any]:
        normalized = normalize_leetspeak(title)
        words = [w for w in normalized.split() if len(w) > 2]

        flagged_tokens = []
        max_confidence = 0.0

        for word in words:
            # 1. Direct exact match check
            if word in self.seed_terms:
                flagged_tokens.append({"word": word, "match_type": "EXACT", "confidence": 1.0})
                max_confidence = max(max_confidence, 1.0)
                continue

            # Compute word phonetics
            try:
                w_sndx = phonetics.soundex(word)
                w_meta = phonetics.dmetaphone(word)[0]
            except Exception:
                w_sndx, w_meta = "", ""

            for seed, (s_sndx, s_meta) in self.phonetic_seeds.items():
                # Substring containment check
                if seed in word or word in seed:
                    confidence = 0.85 if len(seed) >= 4 else 0.70
                    flagged_tokens.append({"word": word, "seed_match": seed, "match_type": "SUBSTRING", "confidence": confidence})
                    max_confidence = max(max_confidence, confidence)
                    break

                # Edit distance check
                dist = levenshtein_distance(word, seed)
                max_len = max(len(word), len(seed))
                sim = 1.0 - (dist / max_len)

                if sim >= 0.75:
                    flagged_tokens.append({"word": word, "seed_match": seed, "match_type": "FUZZY_EDIT", "confidence": round(sim, 2)})
                    max_confidence = max(max_confidence, round(sim, 2))
                    break

                # Phonetic soundex / metaphone match
                if (w_sndx and w_sndx == s_sndx) or (w_meta and w_meta == s_meta):
                    flagged_tokens.append({"word": word, "seed_match": seed, "match_type": "PHONETIC", "confidence": 0.75})
                    max_confidence = max(max_confidence, 0.75)
                    break

        status = "PASSED"
        if max_confidence >= 0.70:
            status = "REJECTED"
        elif max_confidence >= 0.40:
            status = "UNDER_REVIEW"

        return {
            "status": status,
            "confidence_score": round(max_confidence, 2),
            "flagged": max_confidence >= 0.40,
            "flagged_tokens": flagged_tokens,
            "details": f"Stage 0 Shield evaluated {len(words)} tokens against {len(self.seed_terms)} seed patterns."
        }

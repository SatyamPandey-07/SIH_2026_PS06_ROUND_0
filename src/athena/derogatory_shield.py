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
    # --- English Explicit, Profane, and Vulgar Terms ---
    "fuck", "fucking", "fucker", "shit", "shitting", "shitty", "bitch", "bitches",
    "cunt", "cunts", "asshole", "assholes", "bastard", "bastards", "dick", "dicks",
    "pussy", "pussies", "cock", "cocks", "prick", "pricks", "twat", "motherfucker",
    "motherfucking", "bullshit", "horseshit", "dipshit", "dumbass", "jackass",
    "slut", "whore", "slutty", "wanker", "bugger", "bollocks", "arse", "arsehole",

    # --- English Hate, Violence, Crime & Extremism ---
    "hate", "racist", "racism", "terror", "terrorist", "terrorism", "nazi", "fascist",
    "slur", "scam", "scammer", "fraud", "fraudster", "kill", "killer", "murder",
    "murderer", "blast", "violence", "porn", "porno", "pornography", "xxx",
    "adult", "sex", "cheat", "cheater", "idiot", "scoundrel", "fake", "corrupt",
    "extortion", "blackmail", "smuggling", "contraband",

    # --- Hindi / Hinglish Profane & Derogatory Terms ---
    "chutiya", "chutiyapa", "gandu", "gand", "bhosdike", "bhosdi", "bhosda",
    "madarchod", "behenchod", "bhenchod", "mc", "bc", "bhadwa", "bhadwe",
    "dalal", "harami", "haramzada", "kamina", "kamine", "kutte", "kutta",
    "kuttiya", "saala", "saale", "raand", "randi", "chut", "gaand",
    "lauda", "loda", "lund", "tatte", "tatty", "jhant", "jhaant",

    # --- Hindi / Hinglish Crime, Threat & Misconduct Terms ---
    "gunda", "goonda", "gundagardi", "chor", "chori", "dacoit", "dakait",
    "mafia", "bakwas", "jhootha", "feku", "dhamaka", "hatya", "kattar",
    "aatankwadi", "aatank", "visphot", "aag", "hinsa", "danga", "rioter",
    "looter", "loot", "thug", "fraudster"
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
        words = [w for w in normalized.split() if len(w) >= 2]

        flagged_tokens = []
        max_confidence = 0.0

        for word in words:
            # 1. Direct exact match check
            if word in self.seed_terms:
                flagged_tokens.append({"word": word, "match_type": "EXACT", "confidence": 1.0})
                max_confidence = max(max_confidence, 1.0)
                continue

            # 2. Substring containment check (only for long specific derogatory roots of len >= 5)
            for seed in self.seed_terms:
                if len(seed) >= 5 and (seed in word or (len(word) >= 5 and word in seed)):
                    confidence = 0.85
                    flagged_tokens.append({"word": word, "seed_match": seed, "match_type": "SUBSTRING", "confidence": confidence})
                    max_confidence = max(max_confidence, confidence)
                    break

                # 3. High edit distance similarity (only for seeds of len >= 5 with dist <= 1)
                if len(seed) >= 5 and len(word) >= 5:
                    dist = levenshtein_distance(word, seed)
                    if dist <= 1:
                        sim = 1.0 - (dist / max(len(word), len(seed)))
                        flagged_tokens.append({"word": word, "seed_match": seed, "match_type": "FUZZY_EDIT", "confidence": round(sim, 2)})
                        max_confidence = max(max_confidence, round(sim, 2))
                        break

        status = "PASSED"
        if max_confidence >= 0.75:
            status = "REJECTED"
        elif max_confidence >= 0.50:
            status = "UNDER_REVIEW"

        return {
            "status": status,
            "confidence_score": round(max_confidence, 2),
            "flagged": max_confidence >= 0.40,
            "flagged_tokens": flagged_tokens,
            "details": f"Stage 0 Shield evaluated {len(words)} tokens against {len(self.seed_terms)} seed patterns."
        }

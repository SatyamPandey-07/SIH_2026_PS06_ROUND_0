import os
import re
import pandas as pd
import jellyfish

class PRGIDataLoader:
    _instance = None
    
    def __init__(self, csv_path: str = "prgi_titles.csv"):
        self.csv_path = csv_path
        if not os.path.exists(self.csv_path):
            # Check data/ subdirectory
            alt_path = os.path.join("data", "prgi_titles.csv")
            if os.path.exists(alt_path):
                self.csv_path = alt_path
                
        self.df = None
        self.titles = []
        self.soundex_map = {}
        self.metaphone_map = {}
        self.nysiis_map = {}
        self._load_data()
        
    @classmethod
    def get_instance(cls, csv_path: str = "prgi_titles.csv"):
        if cls._instance is None:
            cls._instance = cls(csv_path)
        return cls._instance

    def _clean_title(self, title: str) -> str:
        if not isinstance(title, str):
            return ""
        # Uppercase and remove excessive spaces and special symbols
        t = re.sub(r"[^\w\s]", " ", title.upper())
        return re.sub(r"\s+", " ", t).strip()

    def _load_data(self):
        if not os.path.exists(self.csv_path):
            raise FileNotFoundError(f"PRGI dataset not found at {self.csv_path}")
            
        print(f"[DataLoader] Loading PRGI dataset from {self.csv_path}...")
        self.df = pd.read_csv(self.csv_path, low_memory=False)
        self.df["title"] = self.df["title"].fillna("").astype(str)
        self.df["clean_title"] = self.df["title"].apply(self._clean_title)
        
        # Build fast phonetic index
        print("[DataLoader] Indexing phonetic keys...")
        for idx, row in self.df.iterrows():
            clean = row["clean_title"]
            if not clean:
                continue
                
            # Soundex & Metaphone for full title and individual words
            try:
                sx = jellyfish.soundex(clean)
                mp = jellyfish.metaphone(clean)
                ny = jellyfish.nysiis(clean)
                if sx:
                    self.soundex_map.setdefault(sx, []).append(idx)
                if mp:
                    self.metaphone_map.setdefault(mp, []).append(idx)
                if ny:
                    self.nysiis_map.setdefault(ny, []).append(idx)
            except Exception:
                pass
                
            words = clean.split()
            for w in words:
                if len(w) > 2:
                    try:
                        sx_w = jellyfish.soundex(w)
                        mp_w = jellyfish.metaphone(w)
                        self.soundex_map.setdefault(sx_w, []).append(idx)
                        self.metaphone_map.setdefault(mp_w, []).append(idx)
                    except Exception:
                        pass
                    
        self.titles = self.df["clean_title"].tolist()
        print(f"[DataLoader] Successfully loaded {len(self.df)} registered titles.")

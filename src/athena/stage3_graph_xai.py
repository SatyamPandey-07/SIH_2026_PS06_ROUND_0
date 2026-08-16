import re
import networkx as nx
from collections import Counter
from athena.data_loader import PRGIDataLoader

class Stage3GraphAndXAI:
    def __init__(self, data_loader: PRGIDataLoader = None):
        self.loader = data_loader or PRGIDataLoader.get_instance()
        self.word_freq = Counter()
        self.title_graph = nx.Graph()
        self._build_word_index()

    def _build_word_index(self):
        print("[Stage3] Indexing word frequencies and entity co-occurrence...")
        for title in self.loader.titles:
            words = title.split()
            for w in words:
                if len(w) > 1:
                    self.word_freq[w] += 1
        print(f"[Stage3] Indexed {len(self.word_freq)} distinct lexical entities.")

    def explain_title(self, proposed_title: str, matched_titles: list) -> dict:
        """
        Computes SHAP/LIME-style token importance weights and attention scores.
        Identifies which specific words or tokens in the proposed title contribute
        most to the similarity flags or uniqueness.
        """
        tokens = re.findall(r"\b\w+\b", proposed_title.upper())
        if not tokens:
            return {"token_importance": {}, "attention_weights": {}, "influential_words": []}

        # Matched corpus words
        matched_words = []
        for m in matched_titles:
            m_title = m.get("matched_title") or m.get("title") or ""
            matched_words.extend(re.findall(r"\b\w+\b", str(m_title).upper()))
            
        matched_counts = Counter(matched_words)
        total_matched = max(1, sum(matched_counts.values()))
        
        token_importance = {}
        attention_weights = {}
        
        for token in tokens:
            # Frequency in matched titles vs global corpus rarity (TF-IDF / SHAP style)
            match_frequency = matched_counts.get(token, 0)
            global_freq = self.word_freq.get(token, 1)
            
            # Inverse document rarity multiplier
            rarity_score = 1.0 / (1.0 + (global_freq / 500.0))
            
            # If word appears in matched duplicates, high collision risk weight
            if match_frequency > 0:
                importance = (match_frequency / total_matched) * 1.5 + (0.5 * rarity_score)
            else:
                importance = 0.05 * rarity_score
                
            token_importance[token] = round(float(importance), 4)

        # Normalize attention weights to sum to 1.0 (softmax style)
        raw_vals = [token_importance[t] for t in tokens]
        total_val = sum(raw_vals) or 1.0
        for t in tokens:
            attention_weights[t] = round(token_importance[t] / total_val, 4)

        # Ranked influential words
        influential_words = sorted(
            [{"word": t, "importance": token_importance[t], "attention": attention_weights[t]} for t in tokens],
            key=lambda x: x["importance"],
            reverse=True
        )

        return {
            "token_importance": token_importance,
            "attention_weights": attention_weights,
            "influential_words": influential_words
        }

    def build_subgraph_for_candidates(self, proposed_title: str, candidates: list) -> dict:
        """
        Constructs an entity and co-registration graph for the proposed title and its top matches.
        Nodes: Titles, Owners, States, Periodicity.
        Edges: Co-registration relationships.
        """
        G = nx.Graph()
        G.add_node(proposed_title, type="proposed_title", label=proposed_title)

        for c in candidates[:6]:
            t_name = c.get("matched_title") or c.get("title") or "Title"
            owner = c.get("owner")
            state = c.get("state") or c.get("publication_state")
            periodicity = c.get("periodicity")

            G.add_node(t_name, type="registered_title", label=t_name, score=c.get("stage1_score", 0.0))
            G.add_edge(proposed_title, t_name, relation="similar_to")

            if owner and str(owner).strip() and str(owner).upper() != "NAN":
                o_name = f"Owner: {str(owner).title()[:25]}"
                G.add_node(o_name, type="owner", label=o_name)
                G.add_edge(t_name, o_name, relation="owned_by")

            if state and str(state).strip() and str(state).upper() != "NAN":
                s_name = f"State: {str(state)}"
                G.add_node(s_name, type="state", label=s_name)
                G.add_edge(t_name, s_name, relation="published_in")

        nodes = [{"id": n, "label": G.nodes[n].get("label", n), "type": G.nodes[n].get("type", "node")} for n in G.nodes()]
        edges = [{"source": u, "target": v, "relation": G.edges[u, v].get("relation", "")} for u, v in G.edges()]

        return {"nodes": nodes, "edges": edges, "node_count": len(nodes), "edge_count": len(edges)}

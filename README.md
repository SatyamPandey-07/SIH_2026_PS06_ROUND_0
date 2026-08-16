# Overview

The Press Registrar General of India (PRGI) maintains a database of ~160,000 registered newspaper and periodical titles. When publishers submit new titles for verification, the system must ensure uniqueness while enforcing strict compliance guidelines. Athena automates this process through a three-stage verification pipeline:

    - Stage 1 (Fast): Phonetic & fuzzy matching (Soundex, Metaphone, Levenshtein)

    - Stage 2 (Accurate): Transformer-based semantic similarity (RoBERTa Multilingual, XLM-R)

    - Stage 3 (Advanced): Graph neural networks (GLORY) + explainable AI (SHAP, LIME)

The MVP is a Streamlit-based web application that provides real-time title verification with probability scores, detailed feedback, and actionable recommendations for improvement.

---

## Stage 1: Phonetic & Fuzzy Matching (Baseline)

**Purpose**: Fast filtering to eliminate obvious duplicates (<100ms per query)

**Algorithms**:

    Soundex: Encodes titles into 4-character phonetic representations

    Metaphone: Improved phonetic encoding for English spelling variations

    Double Metaphone: Handles multiple pronunciations

    Levenshtein Distance: Edit distance for spelling variations

    Jaro-Winkler Similarity: Better for short strings (titles)

    N-gram Overlap: 2-3 character and word-level n-grams

**Thresholds**:

    Phonetic match: >85% similarity → Flag for review

    Levenshtein: <3 edit distance → Flag for review

    Jaro-Winkler: >0.85 → Flag for review

**Output**: List of candidate titles with similarity scores

---

## Stage 2: Transformer-Based Semantic Similarity

**Purpose**: Detect semantically similar titles across languages and contexts

**Models**:

    RoBERTa Multilingual (roberta-base): Strong baseline for English + 100+ languages

    XLM-RoBERTa Base (xlm-roberta-base): Better for low-resource Indian languages

    IndicBERT (ai4bharat/indic-bert): Optimized for 12 Indian languages

    Sentence Transformers (paraphrase-multilingual-mpnet-base-v2): Pre-trained for semantic similarity

**Process**:

    Generate embeddings for input title and all 160K existing titles (pre-computed)

    Use FAISS for sub-millisecond similarity search

    Calculate cosine similarity scores

    Apply threshold (0.80 = 80% similarity)

**Output**: Ranked list of semantically similar titles with confidence scores

---

## Stage 3: Graph Neural Networks + Explainable AI

**Purpose**: Detect structural patterns, thematic clusters, and provide explanations

**GLORY Architecture**:

    Global Title Graph: Nodes = titles, Edges = co-registration patterns

    Global Entity Graph: Nodes = entities (people, places, orgs), Edges = co-occurrence

    Gated Graph Neural Network (GGNN): Encodes graph structure

    Multi-Head Attention: Combines local + global representations

**Explainable AI (xAI)**:

    SHAP (SHapley Additive exPlanations):

        Global feature importance across all predictions

        Shows which words/entities drive similarity scores

    LIME (Local Interpretable Model-agnostic Explanations):

        Local explanations for individual predictions

        Highlights specific title components causing flags

    Attention Visualization:

        Transformer attention weights showing word-level importance

        Visual heatmaps for user-friendly explanations

**Output**:

    Final verification probability score

    Detailed explanation of rejection reasons

    Visualizations showing influential words/entities



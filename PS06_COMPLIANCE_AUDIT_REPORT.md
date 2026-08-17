# SIH 2026 Problem Statement PS06: Comprehensive System Compliance Audit

## Project Title
**Athena: Automated PRGI Title Verification & Guideline Enforcement System**
**Problem Statement ID**: PS06  
**Target Organization**: Press Registrar General of India (PRGI)

---

## Executive Summary & Audit Overview

A comprehensive compliance evaluation of the **Athena Title Verification Pipeline** was executed against all functional requirements and expected solutions outlined in **SIH 2026 Problem Statement PS06**.

As per evaluation instructions, **no codebase modifications were made during this audit phase**. The system was evaluated in its current operational state across a test suite covering phonetic matching, prefix/suffix handling, statutory guideline enforcement, cross-lingual translation equivalence, verification probability scaling, application tracking, and user feedback interfaces.

### Overall Qualification Summary
- **Fully Qualified Requirements**: 1b, 1c, 1d, 2a, 2b, 3a, 3b, 3d, 3e, 5a, 5c, 6a, 6b, 6c, 7a, 7b
- **Partially Qualified / Gaps Identified**: 1a, 3c, 4 (Expected Solution a), 5b (Expected Solution c)

---

## Detailed Requirement-by-Requirement Audit

### 1. Similarity Check

| Sub-Requirement | Status | Audit Findings & Benchmark Behavior |
| :--- | :--- | :--- |
| **1a. Phonetic Similarity Algorithms** *(Soundex, Metaphone)* | ⚠️ **Partial** | Stage 1 indexes titles using Soundex, Metaphone, and NYSIIS. However, for `"Namaskar"` vs `"Namascar"`, Soundex generates `N522` vs `N526`. Because core word sets were treated as disjoint, similarity was capped at **55.0% (APPROVED)** instead of being flagged as a close phonetic spelling match. |
| **1b. Common Prefix / Suffix Identification** | ✅ **Qualified** | Detects and evaluates common publication prefixes/suffixes (`The`, `India`, `Samachar`, `News`, `Today`, `Daily`) via `rules_engine.py` and `stage1_phonetic.py`. |
| **1c. Spelling Variations & Slight Modifications** | ✅ **Qualified** | RapidFuzz token ratios and Levenshtein distance successfully flag spelling tweaks. Test case `'Prabhat Khabbar'` vs `'PRABHAT KHABAR'` scored **96.5% similarity** and was **REJECTED (19.5% prob)**. |
| **1d. Similarity Percentage Calculation** | ✅ **Qualified** | Returns explicit percentage scores for Stage 1 (`stage1_score`), Stage 2 (`semantic_similarity`), and overall pipeline (`highest_similarity` & `final_similarity_score`). |

---

### 2. Prefix / Suffix Handling

| Sub-Requirement | Status | Audit Findings & Benchmark Behavior |
| :--- | :--- | :--- |
| **2a. Disallowed Prefixes / Suffixes List** | ✅ **Qualified** | System maintains lists of disallowed periodicity and generic prefix/suffix terms in `PERIODICITY_TERMS` and `GENERIC_DISALLOWED_PREFIX_SUFFIX`. |
| **2b. Reject Titles with Disallowed Prefixes / Suffixes causing close resemblance** | ✅ **Qualified** | Rejects submission when adding prefixes/suffixes causes close resemblance to existing titles. Test case `'Hindustan Today'` vs `'HINDUSTAN'` scored **100.0% similarity** and was **REJECTED (10.0% prob)**. |

---

### 3. Guideline Enforcement

| Sub-Requirement | Status | Audit Findings & Benchmark Behavior |
| :--- | :--- | :--- |
| **3a. Disallowed Words List** *(Police, Crime, Corruption, CBI, CID, Army, etc.)* | ✅ **Qualified** | Maintained in `EMBLEM_RESTRICTED_WORDS` in `rules_engine.py` under the Emblems & Names Act ruleset. |
| **3b. Rejection of Titles Containing Disallowed Words** | ✅ **Qualified** | Titles containing prohibited statutory terms trigger CRITICAL violations (+75 penalty points). Test case `'CBI Crime Investigation'` was **REJECTED (0.0% prob)**. |
| **3c. Prevention of Combined Existing Titles** | ⚠️ **Partial** | Test case `'Hindu Indian Express'` (combining `"Hindu"` and `"Indian Express"`) matched `"INDIAN EXPRESS"` at 82.3% similarity and received **UNDER_REVIEW (58.5% prob)**. However, there is no explicit multi-title decomposition rule checking if an input is formed by combining two distinct registered titles. |
| **3d. Cross-Lingual Similar Meanings in Other Languages** | ✅ **Qualified** | Stage 2 utilizes a cross-lingual `SEMANTIC_SYNONYMS` dictionary (mapping `DAILY` $\leftrightarrow$ `PRATIDIN`, `EVENING` $\leftrightarrow$ `SANDHYA`). Test case `'Pratidin Sandhya'` matched `'DAILY EVENING'` with high semantic score and was **REJECTED (0.0% prob)**. |
| **3e. Disallow Periodicity Additions to Existing Titles** | ✅ **Qualified** | Evaluated in `rules_engine.py`. Strips periodicity terms to detect core title collisions. Test case `'Dainik Jagran'` triggered `Periodicity Prefix/Suffix Disallowance` and was **REJECTED (0.0% prob)**. |

---

### 4. Verification Probability & Expected Solution (a)

| Requirement / Constraint | Status | Audit Findings & Gap Analysis |
| :--- | :--- | :--- |
| **Probability Score Display** | ✅ **Qualified** | Displays numerical probability score (0.0% to 100.0%) and radial Plotly gauge in UI. |
| **Expected Solution (a) Constraint**:  <br>$\text{Probability} \le (100 - \text{Similarity})\%$ | ❌ **Gap Identified** | Expected Solution (a) explicitly states: *"If a title has a similarity score of 80%, the verification probability shall not be more than 100% - 80% = 20%."* <br>Currently, when $S = 80\%$, the penalty curve sets `uniqueness_penalty` = 35.0%, resulting in **Acceptance Probability = 65.0%** (exceeding the required 20% ceiling). |

---

### 5. Database Interaction & Application Tracking

| Sub-Requirement | Status | Audit Findings & Gap Analysis |
| :--- | :--- | :--- |
| **5a. Efficient Search Across Database** | ✅ **Qualified** | `PRGIDataLoader` loads and queries 82,730 registered PRGI titles with sub-second response times (<150ms average search latency). |
| **5b. Application Tracking & Future Reference** *(Expected Solution c)* | ❌ **Gap Identified** | The system currently queries a static CSV dataset (`prgi_titles.csv`). Newly verified/approved applications submitted by users are **not dynamically stored or tracked in a persistent submission queue** to block subsequent duplicate submissions submitted later by other users. |
| **5c. Indexing & Optimization** | ✅ **Qualified** | Uses Soundex/Metaphone hash tables in Stage 1 and TF-IDF sparse matrix dot products in Stage 2 for fast sub-millisecond retrieval. |

---

### 6. User Feedback & 7. Scalability

| Sub-Requirement | Status | Audit Findings |
| :--- | :--- | :--- |
| **6a. Clear Violation Feedback** | ✅ **Qualified** | Provides detailed breakdown of statutory violations, high-risk token heatmaps, top matched titles, and official certificates. |
| **6b. Display Verification Probability** | ✅ **Qualified** | Rendered via radial gauge and official status badge (`APPROVED`, `UNDER_REVIEW`, `REJECTED`). |
| **6c. Title Modification & Resubmission** | ✅ **Qualified** | Streamlit UI allows real-time edits and generates 4 pre-verified smart alternatives. |
| **7a/b. System Scalability & Performance** | ✅ **Qualified** | Memory-efficient sparse matrix vectorization and candidate generation scale well with dataset growth. |

---

## Summary of Actionable Gaps to Address in Future Iterations

1. **Enforce Strict Probability Ceiling**: Update `acceptance_probability` formula to cap probability at $\min(\text{Current Prob}, 100 - \text{Similarity Score})$.
2. **Implement Dynamic Application Tracker**: Add a persistent sqlite/session database store to log newly approved titles so subsequent user submissions are checked against live applications.
3. **Add Explicit Combined Title Decomposition Rule**: Check if input title $T$ can be split into $T_1 + T_2$ where both $T_1$ and $T_2$ exist as registered titles in the PRGI database.
4. **Tune Phonetic Equivalence for Spelling Variants**: Adjust soundex/metaphone fallback so spelling variants like `Namaskar` vs `Namascar` trigger phonetic similarity flags.

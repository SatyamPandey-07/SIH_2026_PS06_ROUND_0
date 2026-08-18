# Athena: Setup & Execution Guide (RUN.md)

Welcome! This guide explains how to quickly clone, set up, and run **Athena: The PRGI AI Title Verification & Guideline Enforcement System** on any machine (Windows / macOS / Linux).

---

## 1. Prerequisites

- **Python**: Version `3.10`, `3.11`, or `3.12`
- **Package Manager**: [uv](https://docs.astral.sh/uv/) *(Recommended for 10x faster setup)* or standard `pip` / `venv`
- **Git**: Installed on your system

---

## 2. Quick Setup

### Method A: Using `uv` (Fastest & Recommended)

If you don't have `uv` installed, install it in seconds:
- **Windows (PowerShell)**:
  ```powershell
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```
- **macOS / Linux**:
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

Then run:
```bash
# 1. Clone the repository
git clone https://github.com/SatyamPandey-07/SIH_2026_PS06.git
cd SIH_2026_PS06

# 2. Sync all dependencies automatically
uv sync
```

---

### Method B: Using Standard `pip` and `venv`

```bash
# 1. Clone the repository
git clone https://github.com/SatyamPandey-07/SIH_2026_PS06.git
cd SIH_2026_PS06

# 2. Create and activate a virtual environment
# On Windows:
python -m venv .venv
.venv\Scripts\activate

# On macOS / Linux:
python3 -m venv .venv
source .venv/bin/activate

# 3. Install required packages
pip install streamlit rapidfuzz jellyfish scikit-learn networkx plotly pandas pymupdf
```

---

## 3. How to Run the Application

### A. Launch the Interactive Web Dashboard (UI)

Run the Streamlit application with:

```bash
# Using uv:
uv run streamlit run src/athena/app.py

# Or using standard python virtual environment:
streamlit run src/athena/app.py
```

Open your browser at **`http://localhost:8501`**.

---

### B. Run Title Verification via Command Line (CLI)

You can verify any proposed title directly from your terminal:

```bash
# Example 1: Verify a Hindi daily newspaper in Uttar Pradesh
uv run athena "Dainik Bharat Samachar" --language Hindi --state "Uttar Pradesh" --periodicity Daily

# Example 2: Verify an English title
uv run athena "Police Crime Branch Times" --language English --state Delhi
```

---

## 4. Platform Features & How to Demo

The web platform provides a dual-role workflow:

### Role 1: Publisher / Applicant Portal
1. **Live Title Verification**:
   - Test proposed titles with real-time 3-stage AI similarity checks.
   - Use the **1-Click Live Demo Presets** at the top of the tab for instant test scenarios:
     - `1. Direct Collision`: Exact duplicate detection (`A &S INDIA`).
     - `2. Deceptive Phonetic`: Phonetic variant detection (`Dainik Khabbar` vs `Khabar`).
     - `3. Combined Titles Violation`: Multi-title combination detection (`Hindu Indian Express`).
     - `4. Emblems Act Infringement`: Prohibited words detection (`Police Crime Branch Times`).
     - `5. Compliant Novel Title`: Distinctive title passing verification (`Vindhya Innovation Chronicle`).
   - View the **Radial Score Gauge**, **Stage Waterfall**, **Physics Network Graph**, **xAI Token Heatmaps**, and **Smart AI Title Alternatives**.
2. **Submit Formal Application**:
   - Fill in applicant details $\rightarrow$ Submits dossier and logs into the persistent registry (`data/applications.db`).
   - Generates a unique **Application ID** (e.g. `PRGI-2026-A0001`).
3. **Track Application Status**:
   - Enter your Application ID to track live status (`Submitted`, `Pending Review`, `Approved`, `Rejected`).
   - Download the official **PRGI Title Verification Certificate (HTML)**.
4. **Batch CSV Audit**:
   - Upload any CSV containing a `title` column to audit hundreds of titles simultaneously with visual approval donut charts.

---

### Role 2: PRGI Official & Registrar Admin Portal
1. **Registrar Application Queue**:
   - Review pending submissions in the queue with live counters.
2. **AI Audit Dossier**:
   - Inspect full automated AI audit findings, similarity scores, and nearest registered duplicates.
3. **Official Registrar Action Panel**:
   - Issue determinations: `APPROVE TITLE REGISTRATION`, `REJECT APPLICATION`, or `REQUEST TITLE MODIFICATION`.
   - Add official remarks and persist the status update in the registry.
4. **National PRGI Database Analytics**:
   - Visual statistical breakdown across all 82,730 officially registered publications in India (languages, periodicity, states, top keywords).

---

## 5. Project Directory Structure

```text
SIH_2026_PS06/
├── data/
│   ├── prgi_titles.csv         # Extracted dataset of 82,730 registered PRGI titles
│   └── applications.db         # Persistent SQLite store for tracking submitted applications
├── src/
│   └── athena/
│       ├── __init__.py         # Package exports
│       ├── app.py              # Streamlit Web Application (Publisher & Admin portals)
│       ├── app_tracker.py      # SQLite Application Tracker & future reference engine
│       ├── certificate.py      # Official PRGI Compliance Audit Certificate generator
│       ├── cli.py              # CLI verification interface
│       ├── data_loader.py      # In-memory dataset loader & phonetic indexer
│       ├── pipeline.py         # Master 3-Stage verification orchestrator
│       ├── rules_engine.py     # PRGI Statutory & Emblems Act compliance engine
│       ├── stage1_phonetic.py  # Stage 1: Phonetic & Fuzzy Matching
│       ├── stage2_semantic.py  # Stage 2: Multilingual Vector Semantic Similarity
│       └── stage3_graph_xai.py # Stage 3: Graph Relationships & Explainable AI (SHAP/LIME)
├── convert_pdf_to_csv.py       # Parallel PDF to CSV extraction script (PyMuPDF)
├── PS06_COMPLIANCE_AUDIT_REPORT.md # Comprehensive PS06 compliance audit report
├── pyproject.toml              # Project dependencies & packaging config
├── README.md                   # Project overview & technical specifications
└── RUN.md                      # Setup and execution instructions
```

---

## 6. Troubleshooting & FAQs

- **Q: Where is the dataset loaded from?**  
  *A:* The data loader automatically looks for [`data/prgi_titles.csv`](file:///d:/SIH_2026_PS06/data/prgi_titles.csv) or [`prgi_titles.csv`](file:///d:/SIH_2026_PS06/prgi_titles.csv) in the root directory.

- **Q: How does the system handle future duplicate submissions?**  
  *A:* All submitted applications are logged into [`data/applications.db`](file:///d:/SIH_2026_PS06/data/applications.db). When a new title is checked, the pipeline inspects both the 82,730 registered titles AND active applications to prevent collision with previously submitted applications.

- **Q: Port 8501 is already in use?**  
  *A:* Run Streamlit on a different port:
  ```bash
  uv run streamlit run src/athena/app.py --server.port 8502
  ```

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import time
import os

from athena.data_loader import PRGIDataLoader
from athena.pipeline import AthenaVerificationPipeline

# Page configuration - Sidebar removed completely
st.set_page_config(
    page_title="Athena | PRGI AI Title Verification System",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom Styling (Minimal emojis, sleek dark/light modern typography, sidebar hidden)
st.markdown("""
<style>
    /* Hide sidebar completely */
    [data-testid="stSidebar"] {
        display: none !important;
    }
    [data-testid="collapsedControl"] {
        display: none !important;
    }
    
    .app-title {
        font-size: 2.2rem;
        font-weight: 700;
        letter-spacing: -0.5px;
        color: #1E88E5;
        margin-bottom: 0.2rem;
    }
    .app-subtitle {
        color: #8c9ba5;
        font-size: 1.0rem;
        margin-bottom: 1.2rem;
    }
    .stat-chip {
        display: inline-block;
        background-color: rgba(30, 136, 229, 0.12);
        color: #1E88E5;
        border: 1px solid rgba(30, 136, 229, 0.3);
        border-radius: 6px;
        padding: 4px 10px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-right: 8px;
    }
    .status-badge-approved {
        background-color: #1b5e20;
        color: #ffffff;
        padding: 6px 18px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 1.05rem;
        display: inline-block;
        letter-spacing: 0.5px;
    }
    .status-badge-review {
        background-color: #e65100;
        color: #ffffff;
        padding: 6px 18px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 1.05rem;
        display: inline-block;
        letter-spacing: 0.5px;
    }
    .status-badge-rejected {
        background-color: #b71c1c;
        color: #ffffff;
        padding: 6px 18px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 1.05rem;
        display: inline-block;
        letter-spacing: 0.5px;
    }
    .metric-box {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 8px;
        padding: 14px;
        text-align: center;
    }
    .metric-value {
        font-size: 1.6rem;
        font-weight: 700;
        margin-top: 4px;
    }
    .metric-label {
        color: #8c9ba5;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource(show_spinner="Loading PRGI database and AI verification models...")
def get_pipeline():
    loader = PRGIDataLoader.get_instance("prgi_titles.csv")
    pipeline = AthenaVerificationPipeline(loader)
    return pipeline, loader

pipeline, loader = get_pipeline()

# Helper function to generate interactive Vis.js Network Graph
def render_interactive_graph(graph_data, proposed_title):
    nodes = []
    edges = []
    
    # Process nodes
    for n in graph_data.get("nodes", []):
        node_id = n["id"]
        node_type = n.get("type", "node")
        label = n.get("label", node_id)
        
        if node_type == "proposed_title":
            color = {"background": "#7c4dff", "border": "#b388ff"}
            shape = "box"
            size = 28
            font = {"color": "#ffffff", "size": 16, "face": "arial", "bold": True}
        elif node_type == "registered_title":
            score = n.get("score", 0.8)
            color = {"background": "#ef5350", "border": "#ff8a80"} if score > 0.85 else {"background": "#ffa726", "border": "#ffd54f"}
            shape = "ellipse"
            size = 22
            font = {"color": "#ffffff", "size": 13, "face": "arial"}
        elif node_type == "owner":
            color = {"background": "#0288d1", "border": "#4fc3f7"}
            shape = "dot"
            size = 16
            font = {"color": "#b0bec5", "size": 11, "face": "arial"}
        elif node_type == "state":
            color = {"background": "#2e7d32", "border": "#81c784"}
            shape = "dot"
            size = 14
            font = {"color": "#b0bec5", "size": 11, "face": "arial"}
        else:
            color = {"background": "#78909c", "border": "#cfd8dc"}
            shape = "dot"
            size = 14
            font = {"color": "#ffffff", "size": 12, "face": "arial"}
            
        nodes.append({
            "id": node_id,
            "label": label,
            "shape": shape,
            "color": color,
            "size": size,
            "font": font,
            "title": f"{node_type.replace('_', ' ').title()}: {label}"
        })
        
    for e in graph_data.get("edges", []):
        rel = e.get("relation", "")
        edges.append({
            "from": e["source"],
            "to": e["target"],
            "label": rel.replace("_", " "),
            "color": {"color": "#546e7a", "highlight": "#90caf9"},
            "font": {"color": "#90a4ae", "size": 10, "align": "middle"},
            "arrows": "to" if rel != "similar_to" else "",
            "smooth": {"type": "continuous"}
        })

    nodes_json = json.dumps(nodes)
    edges_json = json.dumps(edges)

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
      <style type="text/css">
        #network-canvas {{
          width: 100%;
          height: 480px;
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 8px;
          background-color: #0f141c;
        }}
        .legend {{
          display: flex;
          gap: 16px;
          padding: 8px 4px;
          font-family: sans-serif;
          font-size: 12px;
          color: #b0bec5;
        }}
        .legend-item {{
          display: flex;
          align-items: center;
          gap: 6px;
        }}
        .legend-dot {{
          width: 10px;
          height: 10px;
          border-radius: 50%;
        }}
      </style>
    </head>
    <body>
      <div class="legend">
        <div class="legend-item"><span class="legend-dot" style="background:#7c4dff;"></span> Proposed Title</div>
        <div class="legend-item"><span class="legend-dot" style="background:#ef5350;"></span> High Similarity Title</div>
        <div class="legend-item"><span class="legend-dot" style="background:#ffa726;"></span> Moderate Match</div>
        <div class="legend-item"><span class="legend-dot" style="background:#0288d1;"></span> Owner / Publisher</div>
        <div class="legend-item"><span class="legend-dot" style="background:#2e7d32;"></span> State Entity</div>
      </div>
      <div id="network-canvas"></div>
      <script type="text/javascript">
        var nodes = new vis.DataSet({nodes_json});
        var edges = new vis.DataSet({edges_json});
        var container = document.getElementById('network-canvas');
        var data = {{ nodes: nodes, edges: edges }};
        var options = {{
          nodes: {{
            borderWidth: 2,
            shadow: true
          }},
          edges: {{
            width: 1.5,
            shadow: false
          }},
          physics: {{
            solver: 'forceAtlas2Based',
            forceAtlas2Based: {{
              gravitationalConstant: -50,
              centralGravity: 0.01,
              springLength: 100,
              springConstant: 0.08,
              damping: 0.4
            }},
            maxVelocity: 50,
            minVelocity: 0.1,
            timestep: 0.5,
            stabilization: {{ iterations: 120 }}
          }},
          interaction: {{
            hover: true,
            zoomView: true,
            dragView: true,
            navigationButtons: false
          }}
        }};
        var network = new vis.Network(container, data, options);
      </script>
    </body>
    </html>
    """
    components.html(html_code, height=530)


# Top Navigation / Header Banner
col_head1, col_head2 = st.columns([3, 2])
with col_head1:
    st.markdown('<div class="app-title">Athena Title Verification System</div>', unsafe_allow_html=True)
    st.markdown('<div class="app-subtitle">Press Registrar General of India (PRGI) Automated Compliance & Verification Engine</div>', unsafe_allow_html=True)

with col_head2:
    st.markdown(f"""
    <div style="text-align: right; padding-top: 12px;">
        <span class="stat-chip">PRGI Database: {len(loader.df):,} Titles</span>
        <span class="stat-chip">Stage 1: Phonetic & Fuzzy</span>
        <span class="stat-chip">Stage 2: Multilingual Vector</span>
        <span class="stat-chip">Stage 3: Graph & xAI</span>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# Navigation Tabs without decorative emojis
tab_single, tab_batch, tab_explorer, tab_guidelines = st.tabs([
    "Title Verification",
    "Batch CSV Audit",
    "Database Explorer",
    "Statutory Guidelines"
])

# TAB 1: Single Title Verification
with tab_single:
    col_input1, col_input2 = st.columns([2, 1])
    
    with col_input1:
        proposed_title = st.text_input(
            "Proposed Publication Title*",
            placeholder="e.g. Dainik Bharat Samachar, Times of Awadh, Prabhat Khabar",
            help="Enter the exact title proposed by the publisher."
        )
    
    with col_input2:
        language = st.selectbox(
            "Publication Language",
            ["Hindi", "English", "Bengali", "Telugu", "Marathi", "Tamil", "Gujarati", "Urdu", "Kannada", "Oriya", "Malayalam", "Punjabi", "Assamese", "Bilingual", "Multilingual", "Other"]
        )

    col_meta1, col_meta2, col_meta3 = st.columns(3)
    with col_meta1:
        periodicity = st.selectbox(
            "Periodicity",
            ["Daily", "Weekly", "Fortnightly", "Monthly", "Bimonthly", "Quarterly", "Annual", "Other"]
        )
    with col_meta2:
        state = st.text_input("State of Publication", placeholder="e.g. Maharashtra, Uttar Pradesh, Delhi")
    with col_meta3:
        district = st.text_input("District of Publication", placeholder="e.g. Mumbai, Lucknow, New Delhi")

    verify_btn = st.button("Run Verification Analysis", type="primary", use_container_width=True)

    if verify_btn and proposed_title.strip():
        with st.spinner("Analyzing proposed title across 3 verification stages..."):
            result = pipeline.verify_title(
                proposed_title=proposed_title,
                language=language,
                periodicity=periodicity,
                state=state,
                district=district
            )

        st.divider()

        # Decision Summary Metrics
        col_res1, col_res2, col_res3, col_res4 = st.columns([1.6, 1, 1, 1])
        
        with col_res1:
            st.markdown("<div class='metric-label'>Verification Verdict</div>", unsafe_allow_html=True)
            status = result["status"]
            if status == "APPROVED":
                st.markdown('<div class="status-badge-approved">APPROVED</div>', unsafe_allow_html=True)
            elif status == "UNDER_REVIEW":
                st.markdown('<div class="status-badge-review">UNDER REVIEW</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="status-badge-rejected">REJECTED</div>', unsafe_allow_html=True)
            st.caption(result["status_desc"])

        with col_res2:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-label">Approval Probability</div>
                <div class="metric-value" style="color: {'#4caf50' if result['acceptance_probability'] >= 70 else '#ffa726' if result['acceptance_probability'] >= 45 else '#ef5350'};">
                    {result['acceptance_probability']}%
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_res3:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-label">Max Similarity</div>
                <div class="metric-value">
                    {result['highest_similarity']*100:.1f}%
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_res4:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-label">Pipeline Latency</div>
                <div class="metric-value">
                    {result['total_latency_ms']} ms
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Stage Breakdown Sections
        s_tab_graph, s_tab_xai, s_tab_candidates, s_tab_rules, s_tab_recs = st.tabs([
            "Interactive Network Graph",
            "Explainable AI (xAI)",
            "Matched Registered Titles",
            "Statutory Compliance Audit",
            "Recommendations"
        ])

        # TAB: Interactive Network Graph
        with s_tab_graph:
            st.subheader("Co-Registration & Semantic Network Graph")
            st.caption("Interactive force-directed graph displaying relationship clusters between the proposed title, existing registered titles, owners, and publication states. Drag nodes to explore connections.")
            
            graph_data = result["stage3_results"]["graph_data"]
            if graph_data and graph_data.get("nodes"):
                render_interactive_graph(graph_data, proposed_title)
            else:
                st.info("No co-registration graph relationships detected for this query.")

        # TAB: Explainable AI
        with s_tab_xai:
            col_xai1, col_xai2 = st.columns(2)
            
            with col_xai1:
                st.subheader("Token Feature Importance (SHAP/LIME style)")
                st.caption("Contribution of each word in the proposed title to the overall similarity and collision risk.")
                influential = result["stage3_results"]["influential_words"]
                if influential:
                    xai_df = pd.DataFrame(influential)
                    fig_bar = px.bar(
                        xai_df,
                        x="importance",
                        y="word",
                        orientation="h",
                        color="importance",
                        color_continuous_scale="Blues",
                        labels={"importance": "Risk Contribution Weight", "word": "Token in Title"}
                    )
                    fig_bar.update_layout(yaxis={'categoryorder':'total ascending'}, height=320, margin=dict(l=20, r=20, t=20, b=20))
                    st.plotly_chart(fig_bar, use_container_width=True)
                else:
                    st.info("No tokens found.")

            with col_xai2:
                st.subheader("Attention Weight Distribution")
                st.caption("Transformer attention distribution across title tokens.")
                attention = result["stage3_results"]["attention_weights"]
                if attention:
                    fig_pie = px.pie(
                        names=list(attention.keys()),
                        values=list(attention.values()),
                        hole=0.45
                    )
                    fig_pie.update_layout(height=320, margin=dict(l=20, r=20, t=20, b=20))
                    st.plotly_chart(fig_pie, use_container_width=True)

        # TAB: Top Matched Candidates
        with s_tab_candidates:
            st.subheader("Top Matching Registered Titles")
            candidates = result["top_candidates"]
            if candidates:
                cand_table = []
                for c in candidates:
                    cand_table.append({
                        "SN": c["sn"],
                        "Registered Title": c["matched_title"],
                        "Language": c.get("language", ""),
                        "Periodicity": c.get("periodicity", ""),
                        "State": c.get("state", ""),
                        "Owner": c.get("owner", ""),
                        "Similarity Score": f"{c['final_similarity_score']*100:.1f}%",
                        "Levenshtein Dist": c.get("levenshtein_distance", "N/A"),
                        "Soundex Match": "Yes" if c.get("soundex_match") else "No"
                    })
                st.dataframe(pd.DataFrame(cand_table), use_container_width=True)
            else:
                st.success("No matching registered titles found in the PRGI database.")

        # TAB: Statutory Rules Audit
        with s_tab_rules:
            st.subheader("Statutory Compliance Findings")
            compliance = result["compliance"]
            
            if compliance["violations"]:
                st.error("Violations Detected:")
                for v in compliance["violations"]:
                    st.markdown(f"- **[{v['severity']}] {v['rule']}**: {v['detail']}")
            else:
                st.success("Passed all statutory compliance checks (Emblems & Names Act, Periodicity Manipulation Rules).")

            if compliance["warnings"]:
                st.warning("Warnings:")
                for w in compliance["warnings"]:
                    st.markdown(f"- **[{w['severity']}] {w['rule']}**: {w['detail']}")

        # TAB: Recommendations
        with s_tab_recs:
            st.subheader("Improvement Recommendations")
            if result["recommendations"]:
                for rec in result["recommendations"]:
                    st.info(rec)
            else:
                st.success("The title complies with uniqueness and statutory standards. No modifications required.")

# TAB 2: Batch CSV Verification
with tab_batch:
    st.subheader("Bulk Title Verification")
    st.markdown("Upload a CSV file containing a column named `title` (optional columns: `language`, `periodicity`, `state`).")
    
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
    if uploaded_file is not None:
        batch_df = pd.read_csv(uploaded_file)
        st.write("Uploaded Sample:")
        st.dataframe(batch_df.head(5), use_container_width=True)
        
        if "title" in batch_df.columns:
            if st.button("Run Batch Verification", type="primary"):
                progress_bar = st.progress(0)
                batch_results = []
                
                total = len(batch_df)
                for idx, row in batch_df.iterrows():
                    t = str(row["title"])
                    lang = str(row.get("language", ""))
                    period = str(row.get("periodicity", ""))
                    st_val = str(row.get("state", ""))
                    
                    res = pipeline.verify_title(t, language=lang, periodicity=period, state=st_val)
                    batch_results.append({
                        "Title": t,
                        "Status": res["status"],
                        "Approval Probability (%)": res["acceptance_probability"],
                        "Highest Similarity (%)": f"{res['highest_similarity']*100:.1f}",
                        "Top Matched Title": res["top_candidates"][0]["matched_title"] if res["top_candidates"] else "None",
                        "Violations Count": len(res["compliance"]["violations"])
                    })
                    progress_bar.progress((idx + 1) / total)
                    
                res_df = pd.DataFrame(batch_results)
                st.success(f"Successfully processed {len(res_df)} titles.")
                st.dataframe(res_df, use_container_width=True)
                
                csv_data = res_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download Audited CSV Report",
                    data=csv_data,
                    file_name="athena_batch_audit_results.csv",
                    mime="text/csv"
                )
        else:
            st.error("Uploaded CSV must contain a 'title' column.")

# TAB 3: Database Explorer
with tab_explorer:
    st.subheader("Registered PRGI Database Explorer")
    search_query = st.text_input("Search registered database by title keyword or owner name:")
    
    if search_query.strip():
        q = search_query.strip().upper()
        filtered = loader.df[
            loader.df["clean_title"].str.contains(q, na=False) |
            loader.df["owner"].fillna("").astype(str).str.upper().str.contains(q, na=False)
        ]
        st.write(f"Found {len(filtered)} matching records:")
        st.dataframe(filtered[["sn", "title", "registration_number", "registration_date", "language", "periodicity", "publisher", "owner", "publication_state", "publication_district"]].head(100), use_container_width=True)
    else:
        st.dataframe(loader.df[["sn", "title", "registration_number", "registration_date", "language", "periodicity", "publisher", "owner", "publication_state", "publication_district"]].head(50), use_container_width=True)

# TAB 4: Statutory Guidelines
with tab_guidelines:
    st.subheader("PRGI Statutory Verification Guidelines")
    st.markdown("""
    ### Key Registration Principles
    1. **Uniqueness & Non-Collision**: The proposed title must not be identical or deceptively similar to any existing registered newspaper or periodical title.
    2. **Emblems and Names (Prevention of Improper Use) Act, 1950**:
       - Titles containing protected words (e.g. *Police*, *CBI*, *CID*, *Anti Corruption*, *Rashtrapati*, *Supreme Court*, *Parliament*) are prohibited without statutory authorization.
    3. **Periodicity Prefix/Suffix Manipulation**:
       - Merely adding or removing periodicity terms (e.g. *Daily*, *Weekly*, *Monthly*, *Dainik*, *Saptahik*) to an existing title is disallowed.
    4. **State & Language Restrictions**:
       - Similar or identical titles in the same language published from the same state or union territory are subject to strict rejection.
    """)

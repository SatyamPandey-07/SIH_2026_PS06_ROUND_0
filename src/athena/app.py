import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import time
import os
from collections import Counter

from athena.data_loader import PRGIDataLoader
from athena.pipeline import AthenaVerificationPipeline
from athena.certificate import generate_verification_certificate

# Page configuration - Sidebar removed completely
st.set_page_config(
    page_title="Athena | PRGI AI Title Verification System",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom High-Impact Styling
st.markdown("""
<style>
    /* Completely hide sidebar and collapsed toggle */
    [data-testid="stSidebar"], [data-testid="collapsedControl"] {
        display: none !important;
    }
    
    /* Main typography & headers */
    .app-title {
        font-size: 2.3rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        background: linear-gradient(135deg, #42a5f5 0%, #ab47bc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.1rem;
    }
    .app-subtitle {
        color: #90a4ae;
        font-size: 0.95rem;
        margin-bottom: 0.8rem;
    }
    
    /* Top chips */
    .stat-chip {
        display: inline-block;
        background-color: rgba(33, 150, 243, 0.1);
        color: #64b5f6;
        border: 1px solid rgba(33, 150, 243, 0.25);
        border-radius: 6px;
        padding: 4px 10px;
        font-size: 0.82rem;
        font-weight: 600;
        margin-left: 6px;
    }

    /* Decision Badges */
    .status-badge-approved {
        background-color: #1b5e20;
        color: #ffffff;
        padding: 8px 20px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 1.15rem;
        display: inline-block;
        letter-spacing: 0.5px;
        box-shadow: 0 2px 8px rgba(27, 94, 32, 0.4);
    }
    .status-badge-review {
        background-color: #e65100;
        color: #ffffff;
        padding: 8px 20px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 1.15rem;
        display: inline-block;
        letter-spacing: 0.5px;
        box-shadow: 0 2px 8px rgba(230, 81, 0, 0.4);
    }
    .status-badge-rejected {
        background-color: #b71c1c;
        color: #ffffff;
        padding: 8px 20px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 1.15rem;
        display: inline-block;
        letter-spacing: 0.5px;
        box-shadow: 0 2px 8px rgba(183, 28, 28, 0.4);
    }

    /* Metric Cards */
    .metric-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 8px;
        padding: 12px 16px;
        text-align: center;
    }
    .metric-card-val {
        font-size: 1.6rem;
        font-weight: 700;
        margin-top: 2px;
    }
    .metric-card-lbl {
        color: #90a4ae;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Demo preset bar */
    .preset-title {
        font-size: 0.85rem;
        font-weight: 700;
        color: #90caf9;
        margin-bottom: 6px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Smart alternative cards */
    .alt-card {
        background: rgba(33, 150, 243, 0.06);
        border: 1px solid rgba(33, 150, 243, 0.2);
        border-radius: 6px;
        padding: 10px 14px;
        margin-bottom: 8px;
    }
    .alt-title {
        font-weight: 700;
        color: #64b5f6;
        font-size: 0.95rem;
    }
    .alt-reason {
        color: #b0bec5;
        font-size: 0.82rem;
        margin-top: 2px;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource(show_spinner="Initializing PRGI database and AI verification models...")
def get_pipeline():
    loader = PRGIDataLoader.get_instance("prgi_titles.csv")
    pipeline = AthenaVerificationPipeline(loader)
    return pipeline, loader

pipeline, loader = get_pipeline()

# Helper function to generate interactive Vis.js Network Graph
def render_interactive_graph(graph_data, proposed_title):
    nodes = []
    edges = []
    
    for n in graph_data.get("nodes", []):
        node_id = n["id"]
        node_type = n.get("type", "node")
        label = n.get("label", node_id)
        
        if node_type == "proposed_title":
            color = {"background": "#7c4dff", "border": "#b388ff"}
            shape = "box"
            size = 28
            font = {"color": "#ffffff", "size": 15, "face": "Segoe UI", "bold": True}
        elif node_type == "registered_title":
            score = n.get("score", 0.8)
            color = {"background": "#ef5350", "border": "#ff8a80"} if score > 0.85 else {"background": "#ffa726", "border": "#ffd54f"}
            shape = "ellipse"
            size = 22
            font = {"color": "#ffffff", "size": 13, "face": "Segoe UI"}
        elif node_type == "owner":
            color = {"background": "#0288d1", "border": "#4fc3f7"}
            shape = "dot"
            size = 16
            font = {"color": "#b0bec5", "size": 11, "face": "Segoe UI"}
        elif node_type == "state":
            color = {"background": "#2e7d32", "border": "#81c784"}
            shape = "dot"
            size = 14
            font = {"color": "#b0bec5", "size": 11, "face": "Segoe UI"}
        else:
            color = {"background": "#78909c", "border": "#cfd8dc"}
            shape = "dot"
            size = 14
            font = {"color": "#ffffff", "size": 12, "face": "Segoe UI"}
            
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
          height: 460px;
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 8px;
          background-color: #0d1117;
        }}
        .legend {{
          display: flex;
          gap: 16px;
          padding: 8px 4px;
          font-family: 'Segoe UI', sans-serif;
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
        <div class="legend-item"><span class="legend-dot" style="background:#ef5350;"></span> High Collision Match (>85%)</div>
        <div class="legend-item"><span class="legend-dot" style="background:#ffa726;"></span> Moderate Match</div>
        <div class="legend-item"><span class="legend-dot" style="background:#0288d1;"></span> Publisher / Owner</div>
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
            dragView: true
          }}
        }};
        var network = new vis.Network(container, data, options);
      </script>
    </body>
    </html>
    """
    components.html(html_code, height=510)


# Top Navigation / Header Banner
col_head1, col_head2 = st.columns([3, 2])
with col_head1:
    st.markdown('<div class="app-title">Athena: PRGI AI Title Verification System</div>', unsafe_allow_html=True)
    st.markdown('<div class="app-subtitle">Automated Three-Stage Newspaper & Periodical Title Verification with Explainable AI</div>', unsafe_allow_html=True)

with col_head2:
    st.markdown(f"""
    <div style="text-align: right; padding-top: 10px;">
        <span class="stat-chip">PRGI Records: {len(loader.df):,}</span>
        <span class="stat-chip">Stage 1: Phonetic & Fuzzy</span>
        <span class="stat-chip">Stage 2: Multilingual Vector</span>
        <span class="stat-chip">Stage 3: Graph xAI</span>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# Navigation Tabs
tab_single, tab_batch, tab_analytics, tab_explorer, tab_guidelines = st.tabs([
    "Title Verification",
    "Batch CSV Audit",
    "National Database Analytics",
    "Database Explorer",
    "Statutory Guidelines"
])

# TAB 1: Single Title Verification
with tab_single:
    # 1-Click Live Demo Presets for Hackathon / PPT round
    st.markdown('<div class="preset-title">Live Hackathon Demo Presets (1-Click Evaluation Scenarios)</div>', unsafe_allow_html=True)
    
    preset_col1, preset_col2, preset_col3, preset_col4, preset_col5 = st.columns(5)
    
    preset_data = None
    if preset_col1.button("1. Direct Collision", help="Exact match: 'A &S INDIA'", use_container_width=True):
        preset_data = {"title": "A &S INDIA", "lang": "English", "period": "Monthly", "state": "Maharashtra"}
    if preset_col2.button("2. Deceptive Phonetic", help="Phonetic tweak: 'Dainik Khabbar'", use_container_width=True):
        preset_data = {"title": "Dainik Khabbar", "lang": "Hindi", "period": "Daily", "state": "Madhya Pradesh"}
    if preset_col3.button("3. Periodicity Violation", help="Prefix addition: 'Daily The Hindu'", use_container_width=True):
        preset_data = {"title": "Daily The Hindu", "lang": "English", "period": "Daily", "state": "Delhi"}
    if preset_col4.button("4. Emblems Act Infringement", help="Prohibited word: 'Police Crime Branch Times'", use_container_width=True):
        preset_data = {"title": "Police Crime Branch Times", "lang": "English", "period": "Weekly", "state": "Delhi"}
    if preset_col5.button("5. Compliant Novel Title", help="Clean title: 'Vindhya Innovation Chronicle'", use_container_width=True):
        preset_data = {"title": "Vindhya Innovation Chronicle", "lang": "English", "period": "Monthly", "state": "Madhya Pradesh"}

    # Form inputs with session state fallback from presets
    if "input_title" not in st.session_state:
        st.session_state.input_title = "Dainik Bharat Samachar"
    if "input_lang" not in st.session_state:
        st.session_state.input_lang = "Hindi"
    if "input_period" not in st.session_state:
        st.session_state.input_period = "Daily"
    if "input_state" not in st.session_state:
        st.session_state.input_state = "Uttar Pradesh"

    if preset_data:
        st.session_state.input_title = preset_data["title"]
        st.session_state.input_lang = preset_data["lang"]
        st.session_state.input_period = preset_data["period"]
        st.session_state.input_state = preset_data["state"]

    col_input1, col_input2 = st.columns([2.5, 1])
    with col_input1:
        proposed_title = st.text_input(
            "Proposed Publication Title*",
            value=st.session_state.input_title,
            placeholder="e.g. Dainik Bharat Samachar, Times of Awadh, Prabhat Khabar",
            help="Enter the exact title proposed by the publisher."
        )
    with col_input2:
        lang_list = ["Hindi", "English", "Bengali", "Telugu", "Marathi", "Tamil", "Gujarati", "Urdu", "Kannada", "Oriya", "Malayalam", "Punjabi", "Assamese", "Bilingual", "Multilingual", "Other"]
        lang_idx = lang_list.index(st.session_state.input_lang) if st.session_state.input_lang in lang_list else 0
        language = st.selectbox("Publication Language", lang_list, index=lang_idx)

    col_meta1, col_meta2, col_meta3 = st.columns(3)
    with col_meta1:
        period_list = ["Daily", "Weekly", "Fortnightly", "Monthly", "Bimonthly", "Quarterly", "Annual", "Other"]
        period_idx = period_list.index(st.session_state.input_period) if st.session_state.input_period in period_list else 0
        periodicity = st.selectbox("Periodicity", period_list, index=period_idx)
    with col_meta2:
        state = st.text_input("State of Publication", value=st.session_state.input_state, placeholder="e.g. Maharashtra, Uttar Pradesh, Delhi")
    with col_meta3:
        district = st.text_input("District of Publication", placeholder="e.g. Mumbai, Lucknow, Bhopal")

    verify_btn = st.button("Run Verification Analysis", type="primary", use_container_width=True)

    # Automatic trigger if preset clicked or button pressed
    if (verify_btn or preset_data) and proposed_title.strip():
        with st.spinner("Executing 3-Stage Verification Pipeline across 82,730 titles..."):
            result = pipeline.verify_title(
                proposed_title=proposed_title,
                language=language,
                periodicity=periodicity,
                state=state,
                district=district
            )

        st.divider()

        # Top Results Overview
        col_res1, col_res2, col_res3, col_res4 = st.columns([1.8, 1.2, 1, 1])
        
        with col_res1:
            st.markdown("<div class='metric-card-lbl'>Official Verdict</div>", unsafe_allow_html=True)
            status = result["status"]
            if status == "APPROVED":
                st.markdown('<div class="status-badge-approved">APPROVED</div>', unsafe_allow_html=True)
            elif status == "UNDER_REVIEW":
                st.markdown('<div class="status-badge-review">UNDER REVIEW</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="status-badge-rejected">REJECTED</div>', unsafe_allow_html=True)
            st.caption(result["status_desc"])

        with col_res2:
            # Dynamic Radial Plotly Gauge
            prob_val = result['acceptance_probability']
            gauge_color = "#2e7d32" if prob_val >= 70 else "#ed6c02" if prob_val >= 45 else "#c62828"
            
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=prob_val,
                number={'suffix': "%", 'font': {'size': 24, 'color': gauge_color}},
                title={'text': "Approval Probability", 'font': {'size': 13, 'color': "#90a4ae"}},
                gauge={
                    'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#546e7a"},
                    'bar': {'color': gauge_color},
                    'bgcolor': "rgba(0,0,0,0)",
                    'borderwidth': 1,
                    'bordercolor': "#37474f",
                    'steps': [
                        {'range': [0, 45], 'color': 'rgba(198, 40, 40, 0.2)'},
                        {'range': [45, 70], 'color': 'rgba(237, 108, 2, 0.2)'},
                        {'range': [70, 100], 'color': 'rgba(46, 125, 50, 0.2)'}
                    ],
                    'threshold': {
                        'line': {'color': "white", 'width': 3},
                        'thickness': 0.75,
                        'value': prob_val
                    }
                }
            ))
            fig_gauge.update_layout(height=140, margin=dict(l=10, r=10, t=25, b=5))
            st.plotly_chart(fig_gauge, use_container_width=True)

        with col_res3:
            st.markdown(f"""
            <div class="metric-card" style="margin-top: 10px;">
                <div class="metric-card-lbl">Max Similarity</div>
                <div class="metric-card-val" style="color: {'#ef5350' if result['highest_similarity'] > 0.8 else '#ffa726' if result['highest_similarity'] > 0.6 else '#66bb6a'};">
                    {result['highest_similarity']*100:.1f}%
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_res4:
            st.markdown(f"""
            <div class="metric-card" style="margin-top: 10px;">
                <div class="metric-card-lbl">Pipeline Latency</div>
                <div class="metric-card-val">
                    {result['total_latency_ms']} ms
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Multi-Stage Waterfall Status Banner
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("##### Three-Stage Multi-Modal Pipeline Execution Flow")
        w_col1, w_col2, w_col3, w_col4 = st.columns(4)
        
        s1 = result["stage1_results"]
        s2 = result["stage2_results"]
        comp = result["compliance"]

        with w_col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-card-lbl">Stage 1: Phonetic & Fuzzy</div>
                <div style="font-weight:700; color:{'#ef5350' if s1['flagged'] else '#66bb6a'}; margin: 4px 0;">
                    {'FLAGGED' if s1['flagged'] else 'PASSED'} ({s1['max_score']*100:.1f}%)
                </div>
                <div style="font-size:0.75rem; color:#90a4ae;">{s1['time_ms']} ms | Soundex, Metaphone, Levenshtein</div>
            </div>
            """, unsafe_allow_html=True)

        with w_col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-card-lbl">Stage 2: Multilingual Vector</div>
                <div style="font-weight:700; color:{'#ef5350' if s2['flagged'] else '#66bb6a'}; margin: 4px 0;">
                    {'FLAGGED' if s2['flagged'] else 'PASSED'} ({s2['max_score']*100:.1f}%)
                </div>
                <div style="font-size:0.75rem; color:#90a4ae;">{s2['time_ms']} ms | Semantic Cross-Lingual Vector</div>
            </div>
            """, unsafe_allow_html=True)

        with w_col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-card-lbl">Stage 3: Graph Structure & xAI</div>
                <div style="font-weight:700; color:#42a5f5; margin: 4px 0;">
                    {len(result['stage3_results']['influential_words'])} Tokens Indexed
                </div>
                <div style="font-size:0.75rem; color:#90a4ae;">SHAP / LIME Weights + Co-Registration Graph</div>
            </div>
            """, unsafe_allow_html=True)

        with w_col4:
            v_count = len(comp["violations"])
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-card-lbl">Statutory Rules Engine</div>
                <div style="font-weight:700; color:{'#ef5350' if v_count > 0 else '#66bb6a'}; margin: 4px 0;">
                    {f'{v_count} VIOLATIONS' if v_count > 0 else 'COMPLIANT'}
                </div>
                <div style="font-size:0.75rem; color:#90a4ae;">Emblems Act, Periodicity & State Rules</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Stage Breakdown Tabs
        s_tab_graph, s_tab_xai, s_tab_candidates, s_tab_alts, s_tab_rules, s_tab_cert = st.tabs([
            "Interactive Network Graph",
            "Explainable AI (xAI)",
            "Top Matched Candidates",
            "Smart Title Alternatives",
            "Statutory Compliance Audit",
            "Export Official Certificate"
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
                        color_continuous_scale="Reds",
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

        # TAB: Smart Title Alternatives
        with s_tab_alts:
            st.subheader("AI-Suggested Compliant Title Variations")
            st.caption("Automatically generated distinctive title variations that pass PRGI statutory checks and avoid duplicate collision.")
            
            alts = result.get("smart_alternatives", [])
            if alts:
                for a in alts:
                    st.markdown(f"""
                    <div class="alt-card">
                        <div class="alt-title">{a['title']}</div>
                        <div class="alt-reason">{a['reason']}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.success("The proposed title is already distinctive and unique. No alternative modifications required!")

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

        # TAB: Export Official Certificate
        with s_tab_cert:
            st.subheader("Official PRGI Title Verification Compliance Certificate")
            st.caption("Downloadable official audit document formatted for publication submission dossiers.")
            
            cert_html = generate_verification_certificate(result)
            
            st.download_button(
                label="Download Official Verification Certificate (HTML)",
                data=cert_html,
                file_name=f"PRGI_Verification_Certificate_{proposed_title.replace(' ','_')}.html",
                mime="text/html",
                use_container_width=True
            )
            
            with st.expander("Preview Digital Certificate"):
                components.html(cert_html, height=600, scrolling=True)


# TAB 2: Batch CSV Verification
with tab_batch:
    st.subheader("Bulk Title Verification Audit")
    st.markdown("Upload a CSV file containing a column named `title` (optional columns: `language`, `periodicity`, `state`).")
    
    uploaded_file = st.file_uploader("Upload CSV File", type=["csv"])
    if uploaded_file is not None:
        batch_df = pd.read_csv(uploaded_file)
        st.write("Uploaded Sample Preview:")
        st.dataframe(batch_df.head(5), use_container_width=True)
        
        if "title" in batch_df.columns:
            if st.button("Run Batch Verification Audit", type="primary"):
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
                st.success(f"Audit Complete: Successfully verified {len(res_df)} titles.")
                
                # Visual summary breakdown
                col_b1, col_b2 = st.columns([1, 2])
                with col_b1:
                    status_counts = res_df["Status"].value_counts().reset_index()
                    status_counts.columns = ["Status", "Count"]
                    fig_batch_pie = px.pie(
                        status_counts,
                        names="Status",
                        values="Count",
                        color="Status",
                        color_discrete_map={"APPROVED": "#2e7d32", "UNDER_REVIEW": "#ed6c02", "REJECTED": "#c62828"},
                        hole=0.45,
                        title="Audit Verdict Distribution"
                    )
                    st.plotly_chart(fig_batch_pie, use_container_width=True)
                with col_b2:
                    st.dataframe(res_df, use_container_width=True)
                
                csv_data = res_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download Audited Batch Report (CSV)",
                    data=csv_data,
                    file_name="athena_batch_audit_results.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        else:
            st.error("Uploaded CSV must contain a 'title' column.")


# TAB 3: National PRGI Database Analytics
with tab_analytics:
    st.subheader("National PRGI Database Analytics & Insights")
    st.caption(f"Statistical distribution across {len(loader.df):,} officially registered publications in India.")
    
    col_an1, col_an2 = st.columns(2)
    
    with col_an1:
        st.markdown("##### Top 10 Publication Languages")
        lang_counts = loader.df["language"].fillna("Unknown").value_counts().head(10).reset_index()
        lang_counts.columns = ["Language", "Count"]
        fig_lang = px.bar(
            lang_counts,
            x="Count",
            y="Language",
            orientation="h",
            color="Count",
            color_continuous_scale="Blues"
        )
        fig_lang.update_layout(yaxis={'categoryorder':'total ascending'}, height=340, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_lang, use_container_width=True)

    with col_an2:
        st.markdown("##### Periodicity Distribution")
        period_counts = loader.df["periodicity"].fillna("Unknown").value_counts().head(8).reset_index()
        period_counts.columns = ["Periodicity", "Count"]
        fig_period = px.pie(
            period_counts,
            names="Periodicity",
            values="Count",
            hole=0.45
        )
        fig_period.update_layout(height=340, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_period, use_container_width=True)

    col_an3, col_an4 = st.columns(2)
    with col_an3:
        st.markdown("##### Top 10 Publication States")
        state_counts = loader.df["publication_state"].fillna("Unknown").value_counts().head(10).reset_index()
        state_counts.columns = ["State", "Count"]
        fig_state = px.bar(
            state_counts,
            x="Count",
            y="State",
            orientation="h",
            color="Count",
            color_continuous_scale="Teal"
        )
        fig_state.update_layout(yaxis={'categoryorder':'total ascending'}, height=340, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_state, use_container_width=True)

    with col_an4:
        st.markdown("##### High-Frequency Lexical Keywords in Indian Titles")
        # Extract top words from indexed vocabulary
        top_words = loader.titles
        word_list = []
        for t in top_words[:5000]:
            word_list.extend([w for w in t.split() if len(w) > 3])
        word_counts = Counter(word_list).most_common(10)
        w_df = pd.DataFrame(word_counts, columns=["Keyword", "Frequency"])
        fig_kw = px.bar(
            w_df,
            x="Frequency",
            y="Keyword",
            orientation="h",
            color="Frequency",
            color_continuous_scale="Viridis"
        )
        fig_kw.update_layout(yaxis={'categoryorder':'total ascending'}, height=340, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_kw, use_container_width=True)


# TAB 4: Database Explorer
with tab_explorer:
    st.subheader("Registered PRGI Database Explorer")
    search_query = st.text_input("Search registered database by title keyword, registration number, or owner name:")
    
    if search_query.strip():
        q = search_query.strip().upper()
        filtered = loader.df[
            loader.df["clean_title"].str.contains(q, na=False) |
            loader.df["owner"].fillna("").astype(str).str.upper().str.contains(q, na=False) |
            loader.df["registration_number"].fillna("").astype(str).str.upper().str.contains(q, na=False)
        ]
        st.write(f"Found {len(filtered)} matching records:")
        st.dataframe(filtered[["sn", "title", "registration_number", "registration_date", "language", "periodicity", "publisher", "owner", "publication_state", "publication_district"]].head(100), use_container_width=True)
    else:
        st.dataframe(loader.df[["sn", "title", "registration_number", "registration_date", "language", "periodicity", "publisher", "owner", "publication_state", "publication_district"]].head(50), use_container_width=True)


# TAB 5: Statutory Guidelines
with tab_guidelines:
    st.subheader("PRGI Statutory Verification Guidelines")
    st.markdown("""
    ### Key Statutory Registration Principles
    
    1. **Uniqueness & Non-Deceptiveness**:
       - The proposed title must not be identical or deceptively similar to any existing registered newspaper or periodical title.
       - Phonetic variations (e.g. *Khabar* vs *Khabbar*) and spelling distortions are strictly disallowed.

    2. **The Emblems and Names (Prevention of Improper Use) Act, 1950**:
       - Titles containing protected national and statutory keywords (*Police*, *CBI*, *CID*, *Anti Corruption*, *Vigilance*, *Rashtrapati*, *Supreme Court*, *Parliament*, *Government*) are prohibited without prior official authorization.

    3. **Periodicity Prefix/Suffix Manipulation Rule**:
       - Merely adding or omitting periodicity terms (e.g. *Daily*, *Weekly*, *Monthly*, *Dainik*, *Saptahik*, *Sandhya*, *Prabhat*) to an existing title is invalid.

    4. **State & Language Territorial Conflict**:
       - Identical or near-identical titles in the same publication language published within the same state/union territory face mandatory rejection.
    """)

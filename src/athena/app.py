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
from athena.app_tracker import ApplicationTracker

# Page configuration
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
        margin-bottom: 0.6rem;
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
        font-size: 1.1rem;
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
        font-size: 1.1rem;
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
        font-size: 1.1rem;
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
        font-size: 1.5rem;
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

    /* Timeline and Review styles */
    .review-dossier {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        padding: 18px;
        margin-top: 12px;
    }
    .action-panel {
        background: rgba(30, 136, 229, 0.06);
        border: 1px solid rgba(30, 136, 229, 0.25);
        border-radius: 8px;
        padding: 18px;
        margin-top: 16px;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource(show_spinner="Initializing PRGI database and AI verification models...")
def get_pipeline():
    loader = PRGIDataLoader.get_instance("prgi_titles.csv")
    pipeline = AthenaVerificationPipeline(loader)
    tracker = ApplicationTracker.get_instance()
    return pipeline, loader, tracker

pipeline, loader, tracker = get_pipeline()

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


# Top Navigation / Header Banner with Role Switcher
col_head1, col_head2 = st.columns([2.5, 2.5])
with col_head1:
    st.markdown('<div class="app-title">Athena: PRGI AI Title Verification System</div>', unsafe_allow_html=True)
    st.markdown('<div class="app-subtitle">Press Registrar General of India (PRGI) Title Verification & Administrative Workflow</div>', unsafe_allow_html=True)

with col_head2:
    portal_mode = st.radio(
        "Active Portal Mode",
        ["Publisher / Applicant Portal", "PRGI Official & Registrar Admin Portal"],
        horizontal=True
    )
    all_apps = tracker.get_all_applications()
    pending_count = len([a for a in all_apps if a["status"] in ["PENDING_REVIEW", "AUTO_AUDITED_CLEAR"]])
    st.markdown(f"""
    <div style="text-align: right; padding-top: 4px;">
        <span class="stat-chip">PRGI Database: {len(loader.df):,} Titles</span>
        <span class="stat-chip">Live Applications: {len(all_apps)}</span>
        <span class="stat-chip" style="color:#ffa726;">Pending Review: {pending_count}</span>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ==============================================================================
# MODE 1: PUBLISHER / APPLICANT PORTAL
# ==============================================================================
if portal_mode == "Publisher / Applicant Portal":
    user_tab_verify, user_tab_apply, user_tab_track, user_tab_batch, user_tab_guidelines = st.tabs([
        "Live Title Verification",
        "Submit Formal Application",
        "Track Application & Certificate",
        "Batch CSV Audit",
        "Statutory Guidelines"
    ])

    # SUB-TAB 1: Live Title Verification
    with user_tab_verify:
        st.markdown('<div class="preset-title">Live Hackathon Demo Presets (1-Click Evaluation Scenarios)</div>', unsafe_allow_html=True)
        
        p_col1, p_col2, p_col3, p_col4, p_col5 = st.columns(5)
        preset_data = None
        if p_col1.button("1. Direct Collision", help="Exact match: 'A &S INDIA'", use_container_width=True):
            preset_data = {"title": "A &S INDIA", "lang": "English", "period": "Monthly", "state": "Maharashtra"}
        if p_col2.button("2. Deceptive Phonetic", help="Phonetic tweak: 'Dainik Khabbar'", use_container_width=True):
            preset_data = {"title": "Dainik Khabbar", "lang": "Hindi", "period": "Daily", "state": "Madhya Pradesh"}
        if p_col3.button("3. Combined Titles Violation", help="Combining 2 titles: 'Hindu Indian Express'", use_container_width=True):
            preset_data = {"title": "Hindu Indian Express", "lang": "English", "period": "Daily", "state": "Delhi"}
        if p_col4.button("4. Emblems Act Infringement", help="Prohibited word: 'Police Crime Branch Times'", use_container_width=True):
            preset_data = {"title": "Police Crime Branch Times", "lang": "English", "period": "Weekly", "state": "Delhi"}
        if p_col5.button("5. Compliant Novel Title", help="Clean title: 'Vindhya Innovation Chronicle'", use_container_width=True):
            preset_data = {"title": "Vindhya Innovation Chronicle", "lang": "English", "period": "Monthly", "state": "Madhya Pradesh"}

        if "user_title" not in st.session_state:
            st.session_state.user_title = "Dainik Bharat Samachar"
        if "user_lang" not in st.session_state:
            st.session_state.user_lang = "Hindi"
        if "user_period" not in st.session_state:
            st.session_state.user_period = "Daily"
        if "user_state" not in st.session_state:
            st.session_state.user_state = "Uttar Pradesh"

        if preset_data:
            st.session_state.user_title = preset_data["title"]
            st.session_state.user_lang = preset_data["lang"]
            st.session_state.user_period = preset_data["period"]
            st.session_state.user_state = preset_data["state"]

        col_in1, col_in2 = st.columns([2.5, 1])
        with col_in1:
            prop_title = st.text_input(
                "Proposed Publication Title*",
                value=st.session_state.user_title,
                placeholder="e.g. Dainik Bharat Samachar, Times of Awadh, Prabhat Khabar",
                help="Enter the exact title proposed by the publisher."
            )
        with col_in2:
            lang_opts = ["Hindi", "English", "Bengali", "Telugu", "Marathi", "Tamil", "Gujarati", "Urdu", "Kannada", "Oriya", "Malayalam", "Punjabi", "Assamese", "Bilingual", "Multilingual", "Other"]
            l_idx = lang_opts.index(st.session_state.user_lang) if st.session_state.user_lang in lang_opts else 0
            u_lang = st.selectbox("Publication Language", lang_opts, index=l_idx)

        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            per_opts = ["Daily", "Weekly", "Fortnightly", "Monthly", "Bimonthly", "Quarterly", "Annual", "Other"]
            p_idx = per_opts.index(st.session_state.user_period) if st.session_state.user_period in per_opts else 0
            u_period = st.selectbox("Periodicity", per_opts, index=p_idx)
        with col_m2:
            u_state = st.text_input("State of Publication", value=st.session_state.user_state, placeholder="e.g. Maharashtra, Uttar Pradesh, Delhi")
        with col_m3:
            u_district = st.text_input("District of Publication", placeholder="e.g. Mumbai, Lucknow, Bhopal")

        v_btn = st.button("Run Live Verification Analysis", type="primary", use_container_width=True)

        if (v_btn or preset_data) and prop_title.strip():
            with st.spinner("Analyzing proposed title across 3 verification stages & active applications..."):
                audit_res = pipeline.verify_title(
                    proposed_title=prop_title,
                    language=u_lang,
                    periodicity=u_period,
                    state=u_state,
                    district=u_district
                )
                st.session_state.last_audit = audit_res
                st.session_state.last_title = prop_title

            st.divider()

            # Results Display
            col_r1, col_r2, col_r3, col_r4 = st.columns([1.8, 1.2, 1, 1])
            with col_r1:
                st.markdown("<div class='metric-card-lbl'>Official Verdict</div>", unsafe_allow_html=True)
                stat = audit_res["status"]
                if stat == "APPROVED":
                    st.markdown('<div class="status-badge-approved">APPROVED</div>', unsafe_allow_html=True)
                elif stat == "UNDER_REVIEW":
                    st.markdown('<div class="status-badge-review">UNDER REVIEW</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="status-badge-rejected">REJECTED</div>', unsafe_allow_html=True)
                st.caption(audit_res["status_desc"])

            with col_r2:
                prob = audit_res['acceptance_probability']
                g_col = "#2e7d32" if prob >= 70 else "#ed6c02" if prob >= 40 else "#c62828"
                fig_g = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=prob,
                    number={'suffix': "%", 'font': {'size': 24, 'color': g_col}},
                    title={'text': "Approval Probability", 'font': {'size': 13, 'color': "#90a4ae"}},
                    gauge={
                        'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#546e7a"},
                        'bar': {'color': g_col},
                        'bgcolor': "rgba(0,0,0,0)",
                        'borderwidth': 1,
                        'bordercolor': "#37474f",
                        'steps': [
                            {'range': [0, 40], 'color': 'rgba(198, 40, 40, 0.2)'},
                            {'range': [40, 70], 'color': 'rgba(237, 108, 2, 0.2)'},
                            {'range': [70, 100], 'color': 'rgba(46, 125, 50, 0.2)'}
                        ]
                    }
                ))
                fig_g.update_layout(height=140, margin=dict(l=10, r=10, t=25, b=5))
                st.plotly_chart(fig_g, use_container_width=True)

            with col_r3:
                st.markdown(f"""
                <div class="metric-card" style="margin-top: 10px;">
                    <div class="metric-card-lbl">Max Similarity</div>
                    <div class="metric-card-val" style="color: {'#ef5350' if audit_res['highest_similarity'] > 0.75 else '#ffa726' if audit_res['highest_similarity'] > 0.5 else '#66bb6a'};">
                        {audit_res['highest_similarity']*100:.1f}%
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with col_r4:
                st.markdown(f"""
                <div class="metric-card" style="margin-top: 10px;">
                    <div class="metric-card-lbl">Pipeline Latency</div>
                    <div class="metric-card-val">
                        {audit_res['total_latency_ms']} ms
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # Waterfall card
            st.markdown("<br>", unsafe_allow_html=True)
            w1, w2, w3, w4 = st.columns(4)
            st1 = audit_res["stage1_results"]
            st2 = audit_res["stage2_results"]
            cmp_r = audit_res["compliance"]

            with w1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-card-lbl">Stage 1: Phonetic & Fuzzy</div>
                    <div style="font-weight:700; color:{'#ef5350' if st1['flagged'] else '#66bb6a'}; margin: 4px 0;">
                        {'FLAGGED' if st1['flagged'] else 'PASSED'} ({st1['max_score']*100:.1f}%)
                    </div>
                    <div style="font-size:0.75rem; color:#90a4ae;">{st1['time_ms']} ms | Soundex, Metaphone</div>
                </div>
                """, unsafe_allow_html=True)
            with w2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-card-lbl">Stage 2: Multilingual Vector</div>
                    <div style="font-weight:700; color:{'#ef5350' if st2['flagged'] else '#66bb6a'}; margin: 4px 0;">
                        {'FLAGGED' if st2['flagged'] else 'PASSED'} ({st2['max_score']*100:.1f}%)
                    </div>
                    <div style="font-size:0.75rem; color:#90a4ae;">{st2['time_ms']} ms | Cross-Lingual Embeddings</div>
                </div>
                """, unsafe_allow_html=True)
            with w3:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-card-lbl">Stage 3: Graph xAI</div>
                    <div style="font-weight:700; color:#42a5f5; margin: 4px 0;">
                        {len(audit_res['stage3_results']['influential_words'])} Tokens Evaluated
                    </div>
                    <div style="font-size:0.75rem; color:#90a4ae;">SHAP/LIME Token Importance</div>
                </div>
                """, unsafe_allow_html=True)
            with w4:
                vc = len(cmp_r["violations"])
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-card-lbl">Statutory Rules Engine</div>
                    <div style="font-weight:700; color:{'#ef5350' if vc > 0 else '#66bb6a'}; margin: 4px 0;">
                        {f'{vc} VIOLATIONS' if vc > 0 else 'COMPLIANT'}
                    </div>
                    <div style="font-size:0.75rem; color:#90a4ae;">Emblems, Periodicity & Prior Apps</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Details tabs
            dt_graph, dt_xai, dt_cands, dt_alts, dt_rules = st.tabs([
                "Interactive Network Graph",
                "Explainable AI (xAI)",
                "Top Matched Candidates",
                "Smart Title Alternatives",
                "Statutory Compliance Audit"
            ])

            with dt_graph:
                st.subheader("Co-Registration & Semantic Network Graph")
                st.caption("Interactive force-directed graph displaying relationship clusters between the proposed title, existing registered titles, owners, and publication states.")
                g_data = audit_res["stage3_results"]["graph_data"]
                if g_data and g_data.get("nodes"):
                    render_interactive_graph(g_data, prop_title)
                else:
                    st.info("No co-registration graph relationships detected.")

            with dt_xai:
                col_x1, col_x2 = st.columns(2)
                with col_x1:
                    st.subheader("Token Feature Importance (SHAP/LIME style)")
                    inf = audit_res["stage3_results"]["influential_words"]
                    if inf:
                        x_df = pd.DataFrame(inf)
                        fig_b = px.bar(
                            x_df, x="importance", y="word", orientation="h",
                            color="importance", color_continuous_scale="Reds",
                            labels={"importance": "Risk Contribution", "word": "Token in Title"}
                        )
                        fig_b.update_layout(yaxis={'categoryorder':'total ascending'}, height=300, margin=dict(l=20, r=20, t=20, b=20))
                        st.plotly_chart(fig_b, use_container_width=True)
                with col_x2:
                    st.subheader("Attention Weight Distribution")
                    att = audit_res["stage3_results"]["attention_weights"]
                    if att:
                        fig_p = px.pie(names=list(att.keys()), values=list(att.values()), hole=0.45)
                        fig_p.update_layout(height=300, margin=dict(l=20, r=20, t=20, b=20))
                        st.plotly_chart(fig_p, use_container_width=True)

            with dt_cands:
                st.subheader("Top Matching Registered Titles")
                cands = audit_res["top_candidates"]
                if cands:
                    c_tbl = []
                    for c in cands:
                        c_tbl.append({
                            "SN": c["sn"],
                            "Registered Title": c["matched_title"],
                            "Language": c.get("language", ""),
                            "Periodicity": c.get("periodicity", ""),
                            "State": c.get("state", ""),
                            "Owner": c.get("owner", ""),
                            "Similarity Score": f"{c['final_similarity_score']*100:.1f}%",
                            "Soundex Match": "Yes" if c.get("soundex_match") else "No"
                        })
                    st.dataframe(pd.DataFrame(c_tbl), use_container_width=True)
                else:
                    st.success("No similar titles found in the PRGI database.")

            with dt_alts:
                st.subheader("AI-Suggested Compliant Title Variations")
                alts = audit_res.get("smart_alternatives", [])
                if alts:
                    for a in alts:
                        st.markdown(f"""
                        <div class="alt-card">
                            <div class="alt-title">{a['title']}</div>
                            <div class="alt-reason">{a['reason']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.success("The proposed title is distinctive and compliant. Ready for application submission!")

            with dt_rules:
                st.subheader("Statutory Compliance Findings")
                if cmp_r["violations"]:
                    st.error("Violations Detected:")
                    for v in cmp_r["violations"]:
                        st.markdown(f"- **[{v['severity']}] {v['rule']}**: {v['detail']}")
                else:
                    st.success("Passed all statutory compliance checks (Emblems & Names Act, Periodicity Manipulation Rules, Prior Applications).")

    # SUB-TAB 2: Submit Formal Application Form
    with user_tab_apply:
        st.subheader("Submit Official Title Registration Application")
        st.markdown("Complete the formal publisher submission dossier. The system automatically executes a pre-registration audit and forwards the application to the PRGI Registrar Desk.")

        with st.form("publisher_application_form"):
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                app_applicant = st.text_input("Applicant Full Name*", placeholder="e.g. Satyam Pandey")
                app_org = st.text_input("Publishing Entity / Organization*", placeholder="e.g. Awadh Publications Private Limited")
                app_email = st.text_input("Official Email Address*", placeholder="e.g. publisher@awadhmedia.com")
                app_phone = st.text_input("Contact Mobile Number*", placeholder="e.g. +91 98765 43210")

            with col_f2:
                default_sub_title = st.session_state.get("last_title", "Dainik Bharat Samachar")
                app_title = st.text_input("Proposed Publication Title*", value=default_sub_title)
                app_language = st.selectbox("Publication Language*", ["Hindi", "English", "Bengali", "Telugu", "Marathi", "Tamil", "Gujarati", "Urdu", "Kannada", "Oriya", "Malayalam", "Punjabi", "Assamese", "Bilingual", "Multilingual", "Other"])
                app_period = st.selectbox("Periodicity*", ["Daily", "Weekly", "Fortnightly", "Monthly", "Bimonthly", "Quarterly", "Annual", "Other"])
                col_st1, col_st2 = st.columns(2)
                with col_st1:
                    app_state = st.text_input("Publication State*", value="Uttar Pradesh")
                with col_st2:
                    app_district = st.text_input("Publication District*", value="Lucknow")

            submit_app_btn = st.form_submit_button("Submit Application to PRGI Registrar", type="primary", use_container_width=True)

            if submit_app_btn:
                if not app_applicant.strip() or not app_title.strip() or not app_org.strip():
                    st.error("Please fill in all required fields marked with *.")
                else:
                    with st.spinner("Auditing submission and logging application into PRGI Registry..."):
                        sub_audit = pipeline.verify_title(
                            proposed_title=app_title,
                            language=app_language,
                            periodicity=app_period,
                            state=app_state,
                            district=app_district,
                            publisher=app_applicant,
                            owner=app_org
                        )
                        new_app_id = tracker.submit_application(
                            title=app_title,
                            language=app_language,
                            periodicity=app_period,
                            state=app_state,
                            district=app_district,
                            applicant_name=app_applicant,
                            organization=app_org,
                            email=app_email,
                            phone=app_phone,
                            audit_result=sub_audit
                        )
                    st.success(f"Application successfully submitted! Generated Application ID: **{new_app_id}**")
                    st.info(f"Initial AI Audit Probability Score: **{sub_audit['acceptance_probability']}%** ({sub_audit['status']}). Your application is queued for PRGI Registrar review.")

    # SUB-TAB 3: Track Application & Certificate
    with user_tab_track:
        st.subheader("Track Submitted Application Status & Clearance Certificate")
        track_query = st.text_input("Enter your Application ID (e.g. PRGI-2026-A0001) or Title keyword:", placeholder="PRGI-2026-A0001")

        if track_query.strip():
            found_app = tracker.get_application(track_query.strip())
            if found_app:
                st.markdown("### Application Status Dossier")
                col_t1, col_t2, col_t3 = st.columns(3)
                with col_t1:
                    st.markdown(f"**Application ID:** `{found_app['app_id']}`")
                    st.markdown(f"**Proposed Title:** `{found_app['title']}`")
                    st.markdown(f"**Applicant:** {found_app['applicant_name']} ({found_app['organization']})")
                with col_t2:
                    st.markdown(f"**Language / Periodicity:** {found_app['language']} | {found_app['periodicity']}")
                    st.markdown(f"**Jurisdiction:** {found_app['district']}, {found_app['state']}")
                    st.markdown(f"**Submitted At:** {found_app['submission_timestamp']}")
                with col_t3:
                    st_stat = found_app["status"]
                    if st_stat in ["APPROVED", "AUTO_AUDITED_CLEAR"]:
                        st.markdown(f'<div class="status-badge-approved">{st_stat}</div>', unsafe_allow_html=True)
                    elif st_stat in ["PENDING_REVIEW", "UNDER_REVIEW"]:
                        st.markdown(f'<div class="status-badge-review">{st_stat}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="status-badge-rejected">{st_stat}</div>', unsafe_allow_html=True)
                    st.markdown(f"**AI Verification Score:** {found_app['auto_probability']}%")

                if found_app.get("admin_remarks"):
                    st.info(f"**Official Registrar Remarks:** {found_app['admin_remarks']} (Updated: {found_app.get('reviewed_timestamp')})")

                # Generate and download certificate
                if found_app.get("audit_data"):
                    cert_html = generate_verification_certificate(found_app["audit_data"])
                    st.download_button(
                        label="Download Official Verification & Audit Certificate (HTML)",
                        data=cert_html,
                        file_name=f"PRGI_Certificate_{found_app['app_id']}.html",
                        mime="text/html",
                        use_container_width=True
                    )
            else:
                st.warning(f"No application found matching '{track_query}'. Please verify your Application ID.")

    # SUB-TAB 4: Batch CSV Audit
    with user_tab_batch:
        st.subheader("Bulk Title Verification Audit")
        st.markdown("Upload a CSV file containing a column named `title` (optional columns: `language`, `periodicity`, `state`).")
        uploaded_file = st.file_uploader("Upload CSV File", type=["csv"])
        if uploaded_file is not None:
            batch_df = pd.read_csv(uploaded_file)
            st.write("Uploaded Sample Preview:")
            st.dataframe(batch_df.head(5), use_container_width=True)
            if "title" in batch_df.columns:
                if st.button("Run Batch Verification Audit", type="primary"):
                    p_bar = st.progress(0)
                    batch_res = []
                    total = len(batch_df)
                    for idx, row in batch_df.iterrows():
                        t = str(row["title"])
                        res = pipeline.verify_title(t, language=str(row.get("language", "")), periodicity=str(row.get("periodicity", "")), state=str(row.get("state", "")))
                        batch_res.append({
                            "Title": t,
                            "Status": res["status"],
                            "Approval Probability (%)": res["acceptance_probability"],
                            "Highest Similarity (%)": f"{res['highest_similarity']*100:.1f}",
                            "Top Matched Title": res["top_candidates"][0]["matched_title"] if res["top_candidates"] else "None",
                            "Violations Count": len(res["compliance"]["violations"])
                        })
                        p_bar.progress((idx + 1) / total)
                    res_df = pd.DataFrame(batch_res)
                    st.success(f"Audit Complete: Successfully verified {len(res_df)} titles.")
                    col_b1, col_b2 = st.columns([1, 2])
                    with col_b1:
                        st_counts = res_df["Status"].value_counts().reset_index()
                        st_counts.columns = ["Status", "Count"]
                        fig_b_pie = px.pie(st_counts, names="Status", values="Count", color="Status", color_discrete_map={"APPROVED": "#2e7d32", "UNDER_REVIEW": "#ed6c02", "REJECTED": "#c62828"}, hole=0.45)
                        st.plotly_chart(fig_b_pie, use_container_width=True)
                    with col_b2:
                        st.dataframe(res_df, use_container_width=True)

    # SUB-TAB 5: Statutory Guidelines
    with user_tab_guidelines:
        st.subheader("PRGI Statutory Verification Guidelines")
        st.markdown("""
        ### Key Statutory Registration Principles
        1. **Uniqueness & Non-Deceptiveness**: The proposed title must not be identical or deceptively similar to any existing registered newspaper or periodical title. Phonetic variations (e.g. *Khabar* vs *Khabbar*) are strictly disallowed.
        2. **Disallowed Words (Requirement 3a & 3b)**: Titles containing protected national keywords (*Police*, *Crime*, *Corruption*, *CBI*, *CID*, *Army*, *Rashtrapati*, *Supreme Court*, *Parliament*) are prohibited.
        3. **Combined Existing Titles Disallowance (Requirement 3c)**: Combining two existing registered titles into a new title (e.g. *Hindu* + *Indian Express* $\rightarrow$ *Hindu Indian Express*) is strictly rejected.
        4. **Periodicity Prefix/Suffix Manipulation (Requirement 3e)**: Merely adding or omitting periodicity terms (e.g. *Daily*, *Weekly*, *Monthly*, *Dainik*, *Saptahik*) to an existing title is invalid.
        5. **Prior Application Conflict (Requirement 5b)**: Submitting a title identical or closely resembling an active pending/approved application submitted earlier by another user will be rejected.
        """)

# ==============================================================================
# MODE 2: PRGI OFFICIAL & REGISTRAR ADMIN PORTAL
# ==============================================================================
else:
    admin_tab_queue, admin_tab_analytics, admin_tab_explorer = st.tabs([
        "Registrar Application Queue & Decision Desk",
        "National PRGI Database Analytics",
        "Database Explorer"
    ])

    # ADMIN TAB 1: Registrar Review & Decision Desk
    with admin_tab_queue:
        st.subheader("PRGI Official Verification & Title Registration Desk")
        st.caption("Review live publisher applications, inspect automated 3-stage AI similarity audit dossiers, and issue official registrar determinations.")

        apps_list = tracker.get_all_applications()
        if not apps_list:
            st.info("No applications currently logged in the registry.")
        else:
            # Metrics top bar
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            total_apps = len(apps_list)
            pending_apps = len([a for a in apps_list if a["status"] in ["PENDING_REVIEW", "AUTO_AUDITED_CLEAR"]])
            approved_apps = len([a for a in apps_list if a["status"] == "APPROVED"])
            rejected_apps = len([a for a in apps_list if a["status"] in ["REJECTED", "MODIFICATION_REQUESTED"]])

            with m_col1:
                st.markdown(f"<div class='metric-card'><div class='metric-card-lbl'>Total Submissions</div><div class='metric-card-val'>{total_apps}</div></div>", unsafe_allow_html=True)
            with m_col2:
                st.markdown(f"<div class='metric-card'><div class='metric-card-lbl'>Pending Review</div><div class='metric-card-val' style='color:#ffa726;'>{pending_apps}</div></div>", unsafe_allow_html=True)
            with m_col3:
                st.markdown(f"<div class='metric-card'><div class='metric-card-lbl'>Admin Approved</div><div class='metric-card-val' style='color:#66bb6a;'>{approved_apps}</div></div>", unsafe_allow_html=True)
            with m_col4:
                st.markdown(f"<div class='metric-card'><div class='metric-card-lbl'>Rejected / Changes</div><div class='metric-card-val' style='color:#ef5350;'>{rejected_apps}</div></div>", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            
            # Select Application
            app_options = [f"{a['app_id']} | '{a['title']}' | {a['applicant_name']} | Status: {a['status']}" for a in apps_list]
            selected_app_str = st.selectbox("Select Application Dossier to Review:", app_options)
            selected_app_id = selected_app_str.split(" | ")[0]
            selected_app = tracker.get_application(selected_app_id)

            if selected_app:
                st.markdown(f'<div class="review-dossier">', unsafe_allow_html=True)
                st.markdown(f"### Application Dossier: `{selected_app['app_id']}`")
                
                col_d1, col_d2, col_d3 = st.columns(3)
                with col_d1:
                    st.markdown(f"**Proposed Title:** `{selected_app['title']}`")
                    st.markdown(f"**Language:** {selected_app['language']}")
                    st.markdown(f"**Periodicity:** {selected_app['periodicity']}")
                with col_d2:
                    st.markdown(f"**Applicant Name:** {selected_app['applicant_name']}")
                    st.markdown(f"**Organization:** {selected_app['organization']}")
                    st.markdown(f"**Jurisdiction:** {selected_app['district']}, {selected_app['state']}")
                with col_d3:
                    st.markdown(f"**Submitted At:** {selected_app['submission_timestamp']}")
                    st.markdown(f"**AI Verification Score:** {selected_app['auto_probability']}%")
                    st.markdown(f"**Current Status:** `{selected_app['status']}`")

                # AI Audit Details
                audit_info = selected_app.get("audit_data", {})
                if audit_info:
                    st.markdown("---")
                    st.markdown("##### Automated AI Verification Findings")
                    c_viol = audit_info.get("compliance", {}).get("violations", [])
                    if c_viol:
                        st.error("🚨 **Statutory Violations Detected:**")
                        for v in c_viol:
                            st.markdown(f"- **[{v.get('severity')}] {v.get('rule')}:** {v.get('detail')}")
                    else:
                        st.success("✅ Clean AI Audit: Passed phonetic, semantic, combined titles, and Emblems Act checks.")

                    top_cands = audit_info.get("top_candidates", [])
                    if top_cands:
                        st.markdown("**Nearest Registered Matches in PRGI Database:**")
                        for c in top_cands[:3]:
                            st.markdown(f"- SN {c.get('sn')}: **'{c.get('matched_title')}'** ({c.get('language')}, {c.get('state')}) $\\rightarrow$ **Similarity: {c.get('final_similarity_score',0)*100:.1f}%**")

                st.markdown('</div>', unsafe_allow_html=True)

                # Official Registrar Action Panel
                st.markdown(f'<div class="action-panel">', unsafe_allow_html=True)
                st.markdown("### Official Registrar Action & Determination")
                
                with st.form("registrar_action_form"):
                    action_choice = st.radio(
                        "Official Determination*",
                        ["APPROVE TITLE REGISTRATION", "REJECT APPLICATION", "REQUEST TITLE MODIFICATION"],
                        horizontal=True
                    )
                    action_remarks = st.text_area(
                        "Registrar Official Remarks / Compliance Orders*",
                        placeholder="Enter the official reason for approval/rejection or specific instructions for modification..."
                    )
                    
                    submit_decision = st.form_submit_button("Submit Official Registrar Decision", type="primary", use_container_width=True)

                    if submit_decision:
                        new_stat = "APPROVED" if action_choice == "APPROVE TITLE REGISTRATION" else "REJECTED" if action_choice == "REJECT APPLICATION" else "MODIFICATION_REQUESTED"
                        updated = tracker.update_application_status(selected_app_id, new_stat, action_remarks)
                        if updated:
                            st.success(f"Determination submitted successfully! Application `{selected_app_id}` status updated to **{new_stat}**.")
                            time.sleep(1)
                            st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

    # ADMIN TAB 2: National Database Analytics
    with admin_tab_analytics:
        st.subheader("National PRGI Database Analytics & Insights")
        st.caption(f"Statistical distribution across {len(loader.df):,} officially registered publications in India.")
        
        col_an1, col_an2 = st.columns(2)
        with col_an1:
            st.markdown("##### Top 10 Publication Languages")
            lang_c = loader.df["language"].fillna("Unknown").value_counts().head(10).reset_index()
            lang_c.columns = ["Language", "Count"]
            fig_l = px.bar(lang_c, x="Count", y="Language", orientation="h", color="Count", color_continuous_scale="Blues")
            fig_l.update_layout(yaxis={'categoryorder':'total ascending'}, height=340, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig_l, use_container_width=True)

        with col_an2:
            st.markdown("##### Periodicity Distribution")
            per_c = loader.df["periodicity"].fillna("Unknown").value_counts().head(8).reset_index()
            per_c.columns = ["Periodicity", "Count"]
            fig_per = px.pie(per_c, names="Periodicity", values="Count", hole=0.45)
            fig_per.update_layout(height=340, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig_per, use_container_width=True)

        col_an3, col_an4 = st.columns(2)
        with col_an3:
            st.markdown("##### Top 10 Publication States")
            st_c = loader.df["publication_state"].fillna("Unknown").value_counts().head(10).reset_index()
            st_c.columns = ["State", "Count"]
            fig_s = px.bar(st_c, x="Count", y="State", orientation="h", color="Count", color_continuous_scale="Teal")
            fig_s.update_layout(yaxis={'categoryorder':'total ascending'}, height=340, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig_s, use_container_width=True)

        with col_an4:
            st.markdown("##### High-Frequency Lexical Keywords in Indian Titles")
            top_w = loader.titles
            w_list = []
            for t in top_w[:5000]:
                w_list.extend([w for w in t.split() if len(w) > 3])
            w_counts = Counter(w_list).most_common(10)
            w_df = pd.DataFrame(w_counts, columns=["Keyword", "Frequency"])
            fig_kw = px.bar(w_df, x="Frequency", y="Keyword", orientation="h", color="Frequency", color_continuous_scale="Viridis")
            fig_kw.update_layout(yaxis={'categoryorder':'total ascending'}, height=340, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig_kw, use_container_width=True)

    # ADMIN TAB 3: Database Explorer
    with admin_tab_explorer:
        st.subheader("Registered PRGI Database Explorer")
        s_query = st.text_input("Search registered database by title keyword, registration number, or owner name:")
        if s_query.strip():
            sq = s_query.strip().upper()
            filtered = loader.df[
                loader.df["clean_title"].str.contains(sq, na=False) |
                loader.df["owner"].fillna("").astype(str).str.upper().str.contains(sq, na=False) |
                loader.df["registration_number"].fillna("").astype(str).str.upper().str.contains(sq, na=False)
            ]
            st.write(f"Found {len(filtered)} matching records:")
            st.dataframe(filtered[["sn", "title", "registration_number", "registration_date", "language", "periodicity", "publisher", "owner", "publication_state", "publication_district"]].head(100), use_container_width=True)
        else:
            st.dataframe(loader.df[["sn", "title", "registration_number", "registration_date", "language", "periodicity", "publisher", "owner", "publication_state", "publication_district"]].head(50), use_container_width=True)

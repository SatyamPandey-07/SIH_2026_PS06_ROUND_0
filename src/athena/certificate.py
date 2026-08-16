import datetime
import hashlib

def generate_verification_certificate(result: dict) -> str:
    """
    Generates a formal, printable HTML PRGI Title Verification Certificate & Audit Summary.
    """
    timestamp = datetime.datetime.now().strftime("%d-%b-%Y %H:%M:%S UTC")
    title = result.get("proposed_title", "N/A")
    status = result.get("status", "UNDER_REVIEW")
    prob = result.get("acceptance_probability", 0.0)
    latency = result.get("total_latency_ms", 0.0)
    highest_sim = result.get("highest_similarity", 0.0) * 100.0
    
    # Generate unique verification hash
    raw_hash_str = f"{title}_{status}_{prob}_{timestamp}"
    cert_hash = hashlib.sha256(raw_hash_str.encode()).hexdigest()[:16].upper()
    
    status_color = "#2e7d32" if status == "APPROVED" else "#ed6c02" if status == "UNDER_REVIEW" else "#c62828"
    status_text = "PASSED - COMPLIANT" if status == "APPROVED" else "REQUIRES MANUAL REVIEW" if status == "UNDER_REVIEW" else "FAILED - NON-COMPLIANT"

    violations_html = ""
    violations = result.get("compliance", {}).get("violations", [])
    if violations:
        violations_html = "<ul>" + "".join([f"<li><strong style='color:#c62828;'>[{v.get('severity')}] {v.get('rule')}:</strong> {v.get('detail')}</li>" for v in violations]) + "</ul>"
    else:
        violations_html = "<p style='color:#2e7d32; font-weight:600;'>No statutory or guideline violations detected.</p>"

    candidates_rows = ""
    for c in result.get("top_candidates", [])[:5]:
        candidates_rows += f"""
        <tr>
            <td style='padding:6px; border:1px solid #e0e0e0;'>{c.get('sn')}</td>
            <td style='padding:6px; border:1px solid #e0e0e0;'>{c.get('matched_title')}</td>
            <td style='padding:6px; border:1px solid #e0e0e0;'>{c.get('language','-')}</td>
            <td style='padding:6px; border:1px solid #e0e0e0;'>{c.get('state','-')}</td>
            <td style='padding:6px; border:1px solid #e0e0e0; font-weight:bold;'>{c.get('final_similarity_score',0)*100:.1f}%</td>
        </tr>
        """

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>PRGI Title Verification Certificate - {title}</title>
<style>
    body {{
        font-family: 'Segoe UI', Arial, sans-serif;
        background-color: #f4f6f9;
        margin: 0;
        padding: 24px;
        color: #212529;
    }}
    .cert-container {{
        max-width: 800px;
        margin: 0 auto;
        background: #ffffff;
        border: 2px solid #1a237e;
        border-radius: 8px;
        padding: 32px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.1);
    }}
    .cert-header {{
        text-align: center;
        border-bottom: 2px solid #1a237e;
        padding-bottom: 16px;
        margin-bottom: 24px;
    }}
    .gov-title {{
        font-size: 14px;
        font-weight: 700;
        letter-spacing: 1px;
        color: #455a64;
        text-transform: uppercase;
    }}
    .cert-title {{
        font-size: 22px;
        font-weight: 800;
        color: #1a237e;
        margin: 8px 0;
    }}
    .cert-id {{
        font-size: 12px;
        color: #78909c;
        font-family: monospace;
    }}
    .status-box {{
        background-color: {status_color};
        color: #ffffff;
        padding: 12px;
        text-align: center;
        border-radius: 6px;
        font-size: 18px;
        font-weight: bold;
        letter-spacing: 1px;
        margin-bottom: 24px;
    }}
    .section-title {{
        font-size: 14px;
        font-weight: 700;
        color: #1a237e;
        border-bottom: 1px solid #cfd8dc;
        padding-bottom: 4px;
        margin-top: 20px;
        margin-bottom: 12px;
        text-transform: uppercase;
    }}
    .meta-grid {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
        font-size: 14px;
    }}
    .meta-item {{
        background: #f8f9fa;
        padding: 8px 12px;
        border-radius: 4px;
        border-left: 3px solid #1a237e;
    }}
    table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
        margin-top: 8px;
    }}
    th {{
        background: #eceff1;
        padding: 8px;
        border: 1px solid #cfd8dc;
        text-align: left;
    }}
    .cert-footer {{
        margin-top: 32px;
        border-top: 1px dashed #cfd8dc;
        padding-top: 16px;
        font-size: 11px;
        color: #78909c;
        display: flex;
        justify-content: space-between;
    }}
</style>
</head>
<body>
<div class="cert-container">
    <div class="cert-header">
        <div class="gov-title">Press Registrar General of India (PRGI)</div>
        <div class="cert-title">Automated Title Verification & Compliance Audit Certificate</div>
        <div class="cert-id">Verification Hash: PRGI-ATHENA-{cert_hash} | Timestamp: {timestamp}</div>
    </div>

    <div class="status-box">
        VERDICT: {status} ({status_text})
    </div>

    <div class="section-title">1. Submission & Verification Summary</div>
    <div class="meta-grid">
        <div class="meta-item"><strong>Proposed Title:</strong> {title}</div>
        <div class="meta-item"><strong>Approval Probability:</strong> {prob}%</div>
        <div class="meta-item"><strong>Max Similarity Score:</strong> {highest_sim:.1f}%</div>
        <div class="meta-item"><strong>Audit Engine Latency:</strong> {latency} ms</div>
    </div>

    <div class="section-title">2. Statutory Compliance Audit</div>
    {violations_html}

    <div class="section-title">3. Nearest Registered Title Candidates</div>
    <table>
        <thead>
            <tr>
                <th>SN</th>
                <th>Registered Title</th>
                <th>Language</th>
                <th>State</th>
                <th>Similarity</th>
            </tr>
        </thead>
        <tbody>
            {candidates_rows if candidates_rows else "<tr><td colspan='5' style='text-align:center; padding:12px;'>No close collisions found in PRGI database.</td></tr>"}
        </tbody>
    </table>

    <div class="cert-footer">
        <div>System: Athena PRGI Verification Engine (3-Stage Multimodal AI)</div>
        <div>Digitally Generated & Verified</div>
    </div>
</div>
</body>
</html>
"""
    return html

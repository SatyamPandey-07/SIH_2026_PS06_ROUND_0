import React, { useState, useEffect, useRef } from "react";
import {
  Shield, Zap, CheckCircle2, AlertTriangle, XCircle, Search,
  FileText, Download, BarChart2, Database, LayoutDashboard,
  Building, User, Mail, Phone, ArrowRight, RefreshCw, Eye
} from "lucide-react";
import {
  verifyTitle, listApplications, submitApplication, submitDecision,
  getAnalytics, searchExplorer, flagDerogatoryTerm
} from "./api";
import type { VerifyResult, Application, AnalyticsData, ExplorerRecord } from "./api";
import { NetworkGraph } from "./components/NetworkGraph";
import { SimpleBarChart } from "./components/SimpleBarChart";
import { SimplePieChart } from "./components/SimplePieChart";

const PRESETS = [
  { label: "1. Direct Collision", title: "A &S INDIA", language: "English", periodicity: "Monthly", state: "Maharashtra" },
  { label: "2. Deceptive Phonetic", title: "Dainik Khabbar", language: "Hindi", periodicity: "Daily", state: "Madhya Pradesh" },
  { label: "3. Combined Titles", title: "Hindu Indian Express", language: "English", periodicity: "Daily", state: "Delhi" },
  { label: "4. Prohibited Word", title: "Police Crime Branch Times", language: "English", periodicity: "Weekly", state: "Delhi" },
  { label: "5. Compliant Novel", title: "Vindhya Innovation Chronicle", language: "English", periodicity: "Monthly", state: "Madhya Pradesh" },
];

export default function App() {
  // Mode & Tabs
  const [portalMode, setPortalMode] = useState<"applicant" | "admin">("applicant");
  const [applicantTab, setApplicantTab] = useState<"verify" | "submit" | "track" | "batch" | "rules">("verify");
  const [adminTab, setAdminTab] = useState<"queue" | "analytics" | "explorer">("queue");

  // Form State
  const [title, setTitle] = useState("Dainik Bharat Samachar");
  const [language, setLanguage] = useState("Hindi");
  const [periodicity, setPeriodicity] = useState("Daily");
  const [state, setState] = useState("Uttar Pradesh");
  const [district, setDistrict] = useState("Lucknow");

  // Verification State
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<VerifyResult | null>(null);
  const [error, setError] = useState("");
  const resultsRef = useRef<HTMLDivElement>(null);

  // Detail Sub-Tab in Verification Results
  const [verifyDetailTab, setVerifyDetailTab] = useState<"graph" | "xai" | "candidates" | "alternatives" | "compliance">("graph");

  // Application Submission Form State
  const [subApplicant, setSubApplicant] = useState("Satyam Pandey");
  const [subOrg, setSubOrg] = useState("Awadh Media Publications");
  const [subEmail, setSubEmail] = useState("publisher@awadhmedia.com");
  const [subPhone, setSubPhone] = useState("+91 98765 43210");
  const [subSuccessMsg, setSubSuccessMsg] = useState("");
  const [subLoading, setSubLoading] = useState(false);

  // Application Tracking State
  const [trackQuery, setTrackQuery] = useState("");
  const [trackedApp, setTrackedApp] = useState<Application | null>(null);
  const [trackError, setTrackError] = useState("");

  // Admin Queue State
  const [applications, setApplications] = useState<Application[]>([]);
  const [selectedAppId, setSelectedAppId] = useState<string>("");
  const [decisionChoice, setDecisionChoice] = useState<"APPROVED" | "REJECTED" | "MODIFICATION_REQUESTED">("APPROVED");
  const [decisionRemarks, setDecisionRemarks] = useState("");
  const [decisionMsg, setDecisionMsg] = useState("");
  const [adminLoading, setAdminLoading] = useState(false);

  // Analytics State
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [analyticsLoading, setAnalyticsLoading] = useState(false);

  // Database Explorer State
  const [searchQuery, setSearchQuery] = useState("");
  const [explorerRecords, setExplorerRecords] = useState<ExplorerRecord[]>([]);
  const [explorerLoading, setExplorerLoading] = useState(false);

  // Load applications list and analytics on mode switch
  useEffect(() => {
    fetchApplications();
    if (portalMode === "admin" && adminTab === "analytics") {
      fetchAnalytics();
    }
    if (portalMode === "admin" && adminTab === "explorer") {
      fetchExplorer("");
    }
  }, [portalMode, adminTab]);

  const fetchApplications = async () => {
    try {
      const data = await listApplications();
      setApplications(data);
      if (data.length > 0 && !selectedAppId) {
        setSelectedAppId(data[0].app_id);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchAnalytics = async () => {
    setAnalyticsLoading(true);
    try {
      const data = await getAnalytics();
      setAnalytics(data);
    } catch (e) {
      console.error(e);
    } finally {
      setAnalyticsLoading(false);
    }
  };

  const fetchExplorer = async (q: string) => {
    setExplorerLoading(true);
    try {
      const res = await searchExplorer(q);
      setExplorerRecords(res.records);
    } catch (e) {
      console.error(e);
    } finally {
      setExplorerLoading(false);
    }
  };

  const handleVerify = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!title.trim()) return;

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const data = await verifyTitle({ title, language, periodicity, state, district });
      setResult(data);
      setTimeout(() => {
        resultsRef.current?.scrollIntoView({ behavior: "smooth" });
      }, 100);
    } catch (err: any) {
      setError(err.message || "Failed to connect to verification server.");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitApplication = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubLoading(true);
    setSubSuccessMsg("");
    try {
      const res = await submitApplication({
        title, language, periodicity, state, district,
        applicant_name: subApplicant, organization: subOrg, email: subEmail, phone: subPhone
      });
      setSubSuccessMsg(`Application Submitted! Assigned ID: ${res.app_id}. Status: ${res.status} (${res.auto_probability}% acceptance probability).`);
      fetchApplications();
    } catch (e: any) {
      alert("Submission error: " + e.message);
    } finally {
      setSubLoading(false);
    }
  };

  const handleTrackSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setTrackError("");
    setTrackedApp(null);
    const found = applications.find(a =>
      a.app_id.toLowerCase() === trackQuery.trim().toLowerCase() ||
      a.title.toLowerCase().includes(trackQuery.trim().toLowerCase())
    );
    if (found) {
      setTrackedApp(found);
    } else {
      setTrackError(`No application matching '${trackQuery}' found in registry.`);
    }
  };

  const handleAdminDecisionSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedAppId) return;
    setAdminLoading(true);
    setDecisionMsg("");
    try {
      await submitDecision(selectedAppId, decisionChoice, decisionRemarks);
      setDecisionMsg(`Successfully recorded determination (${decisionChoice}) for application ${selectedAppId}`);
      setDecisionRemarks("");
      fetchApplications();
    } catch (e: any) {
      alert("Error saving decision: " + e.message);
    } finally {
      setAdminLoading(false);
    }
  };

  const handleFlagDerogatory = async (termToFlag?: string) => {
    const term = termToFlag || prompt("Enter derogatory or offensive term to flag for Stage 0 Shield:");
    if (!term || !term.trim()) return;
    try {
      const res = await flagDerogatoryTerm(term.trim());
      alert(`🛡️ [STAGE 0 SHIELD UPDATE]\n\n${res.message}`);
    } catch (err: any) {
      alert("Failed to flag term: " + err.message);
    }
  };

  const pendingAppsCount = applications.filter(a => a.status === "PENDING_REVIEW" || a.status === "UNDER_REVIEW" || a.status === "AUTO_AUDITED_CLEAR").length;
  const selectedApp = applications.find(a => a.app_id === selectedAppId);

  return (
    <div style={{ minHeight: "100vh", background: "var(--color-bg)" }}>
      {/* Header Bar with Role Switcher & Live Stats */}
      <header style={{ borderBottom: "1px solid var(--color-hairline)", background: "var(--color-surface)", position: "sticky", top: 0, zIndex: 50 }}>
        <div style={{ maxWidth: 1200, margin: "0 auto", padding: "16px 24px", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 16 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <div style={{ background: "var(--color-ink)", color: "#fff", padding: "8px 12px", borderRadius: "var(--radius-md)", fontWeight: 700, fontSize: "16px" }}>
              ATHENA
            </div>
            <div>
              <h1 style={{ fontSize: 18, fontWeight: 700, margin: 0, letterSpacing: "-0.02em" }}>PRGI AI Title Verification System</h1>
              <p className="caption" style={{ margin: 0 }}>Press Registrar General of India Title Verification & Administrative Desk</p>
            </div>
          </div>

          {/* Mode Switcher */}
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            <div style={{ display: "flex", background: "var(--color-surface-card)", padding: 4, borderRadius: "var(--radius-md)", border: "1px solid var(--color-hairline)" }}>
              <button
                onClick={() => setPortalMode("applicant")}
                className={`button ${portalMode === "applicant" ? "button-primary" : "button-secondary"}`}
                style={{ padding: "6px 14px", fontSize: 13 }}
              >
                Publisher Portal
              </button>
              <button
                onClick={() => setPortalMode("admin")}
                className={`button ${portalMode === "admin" ? "button-primary" : "button-secondary"}`}
                style={{ padding: "6px 14px", fontSize: 13 }}
              >
                Registrar Admin Desk
              </button>
            </div>

            <div style={{ display: "flex", gap: 8, fontSize: 12, fontWeight: 600, alignItems: "center" }}>
              <button
                onClick={() => handleFlagDerogatory()}
                className="button button-secondary"
                style={{ padding: "6px 12px", fontSize: 12, color: "#dc2626", borderColor: "#fca5a5" }}
                title="Stage 0 Shield: Add new derogatory term with automatic fuzzy expansion"
              >
                <AlertTriangle size={14} style={{ marginRight: 4 }} /> Flag Offensive Term
              </button>
              <span className="badge badge-neutral">82,730 Registered</span>
              <span className="badge badge-review">{pendingAppsCount} Pending Review</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main style={{ maxWidth: 1200, margin: "0 auto", padding: "24px" }}>
        
        {/* ========================================================================= */}
        {/* MODE 1: PUBLISHER / APPLICANT PORTAL                                      */}
        {/* ========================================================================= */}
        {portalMode === "applicant" && (
          <div>
            {/* Top Navigation Tabs */}
            <div style={{ display: "flex", gap: 8, borderBottom: "1px solid var(--color-hairline)", marginBottom: 24, flexWrap: "wrap" }}>
              <button
                onClick={() => setApplicantTab("verify")}
                style={{ padding: "10px 16px", borderBottom: applicantTab === "verify" ? "2px solid var(--color-ink)" : "2px solid transparent", fontWeight: 600, fontSize: 14, background: "none", cursor: "pointer" }}
              >
                Live Title Verification
              </button>
              <button
                onClick={() => setApplicantTab("submit")}
                style={{ padding: "10px 16px", borderBottom: applicantTab === "submit" ? "2px solid var(--color-ink)" : "2px solid transparent", fontWeight: 600, fontSize: 14, background: "none", cursor: "pointer" }}
              >
                Submit Application
              </button>
              <button
                onClick={() => setApplicantTab("track")}
                style={{ padding: "10px 16px", borderBottom: applicantTab === "track" ? "2px solid var(--color-ink)" : "2px solid transparent", fontWeight: 600, fontSize: 14, background: "none", cursor: "pointer" }}
              >
                Track & Certificate
              </button>
              <button
                onClick={() => setApplicantTab("rules")}
                style={{ padding: "10px 16px", borderBottom: applicantTab === "rules" ? "2px solid var(--color-ink)" : "2px solid transparent", fontWeight: 600, fontSize: 14, background: "none", cursor: "pointer" }}
              >
                Statutory Rules & Guidelines
              </button>
            </div>

            {/* TAB 1: Live Verification */}
            {applicantTab === "verify" && (
              <div>
                <div style={{ marginBottom: 20 }}>
                  <div className="caption" style={{ marginBottom: 8, textTransform: "uppercase", letterSpacing: "0.05em", fontWeight: 600 }}>Quick Evaluation Presets</div>
                  <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                    {PRESETS.map((p, idx) => (
                      <button
                        key={idx}
                        onClick={() => {
                          setTitle(p.title);
                          setLanguage(p.language);
                          setPeriodicity(p.periodicity);
                          setState(p.state);
                        }}
                        className="button button-secondary"
                        style={{ fontSize: 12, padding: "6px 12px" }}
                      >
                        {p.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Input Card */}
                <div className="card" style={{ padding: 24, marginBottom: 32 }}>
                  <form onSubmit={handleVerify}>
                    <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 16, marginBottom: 16 }}>
                      <div>
                        <label className="caption" style={{ fontWeight: 600, display: "block", marginBottom: 6 }}>Proposed Publication Title *</label>
                        <input
                          type="text"
                          className="input"
                          value={title}
                          onChange={(e) => setTitle(e.target.value)}
                          placeholder="e.g. Dainik Bharat Samachar"
                        />
                      </div>
                      <div>
                        <label className="caption" style={{ fontWeight: 600, display: "block", marginBottom: 6 }}>Language *</label>
                        <select className="input" value={language} onChange={(e) => setLanguage(e.target.value)}>
                          {["Hindi", "English", "Bengali", "Telugu", "Marathi", "Tamil", "Gujarati", "Urdu", "Kannada", "Oriya", "Malayalam", "Punjabi"].map(l => (
                            <option key={l} value={l}>{l}</option>
                          ))}
                        </select>
                      </div>
                    </div>

                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16, marginBottom: 24 }}>
                      <div>
                        <label className="caption" style={{ fontWeight: 600, display: "block", marginBottom: 6 }}>Periodicity *</label>
                        <select className="input" value={periodicity} onChange={(e) => setPeriodicity(e.target.value)}>
                          {["Daily", "Weekly", "Fortnightly", "Monthly", "Bimonthly", "Quarterly", "Annual"].map(p => (
                            <option key={p} value={p}>{p}</option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label className="caption" style={{ fontWeight: 600, display: "block", marginBottom: 6 }}>Publication State</label>
                        <input type="text" className="input" value={state} onChange={(e) => setState(e.target.value)} placeholder="e.g. Uttar Pradesh" />
                      </div>
                      <div>
                        <label className="caption" style={{ fontWeight: 600, display: "block", marginBottom: 6 }}>Publication District</label>
                        <input type="text" className="input" value={district} onChange={(e) => setDistrict(e.target.value)} placeholder="e.g. Lucknow" />
                      </div>
                    </div>

                    <button type="submit" className="button button-primary" style={{ width: "100%", padding: "12px 24px", fontSize: 15 }} disabled={loading}>
                      {loading ? (
                        <>
                          <RefreshCw style={{ animation: "spin 1s linear infinite", marginRight: 8 }} size={16} />
                          Running 3-Stage AI Verification Pipeline...
                        </>
                      ) : (
                        "Run Verification Analysis"
                      )}
                    </button>
                  </form>
                </div>

                {error && (
                  <div className="card" style={{ borderLeft: "4px solid #ef4444", padding: 16, marginBottom: 24, background: "#fef2f2" }}>
                    <div style={{ fontWeight: 600, color: "#991b1b" }}>Verification Error</div>
                    <p style={{ margin: "4px 0 0", fontSize: 14, color: "#7f1d1d" }}>{error}</p>
                  </div>
                )}

                {/* VERIFICATION RESULTS PANEL */}
                {result && (
                  <div ref={resultsRef} style={{ display: "flex", flexDirection: "column", gap: 24 }}>
                    {/* Top KPI Cards */}
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 16 }}>
                      
                      <div className="card" style={{ padding: 20 }}>
                        <div className="caption" style={{ marginBottom: 4 }}>Verdict</div>
                        {result.status === "APPROVED" && <span className="badge badge-approved" style={{ fontSize: 16, padding: "6px 14px" }}>APPROVED</span>}
                        {result.status === "UNDER_REVIEW" && <span className="badge badge-review" style={{ fontSize: 16, padding: "6px 14px" }}>UNDER REVIEW</span>}
                        {result.status === "REJECTED" && <span className="badge badge-rejected" style={{ fontSize: 16, padding: "6px 14px" }}>REJECTED</span>}
                        <p style={{ margin: "8px 0 0", fontSize: 13, color: "var(--color-muted)" }}>{result.status_desc}</p>
                      </div>

                      <div className="card" style={{ padding: 20, textAlign: "center" }}>
                        <div className="caption">Acceptance Probability</div>
                        <div style={{ fontSize: 32, fontWeight: 800, marginTop: 4, color: result.acceptance_probability >= 70 ? "#10b981" : result.acceptance_probability >= 40 ? "#f59e0b" : "#ef4444" }}>
                          {result.acceptance_probability}%
                        </div>
                      </div>

                      <div className="card" style={{ padding: 20, textAlign: "center" }}>
                        <div className="caption">Highest Database Similarity</div>
                        <div style={{ fontSize: 32, fontWeight: 800, marginTop: 4, color: result.highest_similarity > 0.75 ? "#ef4444" : result.highest_similarity > 0.5 ? "#f59e0b" : "#10b981" }}>
                          {(result.highest_similarity * 100).toFixed(1)}%
                        </div>
                      </div>

                      <div className="card" style={{ padding: 20, textAlign: "center" }}>
                        <div className="caption">Pipeline Latency</div>
                        <div style={{ fontSize: 32, fontWeight: 800, marginTop: 4 }}>
                          {result.total_latency_ms} ms
                        </div>
                      </div>
                    </div>

                    {/* Waterfall 4-Stage Pipeline Card */}
                    <div className="card" style={{ padding: 20 }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
                        <h3 style={{ fontSize: 16, fontWeight: 700, margin: 0 }}>4-Stage Verification Pipeline Execution</h3>
                        <button
                          onClick={() => handleFlagDerogatory()}
                          className="button button-secondary"
                          style={{ padding: "4px 10px", fontSize: 12, color: "#dc2626", borderColor: "#fca5a5" }}
                        >
                          + Flag Offensive Term
                        </button>
                      </div>
                      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 16 }}>
                        <div style={{ padding: 12, background: result.stage0?.flagged ? "#fef2f2" : "var(--color-surface-card)", borderRadius: "var(--radius-md)", border: result.stage0?.flagged ? "1px solid #fca5a5" : "1px solid var(--color-hairline)" }}>
                          <div className="caption" style={{ fontWeight: 600 }}>Stage 0: Derogatory Shield</div>
                          <div style={{ fontWeight: 700, marginTop: 4, color: result.stage0?.flagged ? "#ef4444" : "#10b981" }}>
                            {result.stage0?.flagged ? "VIOLATION DETECTED" : "CLEARED"} ({((result.stage0?.confidence_score || 0) * 100).toFixed(0)}%)
                          </div>
                          <div className="caption" style={{ marginTop: 4 }}>{result.stage0?.time_ms || 0} ms | Seed + Fuzzy</div>
                        </div>

                        <div style={{ padding: 12, background: "var(--color-surface-card)", borderRadius: "var(--radius-md)", border: "1px solid var(--color-hairline)" }}>
                          <div className="caption" style={{ fontWeight: 600 }}>Stage 1: Phonetic & Fuzzy</div>
                          <div style={{ fontWeight: 700, marginTop: 4, color: result.stage1.flagged ? "#ef4444" : "#10b981" }}>
                            {result.stage1.flagged ? "FLAGGED" : "PASSED"} ({(result.stage1.max_score * 100).toFixed(1)}%)
                          </div>
                          <div className="caption" style={{ marginTop: 4 }}>{result.stage1.time_ms} ms | Soundex/Metaphone</div>
                        </div>

                        <div style={{ padding: 12, background: "var(--color-surface-card)", borderRadius: "var(--radius-md)", border: "1px solid var(--color-hairline)" }}>
                          <div className="caption" style={{ fontWeight: 600 }}>Stage 2: Vector Embedding</div>
                          <div style={{ fontWeight: 700, marginTop: 4, color: result.stage2.flagged ? "#ef4444" : "#10b981" }}>
                            {result.stage2.flagged ? "FLAGGED" : "PASSED"} ({(result.stage2.max_score * 100).toFixed(1)}%)
                          </div>
                          <div className="caption" style={{ marginTop: 4 }}>{result.stage2.time_ms} ms | Cross-Lingual Vector</div>
                        </div>

                        <div style={{ padding: 12, background: "var(--color-surface-card)", borderRadius: "var(--radius-md)", border: "1px solid var(--color-hairline)" }}>
                          <div className="caption" style={{ fontWeight: 600 }}>Stage 3: Graph xAI</div>
                          <div style={{ fontWeight: 700, marginTop: 4, color: "#3b82f6" }}>
                            {result.influential_words.length} Tokens Evaluated
                          </div>
                          <div className="caption" style={{ marginTop: 4 }}>SHAP/LIME Feature Weights</div>
                        </div>

                        <div style={{ padding: 12, background: "var(--color-surface-card)", borderRadius: "var(--radius-md)", border: "1px solid var(--color-hairline)" }}>
                          <div className="caption" style={{ fontWeight: 600 }}>Statutory Engine</div>
                          <div style={{ fontWeight: 700, marginTop: 4, color: result.violations.length > 0 ? "#ef4444" : "#10b981" }}>
                            {result.violations.length > 0 ? `${result.violations.length} VIOLATIONS` : "COMPLIANT"}
                          </div>
                          <div className="caption" style={{ marginTop: 4 }}>Emblems & Prior Apps</div>
                        </div>
                      </div>
                    </div>

                    {/* Detailed Analysis Tabs */}
                    <div className="card" style={{ padding: 24 }}>
                      <div style={{ display: "flex", gap: 12, borderBottom: "1px solid var(--color-hairline)", paddingBottom: 12, marginBottom: 20, overflowX: "auto" }}>
                        <button
                          onClick={() => setVerifyDetailTab("graph")}
                          className={`button ${verifyDetailTab === "graph" ? "button-primary" : "button-secondary"}`}
                          style={{ padding: "6px 14px", fontSize: 13 }}
                        >
                          Co-Registration Graph
                        </button>
                        <button
                          onClick={() => setVerifyDetailTab("xai")}
                          className={`button ${verifyDetailTab === "xai" ? "button-primary" : "button-secondary"}`}
                          style={{ padding: "6px 14px", fontSize: 13 }}
                        >
                          Explainable AI (xAI)
                        </button>
                        <button
                          onClick={() => setVerifyDetailTab("candidates")}
                          className={`button ${verifyDetailTab === "candidates" ? "button-primary" : "button-secondary"}`}
                          style={{ padding: "6px 14px", fontSize: 13 }}
                        >
                          Matched Titles ({result.top_candidates.length})
                        </button>
                        <button
                          onClick={() => setVerifyDetailTab("alternatives")}
                          className={`button ${verifyDetailTab === "alternatives" ? "button-primary" : "button-secondary"}`}
                          style={{ padding: "6px 14px", fontSize: 13 }}
                        >
                          Smart Alternatives ({result.smart_alternatives.length})
                        </button>
                        <button
                          onClick={() => setVerifyDetailTab("compliance")}
                          className={`button ${verifyDetailTab === "compliance" ? "button-primary" : "button-secondary"}`}
                          style={{ padding: "6px 14px", fontSize: 13 }}
                        >
                          Statutory Findings ({result.violations.length})
                        </button>
                      </div>

                      {/* Detail Content 1: Graph */}
                      {verifyDetailTab === "graph" && (
                        <div>
                          <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 6 }}>Interactive Co-Registration & Semantic Network Graph</h4>
                          <p className="caption" style={{ marginBottom: 16 }}>Force-directed network visualization mapping relationship clusters between proposed title, registered database titles, owners, and jurisdictions.</p>
                          <NetworkGraph data={result.graph_data} proposedTitle={title} />
                        </div>
                      )}

                      {/* Detail Content 2: xAI */}
                      {verifyDetailTab === "xai" && (
                        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>
                          <div>
                            <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 8 }}>Token Feature Importance (SHAP/LIME)</h4>
                            <SimpleBarChart
                              data={result.influential_words.map(w => ({ name: w.word, count: Math.round(w.importance * 100) }))}
                              color="#ef4444"
                            />
                          </div>
                          <div>
                            <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 8 }}>Attention Weight Distribution</h4>
                            <SimplePieChart
                              data={Object.entries(result.attention_weights).map(([k, v]) => ({ name: k, count: Math.round(v * 100) }))}
                            />
                          </div>
                        </div>
                      )}

                      {/* Detail Content 3: Top Matched Candidates */}
                      {verifyDetailTab === "candidates" && (
                        <div>
                          <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Top Matching Registered Titles in Database</h4>
                          <div style={{ overflowX: "auto" }}>
                            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                              <thead>
                                <tr style={{ borderBottom: "1px solid var(--color-hairline)", textAlign: "left" }}>
                                  <th style={{ padding: "8px 12px" }}>SN</th>
                                  <th style={{ padding: "8px 12px" }}>Registered Title</th>
                                  <th style={{ padding: "8px 12px" }}>Language</th>
                                  <th style={{ padding: "8px 12px" }}>State</th>
                                  <th style={{ padding: "8px 12px" }}>Owner</th>
                                  <th style={{ padding: "8px 12px" }}>Similarity Score</th>
                                </tr>
                              </thead>
                              <tbody>
                                {result.top_candidates.map((c, idx) => (
                                  <tr key={idx} style={{ borderBottom: "1px solid var(--color-hairline)" }}>
                                    <td style={{ padding: "8px 12px", color: "var(--color-muted)" }}>{c.sn}</td>
                                    <td style={{ padding: "8px 12px", fontWeight: 600 }}>{c.title}</td>
                                    <td style={{ padding: "8px 12px" }}>{c.language}</td>
                                    <td style={{ padding: "8px 12px" }}>{c.state}</td>
                                    <td style={{ padding: "8px 12px" }}>{c.owner || "N/A"}</td>
                                    <td style={{ padding: "8px 12px", fontWeight: 700, color: c.score > 0.75 ? "#ef4444" : "#f59e0b" }}>
                                      {(c.score * 100).toFixed(1)}%
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      )}

                      {/* Detail Content 4: Smart Alternatives */}
                      {verifyDetailTab === "alternatives" && (
                        <div>
                          <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>AI-Suggested Compliant Title Variations</h4>
                          {result.smart_alternatives.length > 0 ? (
                            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 12 }}>
                              {result.smart_alternatives.map((alt, idx) => (
                                <div key={idx} style={{ padding: 14, background: "var(--color-surface-card)", border: "1px solid var(--color-hairline)", borderRadius: "var(--radius-md)" }}>
                                  <div style={{ fontWeight: 700, fontSize: 14, color: "var(--color-ink)", marginBottom: 4 }}>{alt.title}</div>
                                  <div className="caption">{alt.reason}</div>
                                </div>
                              ))}
                            </div>
                          ) : (
                            <p className="caption">No automated alternatives generated for this title structure.</p>
                          )}
                        </div>
                      )}

                      {/* Detail Content 5: Compliance Findings */}
                      {verifyDetailTab === "compliance" && (
                        <div>
                          <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Statutory Compliance Audit Findings</h4>
                          {result.violations.length > 0 ? (
                            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                              {result.violations.map((v, idx) => (
                                <div key={idx} style={{ padding: 14, background: "#fef2f2", border: "1px solid #fca5a5", borderRadius: "var(--radius-md)" }}>
                                  <div style={{ fontWeight: 700, color: "#991b1b", fontSize: 14 }}>[{v.severity}] {v.rule}</div>
                                  <div style={{ color: "#7f1d1d", fontSize: 13, marginTop: 4 }}>{v.detail}</div>
                                </div>
                              ))}
                            </div>
                          ) : (
                            <div style={{ padding: 16, background: "#ecfdf5", border: "1px solid #6ee7b7", borderRadius: "var(--radius-md)", color: "#065f46" }}>
                              <CheckCircle2 style={{ display: "inline", marginRight: 8 }} size={16} />
                              Passed all statutory compliance checks (Emblems & Names Act, Periodicity Rules, Prior Submissions).
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* TAB 2: Submit Application */}
            {applicantTab === "submit" && (
              <div className="card" style={{ padding: 24, maxWidth: 800, margin: "0 auto" }}>
                <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 6 }}>Submit Official Title Registration Application</h2>
                <p className="caption" style={{ marginBottom: 24 }}>Complete the formal publisher submission dossier. The system automatically executes a pre-registration audit and logs it into the PRGI registry.</p>

                {subSuccessMsg && (
                  <div style={{ padding: 16, background: "#ecfdf5", border: "1px solid #6ee7b7", borderRadius: "var(--radius-md)", color: "#065f46", marginBottom: 20 }}>
                    {subSuccessMsg}
                  </div>
                )}

                <form onSubmit={handleSubmitApplication}>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>
                    <div>
                      <label className="caption" style={{ fontWeight: 600, display: "block", marginBottom: 6 }}>Applicant Full Name *</label>
                      <input type="text" className="input" required value={subApplicant} onChange={(e) => setSubApplicant(e.target.value)} />
                    </div>
                    <div>
                      <label className="caption" style={{ fontWeight: 600, display: "block", marginBottom: 6 }}>Publishing Organization *</label>
                      <input type="text" className="input" required value={subOrg} onChange={(e) => setSubOrg(e.target.value)} />
                    </div>
                  </div>

                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>
                    <div>
                      <label className="caption" style={{ fontWeight: 600, display: "block", marginBottom: 6 }}>Email Address *</label>
                      <input type="email" className="input" required value={subEmail} onChange={(e) => setSubEmail(e.target.value)} />
                    </div>
                    <div>
                      <label className="caption" style={{ fontWeight: 600, display: "block", marginBottom: 6 }}>Phone Number *</label>
                      <input type="text" className="input" required value={subPhone} onChange={(e) => setSubPhone(e.target.value)} />
                    </div>
                  </div>

                  <div style={{ borderTop: "1px solid var(--color-hairline)", paddingTop: 16, marginTop: 16, marginBottom: 16 }}>
                    <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 16, marginBottom: 16 }}>
                      <div>
                        <label className="caption" style={{ fontWeight: 600, display: "block", marginBottom: 6 }}>Proposed Publication Title *</label>
                        <input type="text" className="input" required value={title} onChange={(e) => setTitle(e.target.value)} />
                      </div>
                      <div>
                        <label className="caption" style={{ fontWeight: 600, display: "block", marginBottom: 6 }}>Language *</label>
                        <select className="input" value={language} onChange={(e) => setLanguage(e.target.value)}>
                          {["Hindi", "English", "Bengali", "Telugu", "Marathi", "Tamil", "Gujarati", "Urdu"].map(l => (
                            <option key={l} value={l}>{l}</option>
                          ))}
                        </select>
                      </div>
                    </div>

                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16, marginBottom: 24 }}>
                      <div>
                        <label className="caption" style={{ fontWeight: 600, display: "block", marginBottom: 6 }}>Periodicity *</label>
                        <select className="input" value={periodicity} onChange={(e) => setPeriodicity(e.target.value)}>
                          {["Daily", "Weekly", "Fortnightly", "Monthly"].map(p => (
                            <option key={p} value={p}>{p}</option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label className="caption" style={{ fontWeight: 600, display: "block", marginBottom: 6 }}>State *</label>
                        <input type="text" className="input" required value={state} onChange={(e) => setState(e.target.value)} />
                      </div>
                      <div>
                        <label className="caption" style={{ fontWeight: 600, display: "block", marginBottom: 6 }}>District *</label>
                        <input type="text" className="input" required value={district} onChange={(e) => setDistrict(e.target.value)} />
                      </div>
                    </div>
                  </div>

                  <button type="submit" className="button button-primary" style={{ width: "100%", padding: "12px" }} disabled={subLoading}>
                    {subLoading ? "Submitting to PRGI Registry..." : "Submit Application to PRGI Registrar"}
                  </button>
                </form>
              </div>
            )}

            {/* TAB 3: Track Application & Certificate */}
            {applicantTab === "track" && (
              <div style={{ maxWidth: 800, margin: "0 auto" }}>
                <div className="card" style={{ padding: 24, marginBottom: 24 }}>
                  <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 6 }}>Track Submitted Application & Audit Certificate</h2>
                  <p className="caption" style={{ marginBottom: 16 }}>Enter Application ID (e.g. PRGI-2026-A0001) or title keyword to check real-time status.</p>
                  
                  <form onSubmit={handleTrackSearch} style={{ display: "flex", gap: 12 }}>
                    <input
                      type="text"
                      className="input"
                      value={trackQuery}
                      onChange={(e) => setTrackQuery(e.target.value)}
                      placeholder="PRGI-2026-A0001"
                      style={{ flex: 1 }}
                    />
                    <button type="submit" className="button button-primary" style={{ padding: "0 20px" }}>Search</button>
                  </form>
                </div>

                {trackError && (
                  <div style={{ padding: 16, background: "#fef2f2", border: "1px solid #fca5a5", borderRadius: "var(--radius-md)", color: "#991b1b" }}>
                    {trackError}
                  </div>
                )}

                {trackedApp && (
                  <div className="card" style={{ padding: 24 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16, borderBottom: "1px solid var(--color-hairline)", paddingBottom: 12 }}>
                      <div>
                        <div className="caption">Application ID</div>
                        <div style={{ fontWeight: 700, fontSize: 18 }}>{trackedApp.app_id}</div>
                      </div>
                      <div>
                        {trackedApp.status === "APPROVED" && <span className="badge badge-approved">APPROVED</span>}
                        {trackedApp.status === "PENDING_REVIEW" && <span className="badge badge-review">PENDING REVIEW</span>}
                        {trackedApp.status === "REJECTED" && <span className="badge badge-rejected">REJECTED</span>}
                      </div>
                    </div>

                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 20 }}>
                      <div>
                        <div className="caption">Proposed Title</div>
                        <div style={{ fontWeight: 600, fontSize: 15 }}>{trackedApp.title}</div>
                      </div>
                      <div>
                        <div className="caption">Applicant / Organization</div>
                        <div style={{ fontWeight: 600, fontSize: 15 }}>{trackedApp.applicant_name} ({trackedApp.organization})</div>
                      </div>
                      <div>
                        <div className="caption">Language & Periodicity</div>
                        <div>{trackedApp.language} | {trackedApp.periodicity}</div>
                      </div>
                      <div>
                        <div className="caption">Jurisdiction</div>
                        <div>{trackedApp.district}, {trackedApp.state}</div>
                      </div>
                    </div>

                    {trackedApp.admin_remarks && (
                      <div style={{ padding: 14, background: "var(--color-surface-card)", border: "1px solid var(--color-hairline)", borderRadius: "var(--radius-md)", marginBottom: 20 }}>
                        <div className="caption" style={{ fontWeight: 600 }}>Official Registrar Remarks:</div>
                        <div style={{ fontSize: 14, marginTop: 4 }}>{trackedApp.admin_remarks}</div>
                      </div>
                    )}

                    <a
                      href={`http://localhost:8000/api/certificate/${trackedApp.app_id}`}
                      target="_blank"
                      rel="noreferrer"
                      className="button button-primary"
                      style={{ display: "inline-flex", alignItems: "center", gap: 8, textDecoration: "none" }}
                    >
                      <Download size={16} /> Download Verification & Audit Certificate (HTML)
                    </a>
                  </div>
                )}
              </div>
            )}

            {/* TAB 4: Statutory Guidelines */}
            {applicantTab === "rules" && (
              <div className="card" style={{ padding: 28, maxWidth: 840, margin: "0 auto" }}>
                <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 12 }}>PRGI Statutory Verification Guidelines</h2>
                <div style={{ display: "flex", flexDirection: "column", gap: 16, fontSize: 14, lineHeight: 1.6 }}>
                  <div>
                    <strong>1. Uniqueness & Non-Deceptiveness:</strong> The proposed title must not be identical or deceptively similar to any existing registered newspaper or periodical title. Phonetic variations (e.g. <em>Khabar</em> vs <em>Khabbar</em>) are strictly disallowed.
                  </div>
                  <div>
                    <strong>2. Disallowed Statutory Words:</strong> Titles containing protected national keywords (<em>Police, Crime, Corruption, CBI, CID, Army, Rashtrapati, Supreme Court, Parliament</em>) are prohibited under the Emblems and Names Act.
                  </div>
                  <div>
                    <strong>3. Combination of Registered Titles:</strong> Combining two existing registered titles into a new title (e.g. <em>Hindu</em> + <em>Indian Express</em> &rarr; <em>Hindu Indian Express</em>) is strictly prohibited.
                  </div>
                  <div>
                    <strong>4. Periodicity Prefix/Suffix Manipulation:</strong> Merely adding or omitting periodicity terms (e.g. <em>Daily, Weekly, Monthly, Dainik, Saptahik</em>) to an existing title is invalid.
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ========================================================================= */}
        {/* MODE 2: PRGI OFFICIAL & REGISTRAR ADMIN PORTAL                             */}
        {/* ========================================================================= */}
        {portalMode === "admin" && (
          <div>
            {/* Admin Header Sub-Tabs */}
            <div style={{ display: "flex", gap: 8, borderBottom: "1px solid var(--color-hairline)", marginBottom: 24 }}>
              <button
                onClick={() => setAdminTab("queue")}
                style={{ padding: "10px 16px", borderBottom: adminTab === "queue" ? "2px solid var(--color-ink)" : "2px solid transparent", fontWeight: 600, fontSize: 14, background: "none", cursor: "pointer" }}
              >
                Registrar Queue & Decision Desk
              </button>
              <button
                onClick={() => setAdminTab("analytics")}
                style={{ padding: "10px 16px", borderBottom: adminTab === "analytics" ? "2px solid var(--color-ink)" : "2px solid transparent", fontWeight: 600, fontSize: 14, background: "none", cursor: "pointer" }}
              >
                National Database Analytics
              </button>
              <button
                onClick={() => setAdminTab("explorer")}
                style={{ padding: "10px 16px", borderBottom: adminTab === "explorer" ? "2px solid var(--color-ink)" : "2px solid transparent", fontWeight: 600, fontSize: 14, background: "none", cursor: "pointer" }}
              >
                Database Explorer
              </button>
            </div>

            {/* ADMIN TAB 1: Application Queue & Decision Desk */}
            {adminTab === "queue" && (
              <div>
                {/* Metric Summary Bar */}
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 16, marginBottom: 24 }}>
                  <div className="card" style={{ padding: 16, textAlign: "center" }}>
                    <div className="caption">Total Submissions</div>
                    <div style={{ fontSize: 24, fontWeight: 700, marginTop: 4 }}>{applications.length}</div>
                  </div>
                  <div className="card" style={{ padding: 16, textAlign: "center" }}>
                    <div className="caption">Pending Review</div>
                    <div style={{ fontSize: 24, fontWeight: 700, marginTop: 4, color: "#f59e0b" }}>{pendingAppsCount}</div>
                  </div>
                  <div className="card" style={{ padding: 16, textAlign: "center" }}>
                    <div className="caption">Approved</div>
                    <div style={{ fontSize: 24, fontWeight: 700, marginTop: 4, color: "#10b981" }}>
                      {applications.filter(a => a.status === "APPROVED").length}
                    </div>
                  </div>
                  <div className="card" style={{ padding: 16, textAlign: "center" }}>
                    <div className="caption">Rejected / Modified</div>
                    <div style={{ fontSize: 24, fontWeight: 700, marginTop: 4, color: "#ef4444" }}>
                      {applications.filter(a => a.status === "REJECTED" || a.status === "MODIFICATION_REQUESTED").length}
                    </div>
                  </div>
                </div>

                {applications.length === 0 ? (
                  <div className="card" style={{ padding: 32, textAlign: "center", color: "var(--color-muted)" }}>
                    No applications currently logged in the registry. Submit an application from the Publisher Portal!
                  </div>
                ) : (
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: 24 }}>
                    {/* Application Selection Column */}
                    <div className="card" style={{ padding: 16, height: "fit-content" }}>
                      <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Application Queue</h3>
                      <div style={{ display: "flex", flexDirection: "column", gap: 8, maxHeight: 500, overflowY: "auto" }}>
                        {applications.map(app => (
                          <div
                            key={app.app_id}
                            onClick={() => setSelectedAppId(app.app_id)}
                            style={{
                              padding: 12,
                              borderRadius: "var(--radius-md)",
                              border: selectedAppId === app.app_id ? "2px solid var(--color-ink)" : "1px solid var(--color-hairline)",
                              cursor: "pointer",
                              background: selectedAppId === app.app_id ? "var(--color-surface-card)" : "#fff"
                            }}
                          >
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                              <span style={{ fontWeight: 700, fontSize: 13 }}>{app.app_id}</span>
                              <span style={{ fontSize: 11, fontWeight: 600, color: app.status === "APPROVED" ? "#10b981" : app.status === "REJECTED" ? "#ef4444" : "#f59e0b" }}>
                                {app.status}
                              </span>
                            </div>
                            <div style={{ fontWeight: 600, fontSize: 14, marginTop: 4 }}>{app.title}</div>
                            <div className="caption" style={{ marginTop: 2 }}>{app.applicant_name} &bull; {app.language}</div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Review Dossier & Action Panel Column */}
                    {selectedApp && (
                      <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
                        <div className="card" style={{ padding: 24 }}>
                          <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 16 }}>Dossier: {selectedApp.app_id}</h3>
                          
                          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 20 }}>
                            <div>
                              <div className="caption">Proposed Title</div>
                              <div style={{ fontWeight: 700, fontSize: 16 }}>{selectedApp.title}</div>
                            </div>
                            <div>
                              <div className="caption">Applicant & Organization</div>
                              <div style={{ fontWeight: 600 }}>{selectedApp.applicant_name} ({selectedApp.organization})</div>
                            </div>
                            <div>
                              <div className="caption">Language & Periodicity</div>
                              <div>{selectedApp.language} | {selectedApp.periodicity}</div>
                            </div>
                            <div>
                              <div className="caption">Jurisdiction</div>
                              <div>{selectedApp.district}, {selectedApp.state}</div>
                            </div>
                          </div>

                          {selectedApp.audit_data && (
                            <div style={{ borderTop: "1px solid var(--color-hairline)", paddingTop: 16 }}>
                              <h4 style={{ fontSize: 14, fontWeight: 700, marginBottom: 8 }}>AI Audit Summary</h4>
                              {selectedApp.audit_data.violations.length > 0 ? (
                                <div style={{ padding: 12, background: "#fef2f2", border: "1px solid #fca5a5", borderRadius: "var(--radius-md)", color: "#991b1b", fontSize: 13, marginBottom: 12 }}>
                                  🚨 Statutory Violations Detected ({selectedApp.audit_data.violations.length})
                                </div>
                              ) : (
                                <div style={{ padding: 12, background: "#ecfdf5", border: "1px solid #6ee7b7", borderRadius: "var(--radius-md)", color: "#065f46", fontSize: 13, marginBottom: 12 }}>
                                  ✅ Clean AI Audit: Passed phonetic, vector similarity, and Statutory Engine checks.
                                </div>
                              )}
                            </div>
                          )}
                        </div>

                        {/* Official Registrar Action Panel */}
                        <div className="card" style={{ padding: 24, border: "2px solid var(--color-ink)" }}>
                          <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 12 }}>Official Registrar Determination Desk</h3>
                          
                          {decisionMsg && (
                            <div style={{ padding: 12, background: "#ecfdf5", color: "#065f46", borderRadius: "var(--radius-md)", marginBottom: 16, fontSize: 13 }}>
                              {decisionMsg}
                            </div>
                          )}

                          <form onSubmit={handleAdminDecisionSubmit}>
                            <div style={{ marginBottom: 16 }}>
                              <label className="caption" style={{ fontWeight: 600, display: "block", marginBottom: 8 }}>Official Determination *</label>
                              <div style={{ display: "flex", gap: 12 }}>
                                <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 13, cursor: "pointer" }}>
                                  <input type="radio" name="decision" checked={decisionChoice === "APPROVED"} onChange={() => setDecisionChoice("APPROVED")} />
                                  Approve Registration
                                </label>
                                <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 13, cursor: "pointer" }}>
                                  <input type="radio" name="decision" checked={decisionChoice === "REJECTED"} onChange={() => setDecisionChoice("REJECTED")} />
                                  Reject Application
                                </label>
                                <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 13, cursor: "pointer" }}>
                                  <input type="radio" name="decision" checked={decisionChoice === "MODIFICATION_REQUESTED"} onChange={() => setDecisionChoice("MODIFICATION_REQUESTED")} />
                                  Request Modification
                                </label>
                              </div>
                            </div>

                            <div style={{ marginBottom: 20 }}>
                              <label className="caption" style={{ fontWeight: 600, display: "block", marginBottom: 6 }}>Official Registrar Remarks / Compliance Order *</label>
                              <textarea
                                className="input"
                                rows={3}
                                required
                                value={decisionRemarks}
                                onChange={(e) => setDecisionRemarks(e.target.value)}
                                placeholder="Enter official compliance reasoning or directives..."
                              />
                            </div>

                            <button type="submit" className="button button-primary" style={{ width: "100%", padding: 12 }} disabled={adminLoading}>
                              {adminLoading ? "Recording Official Determination..." : "Submit Official Registrar Decision"}
                            </button>
                          </form>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* ADMIN TAB 2: National Database Analytics */}
            {adminTab === "analytics" && (
              <div>
                <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 4 }}>National PRGI Database Analytics</h2>
                <p className="caption" style={{ marginBottom: 24 }}>Statistical breakdown across registered publication titles in India.</p>

                {analyticsLoading ? (
                  <div style={{ padding: 40, textAlign: "center" }}>Loading National Database Analytics...</div>
                ) : analytics ? (
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>
                    <div className="card" style={{ padding: 20 }}>
                      <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 8 }}>Top 10 Languages</h3>
                      <SimpleBarChart data={analytics.languages} color="#3b82f6" />
                    </div>

                    <div className="card" style={{ padding: 20 }}>
                      <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 8 }}>Periodicity Distribution</h3>
                      <SimplePieChart data={analytics.periodicities} />
                    </div>

                    <div className="card" style={{ padding: 20 }}>
                      <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 8 }}>Top 10 Publication States</h3>
                      <SimpleBarChart data={analytics.states} color="#10b981" />
                    </div>

                    <div className="card" style={{ padding: 20 }}>
                      <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 8 }}>High-Frequency Title Keywords</h3>
                      <SimpleBarChart data={analytics.keywords.map(k => ({ name: k.word, count: k.count }))} color="#8b5cf6" />
                    </div>
                  </div>
                ) : null}
              </div>
            )}

            {/* ADMIN TAB 3: Database Explorer */}
            {adminTab === "explorer" && (
              <div>
                <div className="card" style={{ padding: 20, marginBottom: 24 }}>
                  <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 6 }}>Registered PRGI Database Explorer</h2>
                  <p className="caption" style={{ marginBottom: 16 }}>Search registered titles by keyword, registration number, or owner entity name.</p>
                  
                  <div style={{ display: "flex", gap: 12 }}>
                    <input
                      type="text"
                      className="input"
                      placeholder="e.g. Dainik, Awadh, PRGI-1234..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      style={{ flex: 1 }}
                    />
                    <button
                      className="button button-primary"
                      onClick={() => fetchExplorer(searchQuery)}
                      style={{ padding: "0 20px" }}
                    >
                      Search Database
                    </button>
                  </div>
                </div>

                <div className="card" style={{ padding: 20 }}>
                  <div style={{ fontSize: 13, fontWeight: 600, color: "var(--color-muted)", marginBottom: 12 }}>
                    Found {explorerRecords.length} records:
                  </div>

                  {explorerLoading ? (
                    <div style={{ padding: 24, textAlign: "center" }}>Searching records...</div>
                  ) : (
                    <div style={{ overflowX: "auto" }}>
                      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                        <thead>
                          <tr style={{ borderBottom: "1px solid var(--color-hairline)", textAlign: "left" }}>
                            <th style={{ padding: "8px 12px" }}>SN</th>
                            <th style={{ padding: "8px 12px" }}>Title</th>
                            <th style={{ padding: "8px 12px" }}>Reg No</th>
                            <th style={{ padding: "8px 12px" }}>Language</th>
                            <th style={{ padding: "8px 12px" }}>Periodicity</th>
                            <th style={{ padding: "8px 12px" }}>Owner / Publisher</th>
                            <th style={{ padding: "8px 12px" }}>State</th>
                          </tr>
                        </thead>
                        <tbody>
                          {explorerRecords.map((r, idx) => (
                            <tr key={idx} style={{ borderBottom: "1px solid var(--color-hairline)" }}>
                              <td style={{ padding: "8px 12px", color: "var(--color-muted)" }}>{r.sn}</td>
                              <td style={{ padding: "8px 12px", fontWeight: 600 }}>{r.title}</td>
                              <td style={{ padding: "8px 12px" }}>{r.registration_number || "N/A"}</td>
                              <td style={{ padding: "8px 12px" }}>{r.language}</td>
                              <td style={{ padding: "8px 12px" }}>{r.periodicity}</td>
                              <td style={{ padding: "8px 12px" }}>{r.owner || r.publisher || "N/A"}</td>
                              <td style={{ padding: "8px 12px" }}>{r.publication_state}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

export interface VerifyRequest {
  title: string;
  language: string;
  periodicity: string;
  state: string;
  district: string;
  publisher?: string;
  owner?: string;
}

export interface Candidate {
  sn: number;
  title: string;
  language: string;
  state: string;
  periodicity: string;
  owner: string;
  score: number;
  soundex_match: boolean;
}

export interface Violation {
  rule: string;
  severity: string;
  detail: string;
}

export interface Alternative {
  title: string;
  reason: string;
}

export interface InfluentialWord {
  word: string;
  importance: number;
}

export interface GraphNode {
  id: string;
  label: string;
  type: string;
  score?: number;
}

export interface GraphEdge {
  source: string;
  target: string;
  relation: string;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface VerifyResult {
  status: "APPROVED" | "UNDER_REVIEW" | "REJECTED";
  status_desc: string;
  acceptance_probability: number;
  rejection_probability: number;
  highest_similarity: number;
  total_latency_ms: number;
  stage1: { flagged: boolean; max_score: number; time_ms: number };
  stage2: { flagged: boolean; max_score: number; time_ms: number };
  top_candidates: Candidate[];
  violations: Violation[];
  recommendations: string[];
  smart_alternatives: Alternative[];
  influential_words: InfluentialWord[];
  attention_weights: Record<string, number>;
  graph_data: GraphData;
}

export interface Application {
  app_id: string;
  title: string;
  language: string;
  periodicity: string;
  state: string;
  district: string;
  applicant_name: string;
  organization: string;
  email: string;
  phone: string;
  submission_timestamp: string;
  status: string;
  auto_probability: number;
  audit_data: VerifyResult;
  admin_remarks?: string;
  reviewed_timestamp?: string;
}

export interface AnalyticsData {
  total_titles: number;
  languages: { name: string; count: number }[];
  periodicities: { name: string; count: number }[];
  states: { name: string; count: number }[];
  keywords: { word: string; count: number }[];
}

export interface ExplorerRecord {
  sn: number;
  title: string;
  registration_number: string;
  registration_date: string;
  language: string;
  periodicity: string;
  publisher: string;
  owner: string;
  publication_state: string;
  publication_district: string;
}

const API_BASE = "http://localhost:8000";

export async function verifyTitle(req: VerifyRequest): Promise<VerifyResult> {
  const res = await fetch(`${API_BASE}/api/verify`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || "Verification failed");
  }
  return res.json();
}

export async function listApplications(): Promise<Application[]> {
  const res = await fetch(`${API_BASE}/api/applications`);
  if (!res.ok) throw new Error("Failed to fetch applications");
  return res.json();
}

export async function submitApplication(data: {
  title: string;
  language: string;
  periodicity: string;
  state: string;
  district: string;
  applicant_name: string;
  organization: string;
  email: string;
  phone: string;
}): Promise<{ app_id: string; status: string; auto_probability: number; message: string }> {
  const res = await fetch(`${API_BASE}/api/applications/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to submit application");
  return res.json();
}

export async function getApplication(app_id: string): Promise<Application> {
  const res = await fetch(`${API_BASE}/api/applications/${app_id}`);
  if (!res.ok) throw new Error(`Application ${app_id} not found`);
  return res.json();
}

export async function submitDecision(
  app_id: string,
  status: string,
  remarks: string
): Promise<{ status: string; app_id: string; new_status: string }> {
  const res = await fetch(`${API_BASE}/api/applications/${app_id}/decision`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status, remarks }),
  });
  if (!res.ok) throw new Error("Failed to submit registrar decision");
  return res.json();
}

export async function getAnalytics(): Promise<AnalyticsData> {
  const res = await fetch(`${API_BASE}/api/analytics`);
  if (!res.ok) throw new Error("Failed to fetch analytics");
  return res.json();
}

export async function searchExplorer(q: string = ""): Promise<{ count: number; records: ExplorerRecord[] }> {
  const res = await fetch(`${API_BASE}/api/explorer?q=${encodeURIComponent(q)}`);
  if (!res.ok) throw new Error("Failed to search database");
  return res.json();
}

export async function flagDerogatoryTerm(term: string): Promise<{ status: string; term: string; total_seed_terms: number; message: string }> {
  const res = await fetch(`${API_BASE}/api/derogatory/flag`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ term, source: "COMMUNITY_FLAG" }),
  });
  if (!res.ok) throw new Error("Failed to flag derogatory term");
  return res.json();
}

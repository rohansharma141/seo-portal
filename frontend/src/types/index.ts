// Shared types mirroring the backend response models (Section 7 + Addendum v1.1).

export type SiteType = "brokerage" | "saas" | "broker_landing" | "other";
export type Schedule = "weekly" | "monthly" | "manual";
export type TriggeredBy = "manual" | "scheduled" | "api" | "deploy_hook";
export type Severity = "critical" | "warning" | "info";
export type AuditStatusValue =
  | "pending"
  | "crawling"
  | "analysing"
  | "scoring"
  | "complete"
  | "failed";

export interface Health {
  status: string;
  version: string;
  timestamp: string;
}

// ── Sites (7.2) ─────────────────────────────────────────────
export interface Site {
  id: string;
  name: string;
  domain: string;
  url: string;
  site_type: string;
  schedule: string;
  is_active: boolean;
  last_audit_at: string | null;
  last_score: number | null;
  created_at: string;
}

export interface LastAuditSummary {
  audit_id: string;
  status: string;
  score_overall: number | null;
  completed_at: string | null;
}

export interface SiteDetail extends Site {
  last_audit: LastAuditSummary | null;
}

export interface SiteListResponse {
  sites: Site[];
  total: number;
}

export interface SiteCreate {
  name: string;
  domain: string;
  url: string;
  site_type?: SiteType;
  schedule?: Schedule;
  max_pages?: number;
}

export type SiteUpdate = Partial<
  Pick<SiteCreate, "name" | "url" | "site_type" | "schedule" | "max_pages">
> & { is_active?: boolean };

// ── Audits (7.3) ────────────────────────────────────────────
export interface AuditScores {
  overall: number | null;
  technical: number | null;
  content: number | null;
  eeeat: number | null;
  performance: number | null;
  structure: number | null;
}

export interface IssueCounts {
  critical: number;
  warning: number;
  info: number;
}

export interface QuickWin {
  title: string;
  effort: string;
  impact: string;
  description: string;
}

export interface AuditAnalysis {
  summary: string | null;
  quick_wins: QuickWin[];
  priority_actions: string[];
  positive_signals: string[];
}

// Addendum v1.1 — backlink placeholder
export interface Backlinks {
  domain?: string;
  data_source?: "mock" | "dataforseo";
  fetched_at?: string;
  domain_rank?: number;
  referring_domains?: number;
  referring_pages?: number;
  backlinks_total?: number;
  backlinks_dofollow?: number;
  backlinks_nofollow?: number;
  broken_backlinks?: number;
  top_referring_domains?: Array<Record<string, unknown>>;
  anchor_distribution?: Array<Record<string, unknown>>;
  new_lost?: {
    new_referring_domains_30d: number;
    lost_referring_domains_30d: number;
  };
  placeholder_note?: string | null;
}

// Addendum v1.2 — PageSpeed Insights
export interface PsiOpportunity {
  id: string;
  title: string;
  savings_ms: number;
  description: string;
}

export interface PageSpeedResult {
  url: string;
  strategy: string;
  data_source: "psi_api" | "mock";
  performance_score: number;
  lab: {
    lcp_ms: number | null;
    cls: number | null;
    inp_ms: number | null;
    fcp_ms: number | null;
    tbt_ms: number | null;
    speed_index_ms: number | null;
  };
  field: {
    lcp_ms?: number | null;
    cls?: number | null;
    inp_ms?: number | null;
    has_field_data: boolean;
  };
  opportunities: PsiOpportunity[];
  error?: string | null;
  note?: string;
  fetched_at: string;
}

export interface Audit {
  id: string;
  site_id: string;
  status: AuditStatusValue;
  scores: AuditScores;
  pages_crawled: number;
  issues: IssueCounts;
  analysis: AuditAnalysis;
  gsc_snapshot: Record<string, unknown>;
  backlinks: Backlinks;
  pagespeed: PageSpeedResult[];
  started_at: string | null;
  completed_at: string | null;
}

export interface AuditListItem {
  id: string;
  site_id: string;
  status: AuditStatusValue;
  score_overall: number | null;
  triggered_by: string;
  created_at: string;
  completed_at: string | null;
}

export interface AuditListResponse {
  audits: AuditListItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface AuditCreated {
  audit_id: string;
  status: string;
  site_id: string;
  message: string;
  estimated_seconds: number;
}

export interface AuditStatus {
  audit_id: string;
  status: AuditStatusValue;
  progress_message: string;
  pages_crawled: number;
  started_at: string | null;
}

export interface AuditIssue {
  id: string;
  page_url: string | null;
  category: string;
  severity: Severity;
  rule_id: string;
  rule_name: string;
  description: string;
  fix_suggestion: string;
  affected_value: string | null;
  expected_value: string | null;
}

export interface AuditIssuesResponse {
  issues: AuditIssue[];
  total: number;
  filters: { severity: string | null; category: string | null };
}

// ── Reports (7.4 + Addendum v1.1) ───────────────────────────
export interface SiteHistory {
  site_id: string;
  site_name: string;
  audits: Array<{
    audit_id: string;
    date: string | null;
    score: number | null;
    critical: number;
    warning: number;
  }>;
  trend: string;
}

export interface SummaryReport {
  sites_total: number;
  sites_healthy: number;
  sites_warning: number;
  sites_critical: number;
  avg_score_all_sites: number;
  total_critical_issues: number;
  total_warning_issues: number;
  sites: Array<{
    name: string;
    score: number | null;
    status: string;
    last_audited: string | null;
  }>;
}

export interface CrossCompare {
  generated_at: string;
  sites: Array<{
    site_id: string;
    site_name: string;
    domain: string;
    site_type: string;
    audit_id: string;
    audit_date: string | null;
    scores: Record<string, number>;
    issues: IssueCounts;
    pages_crawled: number;
    rank: number;
  }>;
  leader: { site_id: string; site_name: string; overall_score: number };
  category_leaders: Record<string, string>;
  gaps: Array<{
    category: string;
    site_id: string;
    site_name: string;
    score: number;
    leader_score: number;
    gap: number;
    note: string | null;
  }>;
}

// ── Tokens (7.5) ────────────────────────────────────────────
export interface ApiToken {
  id: string;
  name: string;
  token_prefix: string;
  scopes: string[];
  is_active: boolean;
  last_used_at: string | null;
  expires_at: string | null;
  created_at: string;
}

export interface TokenListResponse {
  tokens: ApiToken[];
  total: number;
}

export interface TokenCreated {
  id: string;
  name: string;
  token: string;
  token_prefix: string;
  scopes: string[];
  warning: string;
}

// ── Webhooks (7.6) ──────────────────────────────────────────
export interface Webhook {
  id: string;
  name: string;
  url: string;
  events: string[];
  is_active: boolean;
  last_triggered_at: string | null;
  created_at: string;
}

export interface WebhookListResponse {
  webhooks: Webhook[];
  total: number;
}

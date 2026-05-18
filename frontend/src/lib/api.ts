// Typed API client mirroring every backend endpoint (Section 7 + Addendum v1.1).
import type {
  ApiToken,
  Audit,
  AuditCreated,
  AuditIssuesResponse,
  AuditListResponse,
  AuditStatus,
  CrossCompare,
  Health,
  Site,
  SiteCreate,
  SiteDetail,
  SiteHistory,
  SiteListResponse,
  SiteUpdate,
  SummaryReport,
  TokenCreated,
  TokenListResponse,
  Webhook,
  WebhookListResponse,
} from "@/types";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ??
  "http://localhost:8000";

const TOKEN_KEY = "seo_portal_token";

export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
  ) {
    super(`API ${status}: ${detail}`);
    this.name = "ApiError";
  }
}

function authToken(): string | null {
  if (typeof window !== "undefined") {
    const stored = window.localStorage.getItem(TOKEN_KEY);
    if (stored) return stored;
  }
  return process.env.NEXT_PUBLIC_API_TOKEN || null;
}

export function setAuthToken(token: string): void {
  if (typeof window !== "undefined")
    window.localStorage.setItem(TOKEN_KEY, token);
}

async function request<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Content-Type", "application/json");
  const token = authToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const res = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body?.detail ?? detail;
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(res.status, String(detail));
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

function qs(params: Record<string, unknown>): string {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== "") sp.set(k, String(v));
  }
  const s = sp.toString();
  return s ? `?${s}` : "";
}

export const api = {
  health: () => request<Health>("/health"),

  sites: {
    list: () => request<SiteListResponse>("/api/v1/sites"),
    create: (body: SiteCreate) =>
      request<Site>("/api/v1/sites", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    get: (id: string) =>
      request<SiteDetail>(`/api/v1/sites/${id}`),
    update: (id: string, body: SiteUpdate) =>
      request<SiteDetail>(`/api/v1/sites/${id}`, {
        method: "PATCH",
        body: JSON.stringify(body),
      }),
    remove: (id: string) =>
      request<{ status: string; id: string }>(`/api/v1/sites/${id}`, {
        method: "DELETE",
      }),
  },

  audits: {
    list: (params: { site_id?: string; limit?: number; offset?: number } = {}) =>
      request<AuditListResponse>(`/api/v1/audits${qs(params)}`),
    trigger: (site_id: string, triggered_by = "manual") =>
      request<AuditCreated>("/api/v1/audits", {
        method: "POST",
        body: JSON.stringify({ site_id, triggered_by }),
      }),
    get: (id: string) => request<Audit>(`/api/v1/audits/${id}`),
    issues: (
      id: string,
      params: { severity?: string; category?: string } = {},
    ) =>
      request<AuditIssuesResponse>(
        `/api/v1/audits/${id}/issues${qs(params)}`,
      ),
    status: (id: string) =>
      request<AuditStatus>(`/api/v1/audits/${id}/status`),
  },

  reports: {
    summary: () => request<SummaryReport>("/api/v1/reports/summary"),
    siteHistory: (siteId: string) =>
      request<SiteHistory>(`/api/v1/reports/site/${siteId}/history`),
    compareAudits: (siteId: string, a: string, b: string) =>
      request<unknown>(
        `/api/v1/reports/site/${siteId}/compare${qs({ a, b })}`,
      ),
    // Addendum v1.1 — cross-site comparison
    crossCompare: (siteIds: string[]) =>
      request<CrossCompare>(
        `/api/v1/reports/compare${qs({ site_ids: siteIds.join(",") })}`,
      ),
  },

  tokens: {
    list: () => request<TokenListResponse>("/api/v1/tokens"),
    create: (body: {
      name: string;
      scopes?: string[];
      expires_at?: string | null;
    }) =>
      request<TokenCreated>("/api/v1/tokens", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    revoke: (id: string) =>
      request<{ status: string; id: string }>(`/api/v1/tokens/${id}`, {
        method: "DELETE",
      }),
  },

  webhooks: {
    list: () => request<WebhookListResponse>("/api/v1/webhooks"),
    create: (body: {
      name: string;
      url: string;
      events?: string[];
      secret?: string | null;
    }) =>
      request<Webhook>("/api/v1/webhooks", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    remove: (id: string) =>
      request<{ status: string; id: string }>(`/api/v1/webhooks/${id}`, {
        method: "DELETE",
      }),
    test: (url: string, secret?: string | null) =>
      request<{ delivered: boolean; detail: string }>(
        "/api/v1/webhooks/test",
        { method: "POST", body: JSON.stringify({ url, secret }) },
      ),
  },
};

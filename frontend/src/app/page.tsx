"use client";

import Link from "next/link";
import { useState } from "react";

import { StatusBadge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { ScoreGauge } from "@/components/ui/ScoreGauge";
import { PageHeader, StateView } from "@/components/ui/State";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { formatDate, scoreBand } from "@/lib/utils";
import type { AuditListResponse, SiteListResponse, SummaryReport } from "@/types";

interface DashboardData {
  sites: SiteListResponse;
  summary: SummaryReport;
  audits: AuditListResponse;
}

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <Card>
      <p className="text-xs uppercase tracking-wide text-slate-500">
        {label}
      </p>
      <p className="mt-2 font-mono text-2xl font-semibold text-slate-900 tnum">
        {value}
      </p>
    </Card>
  );
}

export default function DashboardPage() {
  const [busy, setBusy] = useState<string | null>(null);
  const state = useApi<DashboardData>(async () => {
    const [sites, summary, audits] = await Promise.all([
      api.sites.list(),
      api.reports.summary(),
      api.audits.list({ limit: 50 }),
    ]);
    return { sites, summary, audits };
  }, []);

  async function auditNow(siteId: string) {
    setBusy(siteId);
    try {
      await api.audits.trigger(siteId, "manual");
      await state.reload();
    } finally {
      setBusy(null);
    }
  }

  const thisMonth = (iso: string) => {
    const d = new Date(iso);
    const now = new Date();
    return (
      d.getUTCFullYear() === now.getUTCFullYear() &&
      d.getUTCMonth() === now.getUTCMonth()
    );
  };

  return (
    <div>
      <PageHeader title="SEO Health Dashboard" />
      <StateView state={state}>
        {({ sites, summary, audits }) => {
          const auditsThisMonth = audits.audits.filter((a) =>
            thisMonth(a.created_at),
          ).length;
          const attention = [...sites.sites]
            .filter((s) => s.last_score != null)
            .sort((a, b) => (a.last_score ?? 0) - (b.last_score ?? 0))
            .slice(0, 3);
          return (
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
                <StatCard label="Total Sites" value={sites.total} />
                <StatCard
                  label="Avg Score"
                  value={summary.avg_score_all_sites}
                />
                <StatCard
                  label="Critical Issues"
                  value={summary.total_critical_issues}
                />
                <StatCard
                  label="Audits This Month"
                  value={auditsThisMonth}
                />
              </div>

              <Card>
                <h3 className="mb-4 text-sm font-semibold text-slate-900">
                  Sites
                </h3>
                {sites.sites.length === 0 ? (
                  <p className="text-sm text-slate-500">
                    No sites yet.{" "}
                    <Link href="/sites" className="text-brand underline">
                      Add one
                    </Link>
                    .
                  </p>
                ) : (
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-slate-200 text-left text-xs uppercase text-slate-500">
                        <th className="pb-2">Name</th>
                        <th className="pb-2">Score</th>
                        <th className="pb-2">Last Audited</th>
                        <th className="pb-2">Status</th>
                        <th className="pb-2 text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {sites.sites.map((s) => (
                        <tr
                          key={s.id}
                          className="border-b border-slate-100 last:border-0"
                        >
                          <td className="py-3">
                            <Link
                              href={`/sites/${s.id}`}
                              className="font-medium text-slate-900 hover:text-brand"
                            >
                              {s.name}
                            </Link>
                            <div className="text-xs text-slate-500">
                              {s.domain}
                            </div>
                          </td>
                          <td className="py-3">
                            <ScoreGauge score={s.last_score} size={48} />
                          </td>
                          <td className="py-3 text-slate-600">
                            {formatDate(s.last_audit_at)}
                          </td>
                          <td className="py-3">
                            <StatusBadge
                              status={scoreBand(s.last_score)}
                            />
                          </td>
                          <td className="py-3 text-right">
                            <Button
                              variant="secondary"
                              disabled={busy === s.id}
                              onClick={() => auditNow(s.id)}
                            >
                              {busy === s.id ? "Queuing…" : "Audit Now"}
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </Card>

              <div className="grid gap-6 lg:grid-cols-2">
                <Card>
                  <h3 className="mb-4 text-sm font-semibold text-slate-900">
                    Recent Audits
                  </h3>
                  {audits.audits.length === 0 ? (
                    <p className="text-sm text-slate-500">No audits yet.</p>
                  ) : (
                    <ul className="space-y-3">
                      {audits.audits.slice(0, 5).map((a) => (
                        <li
                          key={a.id}
                          className="flex items-center justify-between text-sm"
                        >
                          <div className="flex items-center gap-3">
                            <StatusBadge status={a.status} />
                            <span className="font-mono text-slate-700 tnum">
                              {a.score_overall ?? "—"}
                            </span>
                          </div>
                          <span className="text-slate-500">
                            {formatDate(a.created_at)}
                          </span>
                        </li>
                      ))}
                    </ul>
                  )}
                </Card>

                <Card>
                  <h3 className="mb-4 text-sm font-semibold text-slate-900">
                    Needs Attention
                  </h3>
                  {attention.length === 0 ? (
                    <p className="text-sm text-slate-500">
                      Nothing flagged — all audited sites are healthy.
                    </p>
                  ) : (
                    <ul className="space-y-3">
                      {attention.map((s) => (
                        <li
                          key={s.id}
                          className="flex items-center justify-between text-sm"
                        >
                          <Link
                            href={`/sites/${s.id}`}
                            className="font-medium text-slate-800 hover:text-brand"
                          >
                            {s.name}
                          </Link>
                          <span className="font-mono text-slate-700 tnum">
                            {s.last_score}
                          </span>
                        </li>
                      ))}
                    </ul>
                  )}
                </Card>
              </div>
            </div>
          );
        }}
      </StateView>
    </div>
  );
}

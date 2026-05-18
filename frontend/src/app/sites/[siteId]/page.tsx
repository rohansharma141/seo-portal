"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { StatusBadge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { PageHeader, StateView } from "@/components/ui/State";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { formatDate, scoreColor } from "@/lib/utils";
import type { Audit, AuditListResponse, SiteDetail } from "@/types";

const CATEGORIES = [
  "technical",
  "content",
  "eeeat",
  "performance",
  "structure",
] as const;

interface SiteData {
  site: SiteDetail;
  audits: AuditListResponse;
  latest: Audit | null;
}

export default function SiteDetailPage() {
  const { siteId } = useParams<{ siteId: string }>();
  const [running, setRunning] = useState<string | null>(null);
  const [progress, setProgress] = useState<string>("");
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);

  const state = useApi<SiteData>(async () => {
    const [site, audits] = await Promise.all([
      api.sites.get(siteId),
      api.audits.list({ site_id: siteId, limit: 20 }),
    ]);
    let latest: Audit | null = null;
    if (site.last_audit && site.last_audit.status === "complete") {
      latest = await api.audits.get(site.last_audit.audit_id);
    }
    return { site, audits, latest };
  }, [siteId]);

  useEffect(
    () => () => {
      if (timer.current) clearInterval(timer.current);
    },
    [],
  );

  async function triggerAudit() {
    const created = await api.audits.trigger(siteId, "manual");
    setRunning(created.audit_id);
    setProgress("Queued…");
    timer.current = setInterval(async () => {
      try {
        const st = await api.audits.status(created.audit_id);
        setProgress(st.progress_message);
        if (st.status === "complete" || st.status === "failed") {
          if (timer.current) clearInterval(timer.current);
          setRunning(null);
          await state.reload();
        }
      } catch {
        /* keep polling */
      }
    }, 3000);
  }

  return (
    <div>
      <StateView state={state}>
        {({ site, audits, latest }) => (
          <div className="space-y-6">
            <PageHeader
              title={site.name}
              subtitle={`${site.domain} · ${site.site_type} · ${site.schedule}`}
              action={
                <Button onClick={triggerAudit} disabled={!!running}>
                  {running ? "Audit running…" : "Trigger New Audit"}
                </Button>
              }
            />

            {running && (
              <Card className="border-amber-200 bg-amber-50">
                <div className="flex items-center gap-3 text-sm text-amber-800">
                  <span className="h-3 w-3 animate-pulse rounded-full bg-amber-500" />
                  Audit in progress — {progress}
                </div>
              </Card>
            )}

            <div className="grid gap-6 lg:grid-cols-2">
              <Card>
                <h3 className="mb-4 text-sm font-semibold text-slate-900">
                  Score Trend
                </h3>
                {audits.audits.filter((a) => a.score_overall != null)
                  .length < 2 ? (
                  <p className="text-sm text-slate-500">
                    Not enough audits for a trend yet.
                  </p>
                ) : (
                  <ResponsiveContainer width="100%" height={200}>
                    <LineChart
                      data={[...audits.audits]
                        .reverse()
                        .filter((a) => a.score_overall != null)
                        .slice(-6)
                        .map((a) => ({
                          date: formatDate(a.created_at),
                          score: a.score_overall,
                        }))}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" fontSize={11} />
                      <YAxis domain={[0, 100]} fontSize={11} />
                      <Tooltip />
                      <Line
                        type="monotone"
                        dataKey="score"
                        stroke="#4f46e5"
                        strokeWidth={2}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                )}
              </Card>

              <Card>
                <h3 className="mb-4 text-sm font-semibold text-slate-900">
                  Current Category Scores
                </h3>
                {latest ? (
                  <div className="space-y-3">
                    {CATEGORIES.map((cat) => {
                      const v = latest.scores[cat] ?? 0;
                      return (
                        <div key={cat}>
                          <div className="mb-1 flex justify-between text-xs">
                            <span className="capitalize text-slate-600">
                              {cat}
                            </span>
                            <span className="font-mono tnum">{v}</span>
                          </div>
                          <div className="h-2 rounded bg-slate-100">
                            <div
                              className="h-2 rounded"
                              style={{
                                width: `${v}%`,
                                background: scoreColor(v),
                              }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <p className="text-sm text-slate-500">
                    No completed audit yet.
                  </p>
                )}
              </Card>
            </div>

            <Card>
              <h3 className="mb-4 text-sm font-semibold text-slate-900">
                Audit History
              </h3>
              {audits.audits.length === 0 ? (
                <p className="text-sm text-slate-500">
                  No audits yet — trigger one above.
                </p>
              ) : (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-200 text-left text-xs uppercase text-slate-500">
                      <th className="pb-2">Date</th>
                      <th className="pb-2">Status</th>
                      <th className="pb-2">Score</th>
                      <th className="pb-2 text-right">Report</th>
                    </tr>
                  </thead>
                  <tbody>
                    {audits.audits.map((a) => (
                      <tr
                        key={a.id}
                        className="border-b border-slate-100 last:border-0"
                      >
                        <td className="py-3 text-slate-600">
                          {formatDate(a.created_at)}
                        </td>
                        <td className="py-3">
                          <StatusBadge status={a.status} />
                        </td>
                        <td className="py-3 font-mono text-slate-700 tnum">
                          {a.score_overall ?? "—"}
                        </td>
                        <td className="py-3 text-right">
                          <Link
                            href={`/sites/${siteId}/audits/${a.id}`}
                            className="text-brand hover:underline"
                          >
                            View
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </Card>
          </div>
        )}
      </StateView>
    </div>
  );
}

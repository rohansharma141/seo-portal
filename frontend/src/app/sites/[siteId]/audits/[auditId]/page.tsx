"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { PerformancePanel } from "@/components/audits/PerformancePanel";
import { SeverityBadge, StatusBadge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { ScoreGauge } from "@/components/ui/ScoreGauge";
import { PageHeader, StateView } from "@/components/ui/State";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { scoreColor } from "@/lib/utils";
import type { Audit, AuditIssue, AuditIssuesResponse } from "@/types";

const CATEGORIES = [
  "technical",
  "content",
  "eeeat",
  "performance",
  "structure",
] as const;

const RUNNING = ["pending", "crawling", "analysing", "scoring"];
const TABS = ["all", "critical", "warning", "info"] as const;
type Tab = (typeof TABS)[number];

interface ReportData {
  audit: Audit;
  issues: AuditIssue[];
}

export default function AuditReportPage() {
  const { siteId, auditId } = useParams<{
    siteId: string;
    auditId: string;
  }>();
  const [tab, setTab] = useState<Tab>("all");
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [progress, setProgress] = useState<string | null>(null);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);

  const state = useApi<ReportData>(async () => {
    const audit = await api.audits.get(auditId);
    let issues: AuditIssue[] = [];
    if (!RUNNING.includes(audit.status)) {
      const res: AuditIssuesResponse = await api.audits.issues(auditId);
      issues = res.issues;
    }
    return { audit, issues };
  }, [auditId]);

  // Poll /status every 3s while the audit is running (Step 9 requirement).
  useEffect(() => {
    const status = state.data?.audit.status;
    if (!status || !RUNNING.includes(status)) return;
    timer.current = setInterval(async () => {
      try {
        const st = await api.audits.status(auditId);
        setProgress(st.progress_message);
        if (!RUNNING.includes(st.status)) {
          if (timer.current) clearInterval(timer.current);
          setProgress(null);
          await state.reload();
        }
      } catch {
        /* keep polling */
      }
    }, 3000);
    return () => {
      if (timer.current) clearInterval(timer.current);
    };
  }, [state.data?.audit.status, auditId]); // eslint-disable-line react-hooks/exhaustive-deps

  const toggle = (id: string) =>
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });

  return (
    <div>
      <StateView state={state}>
        {({ audit, issues }) => {
          const isRunning = RUNNING.includes(audit.status);
          const visible =
            tab === "all"
              ? issues
              : issues.filter((i) => i.severity === tab);
          const bl = audit.backlinks ?? {};
          const gscMock =
            !audit.gsc_snapshot ||
            (audit.gsc_snapshot as { data_source?: string }).data_source !==
              "gsc_api";

          return (
            <div className="space-y-6">
              <PageHeader
                title="Audit Report"
                subtitle={
                  <span>
                    <Link
                      href={`/sites/${siteId}`}
                      className="text-brand hover:underline"
                    >
                      ← Back to site
                    </Link>
                  </span>
                }
              />

              {isRunning && (
                <Card className="border-amber-200 bg-amber-50">
                  <div className="flex items-center gap-3 text-sm text-amber-800">
                    <span className="h-3 w-3 animate-pulse rounded-full bg-amber-500" />
                    {progress ?? "Audit running…"} — auto-refreshing every
                    3s
                  </div>
                </Card>
              )}

              {audit.status === "failed" && (
                <Card className="border-red-200 bg-red-50">
                  <p className="text-sm text-red-700">
                    This audit failed.
                  </p>
                </Card>
              )}

              {!isRunning && audit.status === "complete" && (
                <>
                  <div className="grid gap-6 md:grid-cols-[auto_1fr]">
                    <Card className="flex items-center justify-center">
                      <ScoreGauge
                        score={audit.scores.overall}
                        size={150}
                        label="Overall"
                      />
                    </Card>
                    <Card>
                      <div className="grid grid-cols-3 gap-4 text-center">
                        <div>
                          <p className="font-mono text-2xl font-semibold tnum">
                            {audit.pages_crawled}
                          </p>
                          <p className="text-xs text-slate-500">
                            Pages crawled
                          </p>
                        </div>
                        <div>
                          <p className="font-mono text-2xl font-semibold tnum text-critical">
                            {audit.issues.critical}
                          </p>
                          <p className="text-xs text-slate-500">
                            Critical
                          </p>
                        </div>
                        <div>
                          <p className="font-mono text-2xl font-semibold tnum text-warning">
                            {audit.issues.warning}
                          </p>
                          <p className="text-xs text-slate-500">Warnings</p>
                        </div>
                      </div>
                      <div className="mt-4">
                        <StatusBadge status={audit.status} />
                      </div>
                    </Card>
                  </div>

                  <Card>
                    <h3 className="mb-2 text-sm font-semibold text-slate-900">
                      AI Summary
                    </h3>
                    <p className="text-sm leading-relaxed text-slate-600">
                      {audit.analysis.summary ?? "No summary available."}
                    </p>
                  </Card>

                  {audit.analysis.quick_wins.length > 0 && (
                    <div>
                      <h3 className="mb-3 text-sm font-semibold text-slate-900">
                        Quick Wins
                      </h3>
                      <div className="grid gap-4 md:grid-cols-3">
                        {audit.analysis.quick_wins.map((q, i) => (
                          <Card
                            key={i}
                            className="border-brand/30 bg-brand-fg"
                          >
                            <p className="text-sm font-semibold text-slate-900">
                              {q.title}
                            </p>
                            <p className="mt-1 text-xs text-slate-600">
                              {q.description}
                            </p>
                            <p className="mt-2 text-[11px] uppercase text-slate-500">
                              effort: {q.effort} · impact: {q.impact}
                            </p>
                          </Card>
                        ))}
                      </div>
                    </div>
                  )}

                  <Card>
                    <h3 className="mb-4 text-sm font-semibold text-slate-900">
                      Score Breakdown
                    </h3>
                    <table className="w-full text-sm">
                      <tbody>
                        {CATEGORIES.map((cat) => {
                          const v = audit.scores[cat] ?? 0;
                          return (
                            <tr
                              key={cat}
                              className="border-b border-slate-100 last:border-0"
                            >
                              <td className="py-2 capitalize text-slate-600">
                                {cat}
                              </td>
                              <td className="py-2">
                                <div className="h-2 w-full rounded bg-slate-100">
                                  <div
                                    className="h-2 rounded"
                                    style={{
                                      width: `${v}%`,
                                      background: scoreColor(v),
                                    }}
                                  />
                                </div>
                              </td>
                              <td className="py-2 pl-4 text-right font-mono tnum">
                                {v}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </Card>

                  {/* Addendum v1.2 — PageSpeed performance panel */}
                  <PerformancePanel pagespeed={audit.pagespeed ?? []} />

                  {/* Addendum v1.1 — Backlinks panel */}
                  <Card
                    className={
                      bl.data_source === "dataforseo"
                        ? ""
                        : "border-amber-200 bg-amber-50"
                    }
                  >
                    <h3 className="mb-3 text-sm font-semibold text-slate-900">
                      Backlinks
                      {bl.data_source === "dataforseo" && (
                        <span className="ml-2 text-xs text-slate-500">
                          via DataForSEO
                        </span>
                      )}
                    </h3>
                    {bl.data_source === "dataforseo" ? (
                      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                        {[
                          ["Domain Rank", bl.domain_rank],
                          ["Ref. Domains", bl.referring_domains],
                          ["Total Links", bl.backlinks_total],
                          ["Broken", bl.broken_backlinks],
                        ].map(([label, val]) => (
                          <div key={String(label)}>
                            <p className="font-mono text-xl font-semibold tnum">
                              {String(val ?? 0)}
                            </p>
                            <p className="text-xs text-slate-500">
                              {label}
                            </p>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-sm text-amber-800">
                        <p>🔗 Backlink data not configured.</p>
                        <p className="mt-1 text-amber-700">
                          {bl.placeholder_note ??
                            "Set DATAFORSEO_LOGIN + DATAFORSEO_PASSWORD to enable."}
                        </p>
                        <Link
                          href="/settings"
                          className="mt-2 inline-block font-medium text-brand hover:underline"
                        >
                          Connect →
                        </Link>
                      </div>
                    )}
                  </Card>

                  <Card
                    className={gscMock ? "border-amber-200 bg-amber-50" : ""}
                  >
                    <h3 className="mb-2 text-sm font-semibold text-slate-900">
                      Google Search Console
                    </h3>
                    {gscMock ? (
                      <p className="text-sm text-amber-800">
                        GSC not connected — showing placeholder data. Set{" "}
                        <code>GSC_CREDENTIALS_PATH</code> to enable.
                      </p>
                    ) : (
                      <pre className="overflow-auto text-xs text-slate-600">
                        {JSON.stringify(audit.gsc_snapshot, null, 2)}
                      </pre>
                    )}
                  </Card>

                  <Card>
                    <div className="mb-4 flex gap-2">
                      {TABS.map((t) => (
                        <button
                          key={t}
                          onClick={() => setTab(t)}
                          className={`rounded-md px-3 py-1 text-xs font-medium capitalize ${
                            tab === t
                              ? "bg-brand text-white"
                              : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                          }`}
                        >
                          {t}
                        </button>
                      ))}
                    </div>
                    {visible.length === 0 ? (
                      <p className="text-sm text-slate-500">
                        No issues in this view.
                      </p>
                    ) : (
                      <ul className="space-y-3">
                        {visible.map((i) => (
                          <li
                            key={i.id}
                            className="rounded-md border border-slate-200 p-3"
                          >
                            <button
                              className="flex w-full items-center justify-between text-left"
                              onClick={() => toggle(i.id)}
                            >
                              <span className="flex items-center gap-2">
                                <SeverityBadge severity={i.severity} />
                                <span className="text-sm font-medium text-slate-900">
                                  {i.rule_name}
                                </span>
                              </span>
                              <span className="text-xs text-slate-400">
                                {expanded.has(i.id) ? "▲" : "▼"}
                              </span>
                            </button>
                            {i.page_url && (
                              <p className="mt-1 truncate text-xs text-slate-500">
                                {i.page_url}
                              </p>
                            )}
                            {expanded.has(i.id) && (
                              <div className="mt-3 space-y-2 text-sm">
                                <p className="text-slate-600">
                                  {i.description}
                                </p>
                                <p className="rounded bg-slate-50 p-2 text-slate-700">
                                  <span className="font-medium">Fix: </span>
                                  {i.fix_suggestion}
                                </p>
                              </div>
                            )}
                          </li>
                        ))}
                      </ul>
                    )}
                  </Card>
                </>
              )}
            </div>
          );
        }}
      </StateView>
    </div>
  );
}

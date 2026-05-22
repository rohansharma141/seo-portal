"use client";

// Addendum v1.2 — PageSpeed Insights panel on the audit report.
import { useState } from "react";

import { Card } from "@/components/ui/Card";
import type { PageSpeedResult } from "@/types";

const GOOD = "#10b981";
const NI = "#f59e0b";
const POOR = "#ef4444";
const NONE = "#94a3b8";

// Google Core Web Vitals thresholds [good-max, needs-improvement-max].
const THRESHOLDS: Record<string, [number, number]> = {
  lcp_ms: [2500, 4000],
  cls: [0.1, 0.25],
  inp_ms: [200, 500],
  fcp_ms: [1800, 3000],
  tbt_ms: [200, 600],
};

function metricColor(key: string, v: number | null | undefined): string {
  if (v === null || v === undefined) return NONE;
  const t = THRESHOLDS[key];
  if (!t) return NONE;
  if (v <= t[0]) return GOOD;
  if (v <= t[1]) return NI;
  return POOR;
}

function scoreColor(score: number): string {
  if (score >= 90) return GOOD;
  if (score >= 50) return NI;
  return POOR;
}

function fmtMs(v: number | null | undefined): string {
  if (v === null || v === undefined) return "—";
  return v >= 1000 ? `${(v / 1000).toFixed(1)} s` : `${Math.round(v)} ms`;
}

function Metric({
  label,
  metricKey,
  value,
  unitless,
}: {
  label: string;
  metricKey: string;
  value: number | null | undefined;
  unitless?: boolean;
}) {
  const color = metricColor(metricKey, value);
  const display =
    value === null || value === undefined
      ? "—"
      : unitless
        ? value.toFixed(3)
        : fmtMs(value);
  return (
    <div className="rounded-md border border-slate-200 px-3 py-2">
      <p className="text-[11px] uppercase tracking-wide text-slate-500">
        {label}
      </p>
      <p className="font-mono text-lg font-semibold tnum" style={{ color }}>
        {display}
      </p>
    </div>
  );
}

export function PerformancePanel({
  pagespeed,
}: {
  pagespeed: PageSpeedResult[];
}) {
  const strategies = Array.from(
    new Set(pagespeed.map((r) => r.strategy)),
  );
  const [strategy, setStrategy] = useState(strategies[0] ?? "mobile");

  if (pagespeed.length === 0) {
    return (
      <Card className="border-amber-200 bg-amber-50">
        <h3 className="text-sm font-semibold text-slate-900">
          Performance (PageSpeed)
        </h3>
        <p className="mt-1 text-sm text-amber-800">
          PageSpeed Insights data was not collected for this audit. Set{" "}
          <code>PSI_ENABLED=true</code> (and optionally a free{" "}
          <code>PSI_API_KEY</code>) to enable real Core Web Vitals.
        </p>
      </Card>
    );
  }

  const allMock = pagespeed.every((r) => r.data_source === "mock");
  const shown = pagespeed.filter((r) => r.strategy === strategy);

  return (
    <Card>
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-900">
          Performance (PageSpeed){" "}
          {!allMock && (
            <span className="text-xs font-normal text-slate-500">
              via Google PSI
            </span>
          )}
        </h3>
        <div className="flex gap-1">
          {(["mobile", "desktop"] as const).map((s) => {
            const has = strategies.includes(s);
            return (
              <button
                key={s}
                disabled={!has}
                onClick={() => setStrategy(s)}
                className={`rounded-md px-2.5 py-1 text-xs font-medium capitalize ${
                  strategy === s
                    ? "bg-brand text-white"
                    : has
                      ? "bg-slate-100 text-slate-600 hover:bg-slate-200"
                      : "cursor-not-allowed bg-slate-50 text-slate-300"
                }`}
                title={has ? "" : "Audits run mobile-first"}
              >
                {s}
              </button>
            );
          })}
        </div>
      </div>

      {allMock && (
        <p className="mb-3 rounded bg-amber-50 px-3 py-2 text-xs text-amber-800">
          PSI was unavailable (rate-limited or timed out) — showing
          placeholder values. The audit still completed.
        </p>
      )}

      <div className="space-y-5">
        {shown.map((r) => (
          <div key={r.url}>
            <div className="mb-2 flex items-center justify-between">
              <p className="truncate text-sm text-slate-600">{r.url}</p>
              <span
                className="ml-3 shrink-0 font-mono text-lg font-semibold tnum"
                style={{ color: scoreColor(r.performance_score) }}
              >
                {r.performance_score}
              </span>
            </div>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
              <Metric label="LCP" metricKey="lcp_ms" value={r.lab.lcp_ms} />
              <Metric
                label="CLS"
                metricKey="cls"
                value={r.lab.cls}
                unitless
              />
              <Metric label="INP" metricKey="inp_ms" value={r.lab.inp_ms} />
              <Metric label="FCP" metricKey="fcp_ms" value={r.lab.fcp_ms} />
              <Metric label="TBT" metricKey="tbt_ms" value={r.lab.tbt_ms} />
            </div>

            {r.field.has_field_data ? (
              <p className="mt-2 text-xs text-slate-500">
                Real-user field data (p75): LCP {fmtMs(r.field.lcp_ms)} ·
                INP {fmtMs(r.field.inp_ms)} · CLS{" "}
                {r.field.cls != null ? r.field.cls.toFixed(3) : "—"}
              </p>
            ) : (
              <p className="mt-2 text-xs text-slate-400">
                Not enough real-user field data yet (normal for new sites)
                — showing lab data only.
              </p>
            )}

            {r.opportunities.length > 0 && (
              <ul className="mt-3 space-y-1">
                {r.opportunities.slice(0, 5).map((o) => (
                  <li
                    key={o.id}
                    className="flex items-center justify-between text-xs"
                  >
                    <span className="truncate text-slate-600">
                      {o.title}
                    </span>
                    <span className="ml-3 shrink-0 font-mono text-slate-500">
                      ~{Math.round(o.savings_ms)} ms
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </div>
    </Card>
  );
}

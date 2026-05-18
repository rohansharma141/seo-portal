"use client";

// Addendum v1.1 — cross-site comparison page.
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState, ErrorState, PageHeader, Spinner } from "@/components/ui/State";
import { api, ApiError } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import type { CrossCompare, SiteListResponse } from "@/types";

const CATEGORIES = [
  "technical",
  "content",
  "eeeat",
  "performance",
  "structure",
] as const;
const PALETTE = ["#4f46e5", "#10b981", "#f59e0b", "#f43f5e", "#8b5cf6"];

function CompareInner() {
  const sp = useSearchParams();
  const sites = useApi<SiteListResponse>(() => api.sites.list(), []);
  const [selected, setSelected] = useState<string[]>([]);
  const [result, setResult] = useState<CrossCompare | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  async function runCompare(ids: string[]) {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      setResult(await api.reports.crossCompare(ids));
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Comparison failed");
    } finally {
      setLoading(false);
    }
  }

  // Bookmarkable: ?site_ids=uuid1,uuid2 auto-runs on load.
  useEffect(() => {
    const fromUrl = sp.get("site_ids");
    if (fromUrl) {
      const ids = fromUrl.split(",").filter(Boolean).slice(0, 5);
      setSelected(ids);
      if (ids.length >= 2) void runCompare(ids);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function toggle(id: string) {
    setSelected((p) => {
      if (p.includes(id)) return p.filter((x) => x !== id);
      if (p.length >= 5) return p;
      return [...p, id];
    });
  }

  function copyLink() {
    const url = `${window.location.origin}/compare?site_ids=${selected.join(",")}`;
    navigator.clipboard?.writeText(url);
    window.history.replaceState(null, "", `?site_ids=${selected.join(",")}`);
    setCopied(true);
  }

  const chartData = result
    ? CATEGORIES.map((cat) => {
        const row: Record<string, string | number> = { category: cat };
        for (const s of result.sites) row[s.site_name] = s.scores[cat] ?? 0;
        return row;
      })
    : [];

  return (
    <div>
      <PageHeader title="Compare Sites" />

      <Card className="mb-6">
        {sites.loading ? (
          <Spinner />
        ) : sites.error ? (
          <ErrorState message={sites.error} onRetry={sites.reload} />
        ) : (
          <>
            <p className="mb-3 text-sm text-slate-600">
              Select 2–5 sites ({selected.length}/5 selected).
            </p>
            <div className="flex flex-wrap gap-2">
              {(sites.data?.sites ?? []).map((s) => {
                const on = selected.includes(s.id);
                const full = !on && selected.length >= 5;
                return (
                  <button
                    key={s.id}
                    disabled={full}
                    onClick={() => toggle(s.id)}
                    className={`rounded-full border px-3 py-1 text-sm transition-colors ${
                      on
                        ? "border-brand bg-brand text-white"
                        : full
                          ? "cursor-not-allowed border-slate-200 text-slate-300"
                          : "border-slate-300 text-slate-700 hover:bg-slate-50"
                    }`}
                  >
                    {s.name}
                  </button>
                );
              })}
            </div>
            <div className="mt-4 flex gap-2">
              <Button
                disabled={selected.length < 2 || loading}
                onClick={() => runCompare(selected)}
              >
                {loading ? "Comparing…" : "Compare →"}
              </Button>
              {result && (
                <Button variant="secondary" onClick={copyLink}>
                  {copied ? "Link copied ✓" : "Copy link"}
                </Button>
              )}
            </div>
          </>
        )}
      </Card>

      {loading && <Spinner label="Running comparison…" />}
      {error && <ErrorState message={error} />}
      {!loading && !error && !result && (
        <EmptyState
          title="No comparison yet"
          hint="Select 2 or more sites and click Compare to see results."
        />
      )}

      {result && (
        <div className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {result.sites.map((s, idx) => (
              <Card key={s.site_id}>
                <div className="flex items-center justify-between">
                  <span
                    className="text-sm font-semibold"
                    style={{ color: PALETTE[idx % PALETTE.length] }}
                  >
                    {s.site_name}
                  </span>
                  <span className="text-xs text-slate-500">
                    rank #{s.rank}
                  </span>
                </div>
                <p className="mt-2 font-mono text-3xl font-semibold tnum text-slate-900">
                  {s.scores.overall ?? 0}
                </p>
                <p className="text-xs text-slate-500">{s.domain}</p>
              </Card>
            ))}
          </div>

          <Card>
            <h3 className="mb-4 text-sm font-semibold text-slate-900">
              Score Comparison
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="category" fontSize={11} />
                <YAxis domain={[0, 100]} fontSize={11} />
                <Tooltip />
                <Legend />
                {result.sites.map((s, idx) => (
                  <Bar
                    key={s.site_id}
                    dataKey={s.site_name}
                    fill={PALETTE[idx % PALETTE.length]}
                  />
                ))}
              </BarChart>
            </ResponsiveContainer>
          </Card>

          <Card>
            <h3 className="mb-4 text-sm font-semibold text-slate-900">
              Category Breakdown
            </h3>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-left text-xs uppercase text-slate-500">
                  <th className="pb-2">Category</th>
                  {result.sites.map((s) => (
                    <th key={s.site_id} className="pb-2">
                      {s.site_name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {CATEGORIES.map((cat) => (
                  <tr
                    key={cat}
                    className="border-b border-slate-100 last:border-0"
                  >
                    <td className="py-2 capitalize text-slate-600">
                      {cat}
                    </td>
                    {result.sites.map((s) => {
                      const leader =
                        result.category_leaders[cat] === s.site_id;
                      return (
                        <td
                          key={s.site_id}
                          className="py-2 font-mono tnum"
                        >
                          {s.scores[cat] ?? 0}
                          {leader && " 🏆"}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>

          <div>
            <h3 className="mb-3 text-sm font-semibold text-slate-900">
              Gaps to Close
            </h3>
            {result.gaps.length === 0 ? (
              <p className="text-sm text-slate-500">
                No category gap exceeds 10 points — sites are closely
                matched.
              </p>
            ) : (
              <div className="grid gap-3 md:grid-cols-2">
                {result.gaps.map((g, i) => (
                  <Card
                    key={i}
                    className={
                      g.gap > 20
                        ? "border-red-300 bg-red-50"
                        : "border-amber-300 bg-amber-50"
                    }
                  >
                    <p className="text-sm font-semibold text-slate-900">
                      {g.site_name} ·{" "}
                      <span className="capitalize">{g.category}</span>
                    </p>
                    <p className="mt-1 text-sm text-slate-600">
                      {g.score} vs leader {g.leader_score} —{" "}
                      <span className="font-semibold">
                        {g.gap} point gap
                      </span>
                    </p>
                    {g.note && (
                      <p className="mt-1 text-xs font-medium text-slate-700">
                        {g.note}
                      </p>
                    )}
                  </Card>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default function ComparePage() {
  return (
    <Suspense fallback={<Spinner />}>
      <CompareInner />
    </Suspense>
  );
}

import { cn } from "@/lib/utils";
import type { ScoreBand } from "@/lib/utils";

const BAND_STYLES: Record<ScoreBand | "healthy", string> = {
  healthy: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
  warning: "bg-amber-50 text-amber-700 ring-amber-600/20",
  critical: "bg-red-50 text-red-700 ring-red-600/20",
  unknown: "bg-slate-100 text-slate-600 ring-slate-500/20",
};

export function StatusBadge({ status }: { status: string }) {
  const map: Record<string, ScoreBand> = {
    healthy: "healthy",
    warning: "warning",
    critical: "critical",
    complete: "healthy",
    failed: "critical",
    pending: "unknown",
    crawling: "warning",
    analysing: "warning",
    scoring: "warning",
    unknown: "unknown",
  };
  const band = map[status] ?? "unknown";
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium capitalize ring-1 ring-inset",
        BAND_STYLES[band],
      )}
    >
      {status}
    </span>
  );
}

const SEVERITY: Record<string, string> = {
  critical: "bg-red-50 text-red-700 ring-red-600/20",
  warning: "bg-amber-50 text-amber-700 ring-amber-600/20",
  info: "bg-slate-100 text-slate-600 ring-slate-500/20",
};

export function SeverityBadge({ severity }: { severity: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium capitalize ring-1 ring-inset",
        SEVERITY[severity] ?? SEVERITY.info,
      )}
    >
      {severity}
    </span>
  );
}

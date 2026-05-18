import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

export type ScoreBand = "healthy" | "warning" | "critical" | "unknown";

/** Section 8 colour bands: Emerald 80+, Amber 50–79, Red <50. */
export function scoreBand(score: number | null | undefined): ScoreBand {
  if (score === null || score === undefined) return "unknown";
  if (score >= 80) return "healthy";
  if (score >= 50) return "warning";
  return "critical";
}

export function scoreColor(score: number | null | undefined): string {
  return {
    healthy: "#10b981",
    warning: "#f59e0b",
    critical: "#ef4444",
    unknown: "#94a3b8",
  }[scoreBand(score)];
}

export function scoreTextClass(score: number | null | undefined): string {
  return {
    healthy: "text-healthy",
    warning: "text-warning",
    critical: "text-critical",
    unknown: "text-slate-400",
  }[scoreBand(score)];
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

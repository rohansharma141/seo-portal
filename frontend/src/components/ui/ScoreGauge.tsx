import { scoreColor } from "@/lib/utils";

/** Circular SVG arc gauge — Section 8. Colour by band. */
export function ScoreGauge({
  score,
  size = 120,
  label,
}: {
  score: number | null | undefined;
  size?: number;
  label?: string;
}) {
  const stroke = size * 0.09;
  const r = (size - stroke) / 2;
  const cx = size / 2;
  const circumference = 2 * Math.PI * r;
  const pct = score == null ? 0 : Math.max(0, Math.min(100, score));
  const color = scoreColor(score);

  return (
    <div className="flex flex-col items-center">
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={cx}
          cy={cx}
          r={r}
          fill="none"
          stroke="#e2e8f0"
          strokeWidth={stroke}
        />
        <circle
          cx={cx}
          cy={cx}
          r={r}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={circumference * (1 - pct / 100)}
        />
      </svg>
      <div
        className="-mt-[60%] flex flex-col items-center"
        style={{ marginTop: -size * 0.62 }}
      >
        <span
          className="font-mono text-2xl font-semibold tnum"
          style={{ color }}
        >
          {score == null ? "—" : Math.round(score)}
        </span>
        {label && (
          <span className="text-[11px] text-slate-500">{label}</span>
        )}
      </div>
    </div>
  );
}

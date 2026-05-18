import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

export function Card({
  className,
  children,
}: {
  className?: string;
  children: ReactNode;
}) {
  return (
    <div
      className={cn(
        "rounded-lg border border-slate-200 bg-content p-5 shadow-sm",
        className,
      )}
    >
      {children}
    </div>
  );
}

export function PagePlaceholder({
  title,
  step,
}: {
  title: string;
  step: string;
}) {
  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold tracking-tight text-slate-900">
        {title}
      </h2>
      <Card className="border-dashed">
        <p className="text-sm text-slate-500">
          Scaffolded (Step 8). Full UI is built in {step}.
        </p>
      </Card>
    </div>
  );
}

import type { ReactNode } from "react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";

export function Spinner({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="flex items-center gap-2 text-sm text-slate-500">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-brand" />
      {label}
    </div>
  );
}

export function ErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <Card className="border-red-200 bg-red-50">
      <p className="text-sm text-red-700">Something went wrong: {message}</p>
      {onRetry && (
        <Button
          variant="secondary"
          className="mt-3"
          onClick={onRetry}
        >
          Retry
        </Button>
      )}
    </Card>
  );
}

export function EmptyState({
  title,
  hint,
  action,
}: {
  title: string;
  hint?: string;
  action?: ReactNode;
}) {
  return (
    <Card className="border-dashed text-center">
      <p className="text-sm font-medium text-slate-700">{title}</p>
      {hint && <p className="mt-1 text-sm text-slate-500">{hint}</p>}
      {action && <div className="mt-4 flex justify-center">{action}</div>}
    </Card>
  );
}

/** Standard loading/error/empty/populated switch. */
export function StateView<T>({
  state,
  isEmpty,
  empty,
  children,
}: {
  state: { data: T | null; loading: boolean; error: string | null; reload: () => void };
  isEmpty?: (data: T) => boolean;
  empty?: ReactNode;
  children: (data: T) => ReactNode;
}) {
  if (state.loading && state.data == null) return <Spinner />;
  if (state.error)
    return <ErrorState message={state.error} onRetry={state.reload} />;
  if (state.data == null) return <Spinner />;
  if (isEmpty && isEmpty(state.data) && empty) return <>{empty}</>;
  return <>{children(state.data)}</>;
}

export function PageHeader({
  title,
  subtitle,
  action,
}: {
  title: string;
  subtitle?: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="mb-6 flex items-start justify-between">
      <div>
        <h2 className="text-xl font-semibold tracking-tight text-slate-900">
          {title}
        </h2>
        {subtitle && (
          <p className="mt-1 text-sm text-slate-500">{subtitle}</p>
        )}
      </div>
      {action}
    </div>
  );
}

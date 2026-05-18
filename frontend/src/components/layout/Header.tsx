const APP_NAME =
  process.env.NEXT_PUBLIC_APP_NAME || "Building10X SEO Portal";

export function Header() {
  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b border-slate-200 bg-content px-6">
      <h1 className="text-sm font-semibold text-slate-900">{APP_NAME}</h1>
      <div className="flex items-center gap-3 text-xs text-slate-500">
        <span className="rounded-full bg-slate-100 px-2 py-1">
          {process.env.NODE_ENV === "production" ? "Production" : "Development"}
        </span>
      </div>
    </header>
  );
}

"use client";

import { Card } from "@/components/ui/Card";
import { PageHeader } from "@/components/ui/State";

interface Integration {
  name: string;
  desc: string;
  envVars: string;
  note?: string;
  docs: string;
}

const INTEGRATIONS: Integration[] = [
  {
    name: "Firecrawl",
    desc: "Website crawling for audits",
    envVars: "FIRECRAWL_API_KEY",
    docs: "https://firecrawl.dev",
  },
  {
    name: "Google Search Console",
    desc: "Search performance snapshot per audit",
    envVars: "GSC_CREDENTIALS_PATH, GSC_SITE_URL",
    docs: "https://search.google.com/search-console",
  },
  {
    name: "Claude API",
    desc: "AI narrative analysis (Haiku 4.5)",
    envVars: "ANTHROPIC_API_KEY",
    docs: "https://console.anthropic.com",
  },
  {
    name: "Resend",
    desc: "Audit-complete email notifications",
    envVars: "RESEND_API_KEY",
    docs: "https://resend.com",
  },
  {
    // Addendum v1.1
    name: "DataForSEO",
    desc: "Backlink data for audit reports",
    envVars: "DATAFORSEO_LOGIN, DATAFORSEO_PASSWORD",
    note: "~₹0.12 per domain lookup · dataforseo.com",
    docs: "https://dataforseo.com",
  },
];

export default function SettingsPage() {
  return (
    <div>
      <PageHeader
        title="Settings"
        subtitle="Integrations and operational defaults are configured via backend environment variables (Section 10)."
      />

      <div className="grid gap-4 md:grid-cols-2">
        {INTEGRATIONS.map((i) => (
          <Card key={i.name}>
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-slate-900">
                {i.name}
              </h3>
              <span className="flex items-center gap-1.5 text-xs text-slate-500">
                <span className="h-2 w-2 rounded-full bg-slate-300" />
                Set via env
              </span>
            </div>
            <p className="mt-1 text-sm text-slate-600">{i.desc}</p>
            <p className="mt-2 text-xs text-slate-500">
              Set{" "}
              <code className="font-mono text-slate-700">{i.envVars}</code>{" "}
              to activate.
            </p>
            {i.note && (
              <p className="mt-1 text-xs text-slate-500">{i.note}</p>
            )}
            <a
              href={i.docs}
              target="_blank"
              rel="noreferrer"
              className="mt-2 inline-block text-xs text-brand hover:underline"
            >
              Docs →
            </a>
          </Card>
        ))}
      </div>

      <Card className="mt-6 border-dashed">
        <h3 className="text-sm font-semibold text-slate-900">
          Operational defaults
        </h3>
        <ul className="mt-2 space-y-1 text-sm text-slate-600">
          <li>
            Notification email — <code>NOTIFICATION_EMAIL</code>
          </li>
          <li>
            Default crawl max pages — set per site (Sites → Add/Edit)
          </li>
          <li>
            Default schedule — set per site (weekly / monthly / manual)
          </li>
        </ul>
        <p className="mt-2 text-xs text-slate-500">
          The backend exposes no settings-write API; these are
          environment- or site-level values.
        </p>
      </Card>
    </div>
  );
}

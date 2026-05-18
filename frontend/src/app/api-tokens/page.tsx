"use client";

import { useState } from "react";

import { StatusBadge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Field, Modal, inputClass } from "@/components/ui/Modal";
import { EmptyState, PageHeader, StateView } from "@/components/ui/State";
import { api, ApiError } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { formatDate } from "@/lib/utils";
import type { TokenCreated, TokenListResponse } from "@/types";

const SCOPES = [
  "audit:read",
  "audit:write",
  "site:read",
  "site:write",
  "webhook:read",
  "webhook:write",
];

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function ApiTokensPage() {
  const state = useApi<TokenListResponse>(() => api.tokens.list(), []);
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [scopes, setScopes] = useState<string[]>([
    "audit:read",
    "audit:write",
    "site:read",
  ]);
  const [created, setCreated] = useState<TokenCreated | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  function toggleScope(s: string) {
    setScopes((p) =>
      p.includes(s) ? p.filter((x) => x !== s) : [...p, s],
    );
  }

  async function create() {
    setErr(null);
    try {
      const res = await api.tokens.create({ name, scopes });
      setCreated(res);
      setOpen(false);
      setName("");
      await state.reload();
    } catch (e) {
      setErr(e instanceof ApiError ? e.detail : "Failed to create token");
    }
  }

  async function revoke(id: string) {
    if (!window.confirm("Revoke this token? It stops working immediately."))
      return;
    await api.tokens.revoke(id);
    await state.reload();
  }

  return (
    <div>
      <PageHeader
        title="API Tokens"
        action={
          <Button onClick={() => setOpen(true)}>Create Token</Button>
        }
      />

      <StateView
        state={state}
        isEmpty={(d) => d.tokens.length === 0}
        empty={
          <EmptyState
            title="No API tokens"
            hint="Create one for PropOS or other programmatic API access."
            action={
              <Button onClick={() => setOpen(true)}>Create Token</Button>
            }
          />
        }
      >
        {(data) => (
          <Card>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-left text-xs uppercase text-slate-500">
                  <th className="pb-2">Name</th>
                  <th className="pb-2">Prefix</th>
                  <th className="pb-2">Scopes</th>
                  <th className="pb-2">Last Used</th>
                  <th className="pb-2">Status</th>
                  <th className="pb-2 text-right">Action</th>
                </tr>
              </thead>
              <tbody>
                {data.tokens.map((t) => (
                  <tr
                    key={t.id}
                    className="border-b border-slate-100 last:border-0"
                  >
                    <td className="py-3 font-medium text-slate-900">
                      {t.name}
                    </td>
                    <td className="py-3 font-mono text-slate-600">
                      {t.token_prefix}…
                    </td>
                    <td className="py-3 text-xs text-slate-500">
                      {t.scopes.join(", ")}
                    </td>
                    <td className="py-3 text-slate-600">
                      {formatDate(t.last_used_at)}
                    </td>
                    <td className="py-3">
                      <StatusBadge
                        status={t.is_active ? "healthy" : "failed"}
                      />
                    </td>
                    <td className="py-3 text-right">
                      {t.is_active && (
                        <button
                          onClick={() => revoke(t.id)}
                          className="text-critical hover:underline"
                        >
                          Revoke
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        )}
      </StateView>

      <Card className="mt-6">
        <h3 className="mb-2 text-sm font-semibold text-slate-900">
          API Usage
        </h3>
        <p className="text-sm text-slate-600">
          Base URL: <code className="font-mono">{API_BASE}/api/v1</code>
        </p>
        <p className="mt-1 text-sm text-slate-600">
          Auth header:{" "}
          <code className="font-mono">Authorization: Bearer pse_…</code>
        </p>
        <a
          href={`${API_BASE}/docs`}
          target="_blank"
          rel="noreferrer"
          className="mt-2 inline-block text-sm text-brand hover:underline"
        >
          Open interactive API docs →
        </a>
      </Card>

      <Modal
        open={open}
        onClose={() => setOpen(false)}
        title="Create API Token"
      >
        <Field label="Name">
          <input
            className={inputClass}
            placeholder="PropOS Production"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </Field>
        <Field label="Scopes">
          <div className="space-y-1">
            {SCOPES.map((s) => (
              <label
                key={s}
                className="flex items-center gap-2 text-sm text-slate-700"
              >
                <input
                  type="checkbox"
                  checked={scopes.includes(s)}
                  onChange={() => toggleScope(s)}
                />
                <span className="font-mono">{s}</span>
              </label>
            ))}
          </div>
        </Field>
        {err && <p className="mb-3 text-sm text-critical">{err}</p>}
        <div className="flex justify-end gap-2">
          <Button variant="secondary" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button onClick={create} disabled={!name || scopes.length === 0}>
            Create
          </Button>
        </div>
      </Modal>

      <Modal
        open={!!created}
        onClose={() => {
          setCreated(null);
          setCopied(false);
        }}
        title="Token created"
      >
        <p className="mb-2 text-sm text-critical">
          {created?.warning}
        </p>
        <pre className="overflow-auto rounded bg-slate-900 p-3 font-mono text-xs text-emerald-300">
          {created?.token}
        </pre>
        <Button
          className="mt-3"
          variant="secondary"
          onClick={() => {
            if (created) navigator.clipboard?.writeText(created.token);
            setCopied(true);
          }}
        >
          {copied ? "Copied ✓" : "Copy token"}
        </Button>
      </Modal>
    </div>
  );
}

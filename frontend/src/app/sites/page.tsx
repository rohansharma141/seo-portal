"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Field, Modal, inputClass } from "@/components/ui/Modal";
import { EmptyState, PageHeader, StateView } from "@/components/ui/State";
import { api, ApiError } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { formatDate } from "@/lib/utils";
import type { Site, SiteCreate, SiteListResponse } from "@/types";

const EMPTY: SiteCreate = {
  name: "",
  domain: "",
  url: "",
  site_type: "other",
  schedule: "weekly",
  max_pages: 100,
};

type Mode = "create" | "edit";

export default function SitesPage() {
  const state = useApi<SiteListResponse>(() => api.sites.list(), []);
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState<Mode>("create");
  const [editId, setEditId] = useState<string | null>(null);
  const [form, setForm] = useState<SiteCreate>(EMPTY);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [busyAudit, setBusyAudit] = useState<string | null>(null);
  const [flash, setFlash] = useState<string | null>(null);

  const filtered = useMemo(() => {
    const sites = state.data?.sites ?? [];
    const q = query.trim().toLowerCase();
    if (!q) return sites;
    return sites.filter(
      (s) =>
        s.name.toLowerCase().includes(q) ||
        s.domain.toLowerCase().includes(q),
    );
  }, [state.data, query]);

  function openCreate() {
    setMode("create");
    setEditId(null);
    setForm(EMPTY);
    setFormError(null);
    setOpen(true);
  }

  function openEdit(s: Site) {
    setMode("edit");
    setEditId(s.id);
    setForm({
      name: s.name,
      domain: s.domain,
      url: s.url,
      site_type: s.site_type as SiteCreate["site_type"],
      schedule: s.schedule as SiteCreate["schedule"],
      max_pages: 100,
    });
    setFormError(null);
    setOpen(true);
  }

  async function submit() {
    setSaving(true);
    setFormError(null);
    try {
      if (mode === "create") {
        await api.sites.create(form);
      } else if (editId) {
        // domain is immutable — send only the editable fields
        await api.sites.update(editId, {
          name: form.name,
          url: form.url,
          site_type: form.site_type,
          schedule: form.schedule,
          max_pages: form.max_pages,
        });
      }
      setOpen(false);
      setForm(EMPTY);
      await state.reload();
    } catch (e) {
      setFormError(
        e instanceof ApiError ? e.detail : "Failed to save site",
      );
    } finally {
      setSaving(false);
    }
  }

  async function remove(id: string, name: string) {
    if (!window.confirm(`Remove "${name}"? (soft delete)`)) return;
    await api.sites.remove(id);
    await state.reload();
  }

  async function runAudit(id: string, name: string) {
    setBusyAudit(id);
    setFlash(null);
    try {
      await api.audits.trigger(id, "manual");
      setFlash(`Audit queued for "${name}" — open the site to watch progress.`);
      await state.reload();
    } catch (e) {
      setFlash(
        e instanceof ApiError
          ? `Could not start audit: ${e.detail}`
          : "Could not start audit.",
      );
    } finally {
      setBusyAudit(null);
    }
  }

  return (
    <div>
      <PageHeader
        title="Sites"
        action={<Button onClick={openCreate}>+ Add New Site</Button>}
      />

      {flash && (
        <Card className="mb-4 border-brand/30 bg-brand-fg">
          <p className="text-sm text-slate-700">{flash}</p>
        </Card>
      )}

      <input
        className={`${inputClass} mb-4 max-w-sm`}
        placeholder="Search by name or domain…"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />

      <StateView
        state={state}
        isEmpty={(d) => d.sites.length === 0}
        empty={
          <EmptyState
            title="No sites registered"
            hint="Add a website to start auditing it."
            action={<Button onClick={openCreate}>+ Add New Site</Button>}
          />
        }
      >
        {() => (
          <Card>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-left text-xs uppercase text-slate-500">
                  <th className="pb-2">Name</th>
                  <th className="pb-2">Domain</th>
                  <th className="pb-2">Type</th>
                  <th className="pb-2">Schedule</th>
                  <th className="pb-2">Score</th>
                  <th className="pb-2">Last Audited</th>
                  <th className="pb-2 text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((s) => (
                  <tr
                    key={s.id}
                    className="border-b border-slate-100 last:border-0"
                  >
                    <td className="py-3 font-medium text-slate-900">
                      {s.name}
                    </td>
                    <td className="py-3 text-slate-600">{s.domain}</td>
                    <td className="py-3 capitalize text-slate-600">
                      {s.site_type}
                    </td>
                    <td className="py-3 capitalize text-slate-600">
                      {s.schedule}
                    </td>
                    <td className="py-3 font-mono text-slate-700 tnum">
                      {s.last_score ?? "—"}
                    </td>
                    <td className="py-3 text-slate-600">
                      {formatDate(s.last_audit_at)}
                    </td>
                    <td className="py-3">
                      <div className="flex justify-end gap-3">
                        <button
                          onClick={() => runAudit(s.id, s.name)}
                          disabled={busyAudit === s.id}
                          className="font-medium text-brand hover:underline disabled:opacity-50"
                        >
                          {busyAudit === s.id ? "Queuing…" : "Audit"}
                        </button>
                        <Link
                          href={`/sites/${s.id}`}
                          className="text-slate-600 hover:underline"
                        >
                          View
                        </Link>
                        <button
                          onClick={() => openEdit(s)}
                          className="text-slate-600 hover:underline"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => remove(s.id, s.name)}
                          className="text-critical hover:underline"
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
                {filtered.length === 0 && (
                  <tr>
                    <td
                      colSpan={7}
                      className="py-6 text-center text-slate-500"
                    >
                      No sites match “{query}”.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </Card>
        )}
      </StateView>

      <Modal
        open={open}
        onClose={() => setOpen(false)}
        title={mode === "create" ? "Add New Site" : "Edit Site"}
      >
        <Field label="Name">
          <input
            className={inputClass}
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
          />
        </Field>
        <Field label={mode === "edit" ? "Domain (cannot be changed)" : "Domain"}>
          <input
            className={inputClass}
            placeholder="kedar.estate"
            value={form.domain}
            disabled={mode === "edit"}
            onChange={(e) => setForm({ ...form, domain: e.target.value })}
          />
        </Field>
        <Field label="URL">
          <input
            className={inputClass}
            placeholder="https://kedar.estate"
            value={form.url}
            onChange={(e) => setForm({ ...form, url: e.target.value })}
          />
        </Field>
        <Field label="Site type">
          <select
            className={inputClass}
            value={form.site_type}
            onChange={(e) =>
              setForm({
                ...form,
                site_type: e.target.value as SiteCreate["site_type"],
              })
            }
          >
            <option value="brokerage">brokerage</option>
            <option value="saas">saas</option>
            <option value="broker_landing">broker_landing</option>
            <option value="other">other</option>
          </select>
        </Field>
        <Field label="Schedule">
          <select
            className={inputClass}
            value={form.schedule}
            onChange={(e) =>
              setForm({
                ...form,
                schedule: e.target.value as SiteCreate["schedule"],
              })
            }
          >
            <option value="weekly">weekly</option>
            <option value="monthly">monthly</option>
            <option value="manual">manual</option>
          </select>
        </Field>
        <Field label="Max pages">
          <input
            type="number"
            className={inputClass}
            value={form.max_pages}
            onChange={(e) =>
              setForm({ ...form, max_pages: Number(e.target.value) })
            }
          />
        </Field>
        {formError && (
          <p className="mb-3 text-sm text-critical">{formError}</p>
        )}
        <div className="flex justify-end gap-2">
          <Button variant="secondary" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button onClick={submit} disabled={saving}>
            {saving
              ? "Saving…"
              : mode === "create"
                ? "Create"
                : "Save changes"}
          </Button>
        </div>
      </Modal>
    </div>
  );
}

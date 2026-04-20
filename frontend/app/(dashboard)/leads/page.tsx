"use client";
import { useEffect, useState, useCallback } from "react";
import { leadsApi } from "@/lib/api";
import { Lead } from "@/lib/types";
import Header from "@/components/layout/Header";
import { Plus, Search, Filter, Flame, Thermometer, Snowflake,
  Phone, Mail, MessageSquare, RefreshCw, Trash2, Eye, X } from "lucide-react";
import clsx from "clsx";

const TEMP_FILTERS = [
  { label: "All", value: "" },
  { label: "Hot", value: "hot", icon: Flame, color: "text-red-600 bg-red-50" },
  { label: "Warm", value: "warm", icon: Thermometer, color: "text-amber-600 bg-amber-50" },
  { label: "Cold", value: "cold", icon: Snowflake, color: "text-blue-600 bg-blue-50" },
];

const SOURCE_ICONS: Record<string, string> = {
  facebook: "🔵", whatsapp: "🟢", email: "📧", website: "🌐", manual: "✏️",
};

export default function LeadsPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [tempFilter, setTempFilter] = useState("");
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [showCreate, setShowCreate] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await leadsApi.list({ page, limit: 20, search, temperature: tempFilter || undefined });
      setLeads(res.data.leads);
      setTotal(res.data.total);
    } finally {
      setLoading(false);
    }
  }, [page, search, tempFilter]);

  useEffect(() => { load(); }, [load]);

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this lead?")) return;
    await leadsApi.delete(id);
    setSelectedLead(null);
    load();
  };

  const handleReAnalyze = async (id: string) => {
    await leadsApi.reAnalyze(id);
    setTimeout(load, 2000); // re-load after AI analysis
  };

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <Header title="Leads" subtitle={`${total} total leads`} />

      <div className="flex-1 flex flex-col overflow-hidden p-3 lg:p-6 gap-3 lg:gap-4">
        {/* Toolbar */}
        <div className="flex flex-col sm:flex-row gap-2 sm:gap-3 items-stretch sm:items-center">
          {/* Search */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              className="input pl-9 bg-white" placeholder="Search leads..." />
          </div>

          {/* Temperature filters */}
          <div className="flex gap-1 bg-white border border-slate-200 rounded-lg p-1 overflow-x-auto">
            {TEMP_FILTERS.map(({ label, value, icon: Icon, color }) => (
              <button key={value} onClick={() => { setTempFilter(value); setPage(1); }}
                className={clsx(
                  "flex items-center gap-1 px-2 lg:px-3 py-1.5 rounded-md text-xs lg:text-sm font-medium transition-all whitespace-nowrap",
                  tempFilter === value ? "bg-indigo-600 text-white shadow-sm" : "text-slate-600 hover:bg-slate-50"
                )}>
                {Icon && <Icon className={clsx("w-3 h-3 lg:w-3.5 lg:h-3.5", tempFilter !== value && color?.split(" ")[0])} />}
                {label}
              </button>
            ))}
          </div>

          <button onClick={() => setShowCreate(true)} className="btn-primary">
            <Plus className="w-4 h-4" /> Add Lead
          </button>
        </div>

        {/* Mobile: card list | Desktop: table */}
        <div className="flex-1 overflow-auto">
          {/* ── Mobile card list ─────────────────────────── */}
          <div className="lg:hidden space-y-2">
            {loading ? (
              [...Array(5)].map((_, i) => (
                <div key={i} className="bg-white rounded-xl border border-slate-200 p-4 animate-pulse">
                  <div className="h-4 bg-slate-100 rounded w-1/2 mb-2" />
                  <div className="h-3 bg-slate-100 rounded w-1/3" />
                </div>
              ))
            ) : leads.length === 0 ? (
              <div className="text-center py-16 text-slate-400">
                <p className="font-medium">No leads found</p>
                <p className="text-sm mt-1">Add your first lead to get started</p>
              </div>
            ) : leads.map((lead) => (
              <div key={lead.id} onClick={() => setSelectedLead(lead)}
                className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm active:bg-slate-50">
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div>
                    <p className="font-semibold text-slate-900">{lead.name}</p>
                    <p className="text-xs text-slate-400">{lead.email || lead.phone || "—"}</p>
                  </div>
                  <TempBadge temp={lead.temperature} />
                </div>
                <div className="flex items-center gap-3 flex-wrap">
                  <span className="text-xs text-slate-500">{SOURCE_ICONS[lead.source]} {lead.source}</span>
                  <ScoreBar score={lead.score} />
                  <StatusBadge status={lead.status} />
                </div>
              </div>
            ))}
          </div>

          {/* ── Desktop table ─────────────────────────────── */}
          <div className="hidden lg:block rounded-xl border border-slate-200 bg-white shadow-card">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200">
                {["Lead", "Source", "Score", "Temperature", "Intent", "Status", "Created", "Actions"].map(h => (
                  <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                [...Array(8)].map((_, i) => (
                  <tr key={i}>
                    {[...Array(8)].map((_, j) => (
                      <td key={j} className="px-4 py-3"><div className="h-4 bg-slate-100 rounded animate-pulse" /></td>
                    ))}
                  </tr>
                ))
              ) : leads.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-4 py-16 text-center text-slate-400">
                    <Users2 className="w-8 h-8 mx-auto mb-2 opacity-30" />
                    <p>No leads found. Try adjusting filters or add your first lead.</p>
                  </td>
                </tr>
              ) : leads.map((lead) => (
                <tr key={lead.id} className="hover:bg-slate-50 transition-colors cursor-pointer"
                  onClick={() => setSelectedLead(lead)}>
                  <td className="px-4 py-3">
                    <div className="font-medium text-slate-900">{lead.name}</div>
                    <div className="text-xs text-slate-400">{lead.email || lead.phone || "—"}</div>
                  </td>
                  <td className="px-4 py-3">
                    <span className="capitalize">{SOURCE_ICONS[lead.source] || "?"} {lead.source}</span>
                  </td>
                  <td className="px-4 py-3">
                    <ScoreBar score={lead.score} />
                  </td>
                  <td className="px-4 py-3">
                    <TempBadge temp={lead.temperature} />
                  </td>
                  <td className="px-4 py-3">
                    <span className="capitalize text-xs bg-slate-100 px-2 py-0.5 rounded-full">{lead.intent}</span>
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={lead.status} />
                  </td>
                  <td className="px-4 py-3 text-slate-400 text-xs">
                    {new Date(lead.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                    <div className="flex gap-1">
                      <button onClick={() => handleReAnalyze(lead.id)}
                        className="p-1.5 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-md transition-colors"
                        title="Re-analyze with AI">
                        <RefreshCw className="w-3.5 h-3.5" />
                      </button>
                      <button onClick={() => handleDelete(lead.id)}
                        className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors"
                        title="Delete">
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          </div>{/* end desktop table */}
        </div>{/* end overflow-auto */}

        {/* Pagination */}
        {total > 20 && (
          <div className="flex items-center justify-between">
            <p className="text-sm text-slate-500">
              Showing {(page - 1) * 20 + 1}–{Math.min(page * 20, total)} of {total} leads
            </p>
            <div className="flex gap-2">
              <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}
                className="btn-secondary disabled:opacity-40">Previous</button>
              <button onClick={() => setPage(p => p + 1)} disabled={page * 20 >= total}
                className="btn-secondary disabled:opacity-40">Next</button>
            </div>
          </div>
        )}
      </div>

      {/* Lead Detail Panel */}
      {selectedLead && (
        <LeadDetailPanel lead={selectedLead} onClose={() => setSelectedLead(null)} onRefresh={load} />
      )}

      {/* Create Lead Modal */}
      {showCreate && <CreateLeadModal onClose={() => setShowCreate(false)} onCreated={load} />}
    </div>
  );
}

function ScoreBar({ score }: { score: number }) {
  const color = score >= 70 ? "bg-red-500" : score >= 40 ? "bg-amber-500" : "bg-blue-400";
  return (
    <div className="flex items-center gap-2">
      <div className="w-20 h-1.5 bg-slate-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${score}%` }} />
      </div>
      <span className="text-xs font-medium text-slate-700">{Math.round(score)}</span>
    </div>
  );
}

function TempBadge({ temp }: { temp: string }) {
  if (temp === "hot") return <span className="badge-hot"><Flame className="w-3 h-3" /> Hot</span>;
  if (temp === "warm") return <span className="badge-warm"><Thermometer className="w-3 h-3" /> Warm</span>;
  return <span className="badge-cold"><Snowflake className="w-3 h-3" /> Cold</span>;
}

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, string> = {
    new: "badge-new", converted: "badge-converted",
    contacted: "bg-purple-100 text-purple-700 inline-flex px-2 py-0.5 rounded-full text-xs font-medium",
    qualified: "bg-teal-100 text-teal-700 inline-flex px-2 py-0.5 rounded-full text-xs font-medium",
    lost: "bg-red-100 text-red-700 inline-flex px-2 py-0.5 rounded-full text-xs font-medium",
  };
  return <span className={map[status] || "badge-new capitalize"}>{status}</span>;
}

// ── Lead Detail Side Panel ────────────────────────────────────────────────────
function LeadDetailPanel({ lead, onClose, onRefresh }: {
  lead: Lead; onClose: () => void; onRefresh: () => void;
}) {
  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-white border-l border-slate-200 shadow-xl z-50 flex flex-col overflow-auto">
      <div className="flex items-center justify-between px-5 py-4 border-b border-slate-200">
        <h3 className="font-semibold text-slate-900">Lead Details</h3>
        <button onClick={onClose} className="text-slate-400 hover:text-slate-700">
          <X className="w-5 h-5" />
        </button>
      </div>
      <div className="p-5 space-y-5 flex-1 overflow-auto">
        {/* Header */}
        <div className="flex items-start gap-3">
          <div className="w-12 h-12 bg-indigo-100 rounded-full flex items-center justify-center text-indigo-700 font-bold text-lg">
            {lead.name[0].toUpperCase()}
          </div>
          <div>
            <h4 className="font-semibold text-slate-900">{lead.name}</h4>
            <TempBadge temp={lead.temperature} />
          </div>
        </div>

        {/* Contact */}
        <div className="space-y-2">
          {lead.phone && (
            <div className="flex items-center gap-2 text-sm text-slate-600">
              <Phone className="w-4 h-4 text-slate-400" /> {lead.phone}
            </div>
          )}
          {lead.email && (
            <div className="flex items-center gap-2 text-sm text-slate-600">
              <Mail className="w-4 h-4 text-slate-400" /> {lead.email}
            </div>
          )}
        </div>

        {/* Score */}
        <div className="card bg-slate-50 border-slate-100">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-slate-700">AI Score</span>
            <span className="text-2xl font-bold text-indigo-600">{Math.round(lead.score)}</span>
          </div>
          <div className="w-full h-2 bg-slate-200 rounded-full overflow-hidden">
            <div className="h-full bg-gradient-to-r from-blue-400 via-amber-400 to-red-500 rounded-full"
              style={{ width: `${lead.score}%` }} />
          </div>
        </div>

        {/* AI Analysis */}
        {lead.ai_summary && (
          <div>
            <h5 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">AI Summary</h5>
            <p className="text-sm text-slate-700 bg-blue-50 p-3 rounded-lg">{lead.ai_summary}</p>
          </div>
        )}
        {lead.ai_suggested_action && (
          <div>
            <h5 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Suggested Action</h5>
            <p className="text-sm text-slate-700 bg-green-50 p-3 rounded-lg border border-green-100">
              ✅ {lead.ai_suggested_action}
            </p>
          </div>
        )}
        {lead.ai_generated_reply && (
          <div>
            <h5 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">AI Reply Draft</h5>
            <p className="text-sm text-slate-700 bg-indigo-50 p-3 rounded-lg border border-indigo-100 italic">
              "{lead.ai_generated_reply}"
            </p>
          </div>
        )}

        {/* Message */}
        {lead.message && (
          <div>
            <h5 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Original Message</h5>
            <p className="text-sm text-slate-600 bg-slate-50 p-3 rounded-lg">{lead.message}</p>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Create Lead Modal ─────────────────────────────────────────────────────────
function CreateLeadModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [form, setForm] = useState({ name: "", phone: "", email: "", message: "", source: "website" });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await leadsApi.create(form);
      onCreated();
      onClose();
    } catch {
      alert("Failed to create lead");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md">
        <div className="flex items-center justify-between p-6 border-b border-slate-200">
          <h3 className="font-semibold text-slate-900">Add New Lead</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700">
            <X className="w-5 h-5" />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {[
            { name: "name", label: "Full Name *", type: "text", required: true },
            { name: "phone", label: "Phone", type: "tel", required: false },
            { name: "email", label: "Email", type: "email", required: false },
            { name: "message", label: "Message / Inquiry", type: "text", required: false },
          ].map(({ name, label, type, required }) => (
            <div key={name}>
              <label className="block text-sm font-medium text-slate-700 mb-1">{label}</label>
              <input type={type} value={(form as Record<string,string>)[name]} required={required}
                onChange={(e) => setForm(f => ({ ...f, [name]: e.target.value }))}
                className="input" />
            </div>
          ))}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Source</label>
            <select value={form.source} onChange={(e) => setForm(f => ({ ...f, source: e.target.value }))}
              className="input">
              {["website", "whatsapp", "facebook", "email", "manual"].map(s => (
                <option key={s} value={s} className="capitalize">{s}</option>
              ))}
            </select>
          </div>
          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary flex-1 justify-center">Cancel</button>
            <button type="submit" disabled={loading} className="btn-primary flex-1 justify-center">
              {loading ? "Creating..." : "Create Lead"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// Icon helper (inline)
function Users2(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg {...props} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" />
    </svg>
  );
}

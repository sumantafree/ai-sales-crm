"use client";
import { useEffect, useState } from "react";
import { automationsApi } from "@/lib/api";
import { Automation } from "@/lib/types";
import Header from "@/components/layout/Header";
import { Plus, X, Bot, Zap, Mail, MessageSquare, Play, Pause, Trash2, Sparkles } from "lucide-react";

const TRIGGER_LABELS: Record<string, string> = {
  lead_created: "New Lead Created",
  score_above: "Score Above Threshold",
  score_below: "Score Below Threshold",
  no_reply_24h: "No Reply in 24 Hours",
  no_reply_48h: "No Reply in 48 Hours",
  keyword_detected: "Keyword Detected",
  source_match: "Source Matches",
  intent_match: "Intent Matches",
  temperature_match: "Temperature Matches",
};

const ACTION_LABELS: Record<string, { label: string; icon: React.ReactNode; color: string }> = {
  send_whatsapp: { label: "Send WhatsApp", icon: <MessageSquare className="w-3.5 h-3.5" />, color: "bg-green-100 text-green-700" },
  send_email: { label: "Send Email", icon: <Mail className="w-3.5 h-3.5" />, color: "bg-blue-100 text-blue-700" },
  ai_reply: { label: "AI Reply", icon: <Bot className="w-3.5 h-3.5" />, color: "bg-purple-100 text-purple-700" },
  update_status: { label: "Update Status", icon: <Zap className="w-3.5 h-3.5" />, color: "bg-amber-100 text-amber-700" },
  notify_team: { label: "Notify Team", icon: <Zap className="w-3.5 h-3.5" />, color: "bg-indigo-100 text-indigo-700" },
};

export default function AutomationsPage() {
  const [automations, setAutomations] = useState<Automation[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const res = await automationsApi.list();
      setAutomations(res.data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleSeedDefaults = async () => {
    await automationsApi.seedDefaults();
    load();
  };

  const handleToggle = async (a: Automation) => {
    await automationsApi.update(a.id, { status: a.status === "active" ? "inactive" : "active" });
    load();
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this automation?")) return;
    await automationsApi.delete(id);
    load();
  };

  return (
    <div className="flex flex-col h-full overflow-auto">
      <Header title="Automations" subtitle="Rule-based triggers to automate your follow-ups" />
      <div className="flex-1 p-6">
        <div className="flex justify-between items-center mb-6">
          <button onClick={handleSeedDefaults}
            className="btn-secondary text-sm gap-2">
            <Sparkles className="w-4 h-4 text-indigo-500" /> Load Default Flows
          </button>
          <button onClick={() => setShowCreate(true)} className="btn-primary">
            <Plus className="w-4 h-4" /> New Automation
          </button>
        </div>

        {loading ? (
          <div className="space-y-3 animate-pulse">
            {[...Array(4)].map((_, i) => <div key={i} className="h-24 bg-slate-100 rounded-xl" />)}
          </div>
        ) : automations.length === 0 ? (
          <div className="text-center py-20 text-slate-400">
            <Bot className="w-10 h-10 mx-auto mb-3 opacity-30" />
            <p className="font-medium">No automations yet</p>
            <p className="text-sm mt-1">Load default flows or create custom automations</p>
            <button onClick={handleSeedDefaults} className="btn-primary mt-4">
              <Sparkles className="w-4 h-4" /> Load Default Flows
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {automations.map((a) => {
              const actionInfo = ACTION_LABELS[a.action] || { label: a.action, icon: <Zap className="w-3.5 h-3.5" />, color: "bg-slate-100 text-slate-600" };
              return (
                <div key={a.id} className={`card flex items-center gap-5 transition-all ${a.status === "inactive" ? "opacity-60" : ""}`}>
                  <div className="w-10 h-10 rounded-xl bg-indigo-50 flex items-center justify-center flex-shrink-0">
                    <Bot className="w-5 h-5 text-indigo-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <h4 className="font-semibold text-slate-900 truncate">{a.name}</h4>
                      <span className={`text-xs px-1.5 py-0.5 rounded-full font-medium ${a.status === "active" ? "bg-green-100 text-green-700" : "bg-slate-100 text-slate-500"}`}>
                        {a.status}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 mt-0.5">{a.description}</p>
                    <div className="flex items-center gap-3 mt-2">
                      <div className="flex items-center gap-1.5 text-xs bg-slate-100 px-2 py-1 rounded-md text-slate-600">
                        <Zap className="w-3 h-3" />
                        <span>IF: {TRIGGER_LABELS[a.trigger] || a.trigger}</span>
                      </div>
                      <span className="text-slate-300">→</span>
                      <div className={`flex items-center gap-1.5 text-xs px-2 py-1 rounded-md ${actionInfo.color}`}>
                        {actionInfo.icon}
                        <span>THEN: {actionInfo.label}</span>
                      </div>
                      {parseInt(a.delay_minutes) > 0 && (
                        <>
                          <span className="text-slate-300">·</span>
                          <span className="text-xs text-slate-400">
                            Delay: {parseInt(a.delay_minutes) >= 60
                              ? `${Math.round(parseInt(a.delay_minutes) / 60)}h`
                              : `${a.delay_minutes}m`}
                          </span>
                        </>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <span className="text-xs text-slate-400">{a.run_count} runs</span>
                    <button onClick={() => handleToggle(a)}
                      className={`p-1.5 rounded-lg transition-colors ${a.status === "active"
                        ? "text-amber-600 hover:bg-amber-50"
                        : "text-green-600 hover:bg-green-50"}`}>
                      {a.status === "active" ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                    </button>
                    <button onClick={() => handleDelete(a.id)}
                      className="p-1.5 text-red-400 hover:bg-red-50 rounded-lg transition-colors">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
      {showCreate && <CreateAutomationModal onClose={() => setShowCreate(false)} onCreated={load} />}
    </div>
  );
}

function CreateAutomationModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [form, setForm] = useState({
    name: "", trigger: "lead_created", action: "send_whatsapp",
    delay_minutes: "0", description: "",
    trigger_config: "{}", action_config: "{}",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true); setError("");
    try {
      await automationsApi.create({
        name: form.name, trigger: form.trigger, action: form.action,
        delay_minutes: form.delay_minutes, description: form.description,
        trigger_config: JSON.parse(form.trigger_config || "{}"),
        action_config: JSON.parse(form.action_config || "{}"),
      });
      onCreated(); onClose();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      setError(e.response?.data?.detail || "Failed to create automation");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-screen overflow-auto">
        <div className="flex items-center justify-between p-6 border-b border-slate-200">
          <h3 className="font-semibold text-slate-900">Create Automation</h3>
          <button onClick={onClose}><X className="w-5 h-5 text-slate-400" /></button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && <div className="bg-red-50 text-red-700 px-3 py-2 rounded-lg text-sm">{error}</div>}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Name *</label>
            <input value={form.name} required onChange={(e) => setForm(f => ({ ...f, name: e.target.value }))} className="input" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Description</label>
            <input value={form.description} onChange={(e) => setForm(f => ({ ...f, description: e.target.value }))} className="input" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Trigger (IF)</label>
              <select value={form.trigger} onChange={(e) => setForm(f => ({ ...f, trigger: e.target.value }))} className="input">
                {Object.entries(TRIGGER_LABELS).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Action (THEN)</label>
              <select value={form.action} onChange={(e) => setForm(f => ({ ...f, action: e.target.value }))} className="input">
                {Object.entries(ACTION_LABELS).map(([v, { label }]) => <option key={v} value={v}>{label}</option>)}
              </select>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Delay (minutes)</label>
            <input type="number" value={form.delay_minutes} min="0"
              onChange={(e) => setForm(f => ({ ...f, delay_minutes: e.target.value }))} className="input" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Trigger Config (JSON)</label>
            <input value={form.trigger_config} onChange={(e) => setForm(f => ({ ...f, trigger_config: e.target.value }))}
              className="input font-mono text-xs" placeholder='e.g. {"threshold": 70}' />
          </div>
          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary flex-1 justify-center">Cancel</button>
            <button type="submit" disabled={loading} className="btn-primary flex-1 justify-center">
              {loading ? "Creating..." : "Create"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

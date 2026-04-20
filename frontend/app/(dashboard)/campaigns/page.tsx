"use client";
import { useEffect, useState } from "react";
import { campaignsApi } from "@/lib/api";
import { Campaign } from "@/lib/types";
import Header from "@/components/layout/Header";
import { Plus, X, TrendingUp, Users, CheckCircle2, BarChart3 } from "lucide-react";

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const res = await campaignsApi.list();
      setCampaigns(res.data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this campaign?")) return;
    await campaignsApi.delete(id);
    load();
  };

  const statusColor: Record<string, string> = {
    active: "bg-green-100 text-green-700",
    paused: "bg-amber-100 text-amber-700",
    draft: "bg-slate-100 text-slate-600",
    completed: "bg-blue-100 text-blue-700",
  };

  return (
    <div className="flex flex-col h-full overflow-auto">
      <Header title="Campaigns" subtitle="Track your lead generation campaigns" />
      <div className="flex-1 p-6">
        <div className="flex justify-between items-center mb-6">
          <div />
          <button onClick={() => setShowCreate(true)} className="btn-primary">
            <Plus className="w-4 h-4" /> New Campaign
          </button>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 animate-pulse">
            {[...Array(3)].map((_, i) => <div key={i} className="h-48 bg-slate-100 rounded-xl" />)}
          </div>
        ) : campaigns.length === 0 ? (
          <div className="text-center py-20 text-slate-400">
            <BarChart3 className="w-10 h-10 mx-auto mb-3 opacity-30" />
            <p className="font-medium">No campaigns yet</p>
            <p className="text-sm mt-1">Create your first campaign to start tracking leads</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {campaigns.map((c) => (
              <div key={c.id} className="card hover:shadow-card-hover transition-shadow group">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h3 className="font-semibold text-slate-900">{c.name}</h3>
                    {c.description && <p className="text-xs text-slate-400 mt-0.5">{c.description}</p>}
                  </div>
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium capitalize ${statusColor[c.status] || "bg-slate-100 text-slate-600"}`}>
                    {c.status}
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-3 my-4">
                  <Stat icon={<Users className="w-3.5 h-3.5" />} label="Leads" value={c.total_leads} />
                  <Stat icon={<CheckCircle2 className="w-3.5 h-3.5" />} label="Converted" value={c.converted_leads} />
                  <Stat icon={<TrendingUp className="w-3.5 h-3.5" />} label="Rate" value={`${c.conversion_rate}%`} />
                </div>

                {/* Progress bar */}
                <div>
                  <div className="flex justify-between text-xs text-slate-400 mb-1">
                    <span>Conversion Rate</span>
                    <span>{c.conversion_rate}%</span>
                  </div>
                  <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                    <div className="h-full bg-indigo-500 rounded-full" style={{ width: `${c.conversion_rate}%` }} />
                  </div>
                </div>

                <div className="flex justify-between items-center mt-4 pt-3 border-t border-slate-100">
                  <span className="text-xs text-slate-400">
                    {new Date(c.created_at).toLocaleDateString()}
                  </span>
                  <button onClick={() => handleDelete(c.id)}
                    className="text-xs text-red-500 hover:text-red-700 opacity-0 group-hover:opacity-100 transition-opacity">
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
      {showCreate && <CreateCampaignModal onClose={() => setShowCreate(false)} onCreated={load} />}
    </div>
  );
}

function Stat({ icon, label, value }: { icon: React.ReactNode; label: string; value: string | number }) {
  return (
    <div className="bg-slate-50 rounded-lg p-2 text-center">
      <div className="flex items-center justify-center gap-1 text-slate-400 mb-1">{icon}</div>
      <div className="text-lg font-bold text-slate-900">{value}</div>
      <div className="text-xs text-slate-400">{label}</div>
    </div>
  );
}

function CreateCampaignModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [form, setForm] = useState({ name: "", description: "", utm_source: "", utm_medium: "", facebook_form_id: "" });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await campaignsApi.create(form);
      onCreated();
      onClose();
    } catch {
      alert("Failed to create campaign");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md">
        <div className="flex items-center justify-between p-6 border-b border-slate-200">
          <h3 className="font-semibold text-slate-900">New Campaign</h3>
          <button onClick={onClose}><X className="w-5 h-5 text-slate-400" /></button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {[
            { name: "name", label: "Campaign Name *", required: true },
            { name: "description", label: "Description", required: false },
            { name: "utm_source", label: "UTM Source (e.g. facebook)", required: false },
            { name: "utm_medium", label: "UTM Medium (e.g. cpc)", required: false },
            { name: "facebook_form_id", label: "Facebook Form ID (for Lead Ads)", required: false },
          ].map(({ name, label, required }) => (
            <div key={name}>
              <label className="block text-sm font-medium text-slate-700 mb-1">{label}</label>
              <input value={(form as Record<string,string>)[name]} required={required}
                onChange={(e) => setForm(f => ({ ...f, [name]: e.target.value }))}
                className="input" />
            </div>
          ))}
          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary flex-1 justify-center">Cancel</button>
            <button type="submit" disabled={loading} className="btn-primary flex-1 justify-center">
              {loading ? "Creating..." : "Create Campaign"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

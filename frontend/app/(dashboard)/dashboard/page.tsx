"use client";
import { useEffect, useState } from "react";
import { analyticsApi } from "@/lib/api";
import { DashboardMetrics, AIInsight } from "@/lib/types";
import Header from "@/components/layout/Header";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from "recharts";
import {
  Users, TrendingUp, Flame, Star, Target, Lightbulb,
  AlertTriangle, CheckCircle, Info, ArrowUpRight,
} from "lucide-react";

const COLORS = { hot: "#ef4444", warm: "#f59e0b", cold: "#3b82f6", unknown: "#94a3b8" };
const SOURCE_COLORS = ["#6366f1", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"];

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [insights, setInsights] = useState<AIInsight[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([analyticsApi.dashboard(30), analyticsApi.insights()])
      .then(([m, i]) => {
        setMetrics(m.data);
        setInsights(i.data.insights);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSkeleton />;

  const s = metrics?.summary;
  const dailyData = metrics?.daily_leads || [];
  const tempData = Object.entries(metrics?.leads_by_temperature || {}).map(([name, value]) => ({ name, value }));
  const sourceData = Object.entries(metrics?.leads_by_source || {}).map(([name, value]) => ({ name, value }));

  return (
    <div className="flex flex-col h-full overflow-auto">
      <Header title="Dashboard" subtitle="Your lead intelligence overview" />
      <div className="flex-1 p-6 space-y-6">

        {/* KPI Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 lg:gap-4">
          <KPICard icon={<Users className="w-5 h-5 text-indigo-600" />} label="Total Leads"
            value={s?.total_leads ?? 0} sub={`+${s?.new_leads ?? 0} this month`} color="bg-indigo-50" />
          <KPICard icon={<Flame className="w-5 h-5 text-red-500" />} label="Hot Leads"
            value={s?.hot_leads ?? 0} sub="Ready to convert" color="bg-red-50" />
          <KPICard icon={<CheckCircle className="w-5 h-5 text-green-600" />} label="Converted"
            value={s?.converted ?? 0} sub={`${s?.conversion_rate ?? 0}% rate`} color="bg-green-50" />
          <KPICard icon={<Star className="w-5 h-5 text-amber-500" />} label="Avg Score"
            value={`${s?.avg_score ?? 0}`} sub="Out of 100" color="bg-amber-50" />
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 lg:gap-6">
          {/* Daily Leads Chart */}
          <div className="card lg:col-span-2 p-4 lg:p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-slate-900">Leads Over Time</h3>
              <span className="text-xs text-slate-400 bg-slate-100 px-2 py-1 rounded">Last 30 days</span>
            </div>
            <ResponsiveContainer width="100%" height={180}>
              <AreaChart data={dailyData}>
                <defs>
                  <linearGradient id="colorLeads" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} tickLine={false}
                  tickFormatter={(v) => v.slice(5)} />
                <YAxis tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8 }} />
                <Area type="monotone" dataKey="count" stroke="#6366f1" strokeWidth={2}
                  fill="url(#colorLeads)" name="Leads" />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Temperature Donut */}
          <div className="card p-4 lg:p-6">
            <h3 className="font-semibold text-slate-900 mb-4">Lead Temperature</h3>
            <ResponsiveContainer width="100%" height={180}>
              <PieChart>
                <Pie data={tempData} cx="50%" cy="50%" innerRadius={55} outerRadius={80}
                  paddingAngle={3} dataKey="value">
                  {tempData.map((entry) => (
                    <Cell key={entry.name} fill={COLORS[entry.name as keyof typeof COLORS] || "#94a3b8"} />
                  ))}
                </Pie>
                <Legend iconType="circle" iconSize={8}
                  formatter={(val) => <span className="text-xs capitalize">{val}</span>} />
                <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8 }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* AI Insights + Source Breakdown */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 lg:gap-6">
          {/* AI Insights */}
          <div className="card">
            <div className="flex items-center gap-2 mb-4">
              <Lightbulb className="w-4 h-4 text-amber-500" />
              <h3 className="font-semibold text-slate-900">AI Insights</h3>
            </div>
            <div className="space-y-3">
              {insights.length === 0 ? (
                <p className="text-sm text-slate-400">No insights yet. Add more leads to unlock AI analysis.</p>
              ) : insights.map((insight, i) => (
                <InsightCard key={i} insight={insight} />
              ))}
            </div>
          </div>

          {/* Leads by Source */}
          <div className="card">
            <h3 className="font-semibold text-slate-900 mb-4">Leads by Source</h3>
            <div className="space-y-3">
              {sourceData.map(({ name, value }, i) => {
                const total = sourceData.reduce((s, d) => s + (d.value as number), 0);
                const pct = total > 0 ? Math.round(((value as number) / total) * 100) : 0;
                return (
                  <div key={name}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="capitalize text-slate-700">{name}</span>
                      <span className="font-medium text-slate-900">{value} ({pct}%)</span>
                    </div>
                    <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                      <div className="h-full rounded-full transition-all"
                        style={{ width: `${pct}%`, backgroundColor: SOURCE_COLORS[i % SOURCE_COLORS.length] }} />
                    </div>
                  </div>
                );
              })}
              {sourceData.length === 0 && (
                <p className="text-sm text-slate-400">No lead data yet.</p>
              )}
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}

function KPICard({ icon, label, value, sub, color }: {
  icon: React.ReactNode; label: string; value: number | string; sub: string; color: string;
}) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-card p-4 lg:p-6 hover:shadow-card-hover transition-shadow">
      <div className={`inline-flex p-2 rounded-lg ${color} mb-2 lg:mb-3`}>{icon}</div>
      <div className="text-xl lg:text-2xl font-bold text-slate-900">{value.toLocaleString()}</div>
      <div className="text-xs lg:text-sm font-medium text-slate-600 mt-0.5">{label}</div>
      <div className="text-xs text-slate-400 mt-0.5 hidden sm:block">{sub}</div>
    </div>
  );
}

function InsightCard({ insight }: { insight: AIInsight }) {
  const colors = {
    positive: "bg-green-50 border-green-200 text-green-800",
    warning: "bg-amber-50 border-amber-200 text-amber-800",
    urgent: "bg-red-50 border-red-200 text-red-800",
    info: "bg-blue-50 border-blue-200 text-blue-800",
  };
  const icons = {
    positive: <CheckCircle className="w-4 h-4 flex-shrink-0" />,
    warning: <AlertTriangle className="w-4 h-4 flex-shrink-0" />,
    urgent: <Flame className="w-4 h-4 flex-shrink-0" />,
    info: <Info className="w-4 h-4 flex-shrink-0" />,
  };
  return (
    <div className={`flex gap-3 p-3 rounded-lg border ${colors[insight.type]}`}>
      {icons[insight.type]}
      <div>
        <p className="text-sm font-medium">{insight.text}</p>
        <p className="text-xs mt-0.5 opacity-80">{insight.action}</p>
      </div>
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="flex flex-col h-full">
      <div className="h-16 bg-white border-b border-slate-200" />
      <div className="p-6 space-y-6 animate-pulse">
        <div className="grid grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-28 bg-slate-100 rounded-xl" />
          ))}
        </div>
        <div className="grid grid-cols-3 gap-6">
          <div className="col-span-2 h-64 bg-slate-100 rounded-xl" />
          <div className="h-64 bg-slate-100 rounded-xl" />
        </div>
      </div>
    </div>
  );
}

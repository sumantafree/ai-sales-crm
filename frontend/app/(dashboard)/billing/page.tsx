"use client";
import { useEffect, useState } from "react";
import { billingApi } from "@/lib/api";
import Header from "@/components/layout/Header";
import { Check, Zap, Crown, Building2, CreditCard, ExternalLink } from "lucide-react";

interface Plan {
  name: string;
  price_inr: number;
  features: string[];
  leads_limit: number;
  members_limit: number;
}

interface Subscription {
  plan: string;
  status: string;
  leads_limit: number;
  members_limit: number;
  current_period_end?: string;
  stripe_customer_id?: string;
}

export default function BillingPage() {
  const [plans, setPlans] = useState<Record<string, Plan>>({});
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [loading, setLoading] = useState(true);
  const [checkoutLoading, setCheckoutLoading] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([billingApi.plans(), billingApi.subscription()])
      .then(([p, s]) => {
        setPlans(p.data);
        setSubscription(s.data);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleUpgrade = async (planKey: string) => {
    setCheckoutLoading(planKey);
    try {
      const origin = window.location.origin;
      const res = await billingApi.checkout(planKey,
        `${origin}/billing?success=true`,
        `${origin}/billing?canceled=true`,
      );
      window.location.href = res.data.checkout_url;
    } catch {
      alert("Failed to start checkout. Please check Stripe configuration.");
    } finally {
      setCheckoutLoading(null);
    }
  };

  const handleManage = async () => {
    try {
      const res = await billingApi.portal(window.location.href);
      window.location.href = res.data.portal_url;
    } catch {
      alert("No active subscription to manage.");
    }
  };

  const PLAN_ICONS: Record<string, React.ReactNode> = {
    free: <Zap className="w-5 h-5 text-slate-600" />,
    pro: <Crown className="w-5 h-5 text-indigo-600" />,
    agency: <Building2 className="w-5 h-5 text-purple-600" />,
  };

  const PLAN_COLORS: Record<string, string> = {
    free: "border-slate-200",
    pro: "border-indigo-500 ring-2 ring-indigo-500 ring-offset-2",
    agency: "border-purple-500",
  };

  if (loading) return (
    <div className="flex flex-col h-full">
      <div className="h-16 bg-white border-b border-slate-200" />
      <div className="p-6 animate-pulse grid grid-cols-3 gap-6">
        {[...Array(3)].map((_, i) => <div key={i} className="h-72 bg-slate-100 rounded-xl" />)}
      </div>
    </div>
  );

  return (
    <div className="flex flex-col h-full overflow-auto">
      <Header title="Billing" subtitle="Manage your subscription plan" />
      <div className="flex-1 p-6 max-w-5xl mx-auto w-full">

        {/* Current subscription banner */}
        {subscription && (
          <div className="card bg-indigo-50 border-indigo-100 mb-8 flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-indigo-800">
                Current Plan: <span className="capitalize font-bold">{subscription.plan}</span>
                <span className={`ml-2 text-xs px-2 py-0.5 rounded-full ${
                  subscription.status === "active" ? "bg-green-100 text-green-700" : "bg-amber-100 text-amber-700"
                }`}>
                  {subscription.status}
                </span>
              </p>
              <p className="text-sm text-indigo-600 mt-1">
                {subscription.leads_limit === -1 ? "Unlimited" : subscription.leads_limit} leads ·{" "}
                {subscription.members_limit === -1 ? "Unlimited" : subscription.members_limit} members
                {subscription.current_period_end && (
                  <> · Renews {new Date(subscription.current_period_end).toLocaleDateString()}</>
                )}
              </p>
            </div>
            {subscription.stripe_customer_id && (
              <button onClick={handleManage} className="btn-secondary gap-2 text-sm">
                <CreditCard className="w-4 h-4" /> Manage Billing
                <ExternalLink className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        )}

        {/* Plan Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {Object.entries(plans).map(([key, plan]) => {
            const isCurrent = subscription?.plan === key;
            const isPro = key === "pro";
            return (
              <div key={key} className={`card relative flex flex-col ${PLAN_COLORS[key] || "border-slate-200"}`}>
                {isPro && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <span className="bg-indigo-600 text-white text-xs font-bold px-3 py-1 rounded-full">
                      Most Popular
                    </span>
                  </div>
                )}
                <div className="flex items-center gap-3 mb-4">
                  <div className={`p-2 rounded-xl ${key === "free" ? "bg-slate-100" : key === "pro" ? "bg-indigo-100" : "bg-purple-100"}`}>
                    {PLAN_ICONS[key]}
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-900">{plan.name}</h3>
                    <p className="text-2xl font-bold text-slate-900 mt-0.5">
                      {plan.price_inr === 0 ? "Free" : `₹${plan.price_inr.toLocaleString()}`}
                      {plan.price_inr > 0 && <span className="text-sm font-normal text-slate-400">/mo</span>}
                    </p>
                  </div>
                </div>

                <ul className="space-y-2.5 flex-1 mb-6">
                  {plan.features.map((f) => (
                    <li key={f} className="flex items-start gap-2 text-sm text-slate-600">
                      <Check className="w-4 h-4 text-green-500 flex-shrink-0 mt-0.5" />
                      {f}
                    </li>
                  ))}
                </ul>

                {isCurrent ? (
                  <div className="btn-secondary w-full justify-center pointer-events-none opacity-70">
                    ✓ Current Plan
                  </div>
                ) : key === "free" ? (
                  <div className="text-center text-sm text-slate-400">Always free</div>
                ) : (
                  <button onClick={() => handleUpgrade(key)} disabled={!!checkoutLoading}
                    className={`w-full justify-center ${isPro ? "btn-primary" : "btn-secondary"}`}>
                    {checkoutLoading === key ? "Redirecting..." : `Upgrade to ${plan.name}`}
                  </button>
                )}
              </div>
            );
          })}
        </div>

        <p className="text-center text-xs text-slate-400 mt-8">
          Secure payments via Stripe · Cancel anytime · No hidden fees
        </p>
      </div>
    </div>
  );
}

"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { authApi } from "@/lib/api";
import { setToken, setUser } from "@/lib/auth";
import { Zap, User, Mail, Lock, Building2 } from "lucide-react";

export default function SignupPage() {
  const router = useRouter();
  const [form, setForm] = useState({ full_name: "", email: "", password: "", workspace_name: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [e.target.name]: e.target.value }));

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const res = await authApi.signup(form);
      setToken(res.data.access_token);
      setUser(res.data.user);
      router.replace("/dashboard");
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      setError(e.response?.data?.detail || "Signup failed. Try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 bg-indigo-600 rounded-2xl mb-4 shadow-lg">
            <Zap className="w-7 h-7 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-slate-900">Get Started Free</h1>
          <p className="text-slate-500 mt-1">Create your AI Sales CRM account</p>
        </div>

        <div className="card shadow-xl border-0">
          <form onSubmit={handleSignup} className="space-y-4">
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">{error}</div>
            )}
            {[
              { name: "full_name", label: "Full Name", icon: User, type: "text", placeholder: "John Smith" },
              { name: "email", label: "Work Email", icon: Mail, type: "email", placeholder: "you@company.com" },
              { name: "workspace_name", label: "Company / Workspace Name", icon: Building2, type: "text", placeholder: "Acme Corp" },
              { name: "password", label: "Password", icon: Lock, type: "password", placeholder: "Min 8 characters" },
            ].map(({ name, label, icon: Icon, type, placeholder }) => (
              <div key={name}>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">{label}</label>
                <div className="relative">
                  <Icon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <input
                    name={name} type={type} value={(form as Record<string,string>)[name]}
                    onChange={handleChange} className="input pl-9" placeholder={placeholder} required
                  />
                </div>
              </div>
            ))}
            <button type="submit" className="btn-primary w-full justify-center py-2.5 mt-2" disabled={loading}>
              {loading ? "Creating account..." : "Create Free Account"}
            </button>
          </form>
          <p className="text-center text-xs text-slate-400 mt-4">
            Free plan includes 100 leads/month. No credit card required.
          </p>
          <p className="text-center text-sm text-slate-500 mt-3">
            Already have an account?{" "}
            <Link href="/auth/login" className="text-indigo-600 font-medium hover:underline">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}

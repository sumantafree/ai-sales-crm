"use client";
import { useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { isAuthenticated, getUser } from "@/lib/auth";
import Sidebar from "@/components/layout/Sidebar";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/auth/login");
      return;
    }

    // WebSocket for real-time notifications
    const user = getUser();
    if (user?.current_workspace_id) {
      const wsUrl = `${(process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace("http", "ws")}/ws/${user.current_workspace_id}`;
      const ws = new WebSocket(wsUrl);
      ws.onopen = () => ws.send("ping");
      ws.onmessage = (ev) => {
        try {
          const data = JSON.parse(ev.data);
          if (data.type === "hot_lead") {
            // Could show a toast notification here
            console.log("🔥 Hot lead!", data);
          }
        } catch {}
      };
      wsRef.current = ws;
    }
    return () => wsRef.current?.close();
  }, [router]);

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      <Sidebar />
      {/* pt-14 = mobile top bar height, pb-16 = mobile bottom tab bar */}
      <main className="flex-1 flex flex-col overflow-hidden pt-14 lg:pt-0 pb-16 lg:pb-0">
        {children}
      </main>
    </div>
  );
}

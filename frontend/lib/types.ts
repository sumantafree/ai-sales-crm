export interface User {
  id: string;
  email: string;
  full_name: string;
  avatar_url?: string;
  current_workspace_id?: string;
}

export interface Lead {
  id: string;
  name: string;
  phone?: string;
  email?: string;
  message?: string;
  source: "facebook" | "whatsapp" | "email" | "website" | "manual";
  score: number;
  temperature: "hot" | "warm" | "cold";
  intent: "buying" | "inquiry" | "casual" | "unknown";
  status: "new" | "contacted" | "qualified" | "converted" | "lost";
  ai_summary?: string;
  ai_suggested_action?: string;
  ai_generated_reply?: string;
  campaign_id?: string;
  follow_up_count: number;
  last_contacted_at?: string;
  created_at: string;
  updated_at: string;
}

export interface Campaign {
  id: string;
  name: string;
  description?: string;
  status: "draft" | "active" | "paused" | "completed";
  total_leads: number;
  converted_leads: number;
  conversion_rate: number;
  revenue_generated: number;
  utm_source?: string;
  created_at: string;
}

export interface Automation {
  id: string;
  name: string;
  description?: string;
  status: "active" | "inactive";
  trigger: string;
  trigger_config?: Record<string, unknown>;
  action: string;
  action_config?: Record<string, unknown>;
  delay_minutes: string;
  run_count: string;
  created_at: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  channel: "whatsapp" | "email" | "chat";
  is_ai_generated: boolean;
  created_at: string;
}

export interface Conversation {
  id: string;
  lead_id: string;
  channel: string;
  is_active: boolean;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface Subscription {
  plan: "free" | "pro" | "agency";
  status: string;
  leads_limit: number;
  members_limit: number;
  current_period_end?: string;
}

export interface DashboardMetrics {
  summary: {
    total_leads: number;
    new_leads: number;
    converted: number;
    hot_leads: number;
    avg_score: number;
    conversion_rate: number;
  };
  leads_by_source: Record<string, number>;
  leads_by_temperature: Record<string, number>;
  daily_leads: { date: string; count: number }[];
  top_campaign?: { name: string; total_leads: number; converted: number };
}

export interface AIInsight {
  type: "positive" | "warning" | "urgent" | "info";
  icon: string;
  text: string;
  action: string;
}

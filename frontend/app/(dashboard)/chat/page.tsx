"use client";
import { useEffect, useState, useRef } from "react";
import { leadsApi, conversationsApi } from "@/lib/api";
import { Lead, Conversation, Message } from "@/lib/types";
import Header from "@/components/layout/Header";
import { Send, Bot, MessageSquare, Phone, Flame, Thermometer, Snowflake } from "lucide-react";
import clsx from "clsx";

export default function ChatPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConv, setSelectedConv] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [useAI, setUseAI] = useState(false);
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    leadsApi.list({ limit: 50 }).then((r) => setLeads(r.data.leads));
  }, []);

  useEffect(() => {
    if (!selectedLead) return;
    conversationsApi.getByLead(selectedLead.id).then((r) => {
      setConversations(r.data);
      if (r.data.length > 0) selectConv(r.data[0]);
      else { setSelectedConv(null); setMessages([]); }
    });
  }, [selectedLead]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const selectConv = async (conv: Conversation) => {
    setSelectedConv(conv);
    const r = await conversationsApi.getMessages(conv.id);
    setMessages(r.data.messages);
  };

  const startConversation = async () => {
    if (!selectedLead) return;
    const r = await conversationsApi.start(selectedLead.id, "whatsapp");
    setConversations((prev) => [r.data, ...prev]);
    setSelectedConv(r.data);
    setMessages([]);
  };

  const sendMessage = async () => {
    if (!input.trim() || !selectedConv || sending) return;
    setSending(true);
    try {
      const r = await conversationsApi.send(selectedConv.id, {
        content: input, channel: "whatsapp", use_ai: useAI,
      });
      setMessages((m) => [...m, r.data]);
      setInput("");
    } finally {
      setSending(false);
    }
  };

  const TempIcon = selectedLead?.temperature === "hot" ? Flame :
    selectedLead?.temperature === "warm" ? Thermometer : Snowflake;
  const tempColor = selectedLead?.temperature === "hot" ? "text-red-500" :
    selectedLead?.temperature === "warm" ? "text-amber-500" : "text-blue-500";

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <Header title="Chat" subtitle="WhatsApp-style lead conversations" />
      <div className="flex-1 flex overflow-hidden">

        {/* Lead List */}
        <div className="w-72 border-r border-slate-200 bg-white flex flex-col flex-shrink-0">
          <div className="p-3 border-b border-slate-100">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Leads</p>
          </div>
          <div className="flex-1 overflow-y-auto divide-y divide-slate-50">
            {leads.map((lead) => (
              <button key={lead.id} onClick={() => setSelectedLead(lead)}
                className={clsx(
                  "w-full flex items-center gap-3 px-3 py-3 text-left hover:bg-slate-50 transition-colors",
                  selectedLead?.id === lead.id && "bg-indigo-50 border-r-2 border-indigo-500"
                )}>
                <div className="w-9 h-9 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-700 font-bold text-sm flex-shrink-0">
                  {lead.name[0].toUpperCase()}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-1.5">
                    <p className="text-sm font-medium text-slate-900 truncate">{lead.name}</p>
                    {lead.temperature === "hot" && <Flame className="w-3 h-3 text-red-500 flex-shrink-0" />}
                  </div>
                  <p className="text-xs text-slate-400 truncate">{lead.phone || lead.email || "No contact"}</p>
                </div>
              </button>
            ))}
            {leads.length === 0 && (
              <p className="text-sm text-slate-400 text-center py-8">No leads yet</p>
            )}
          </div>
        </div>

        {/* Chat Area */}
        {selectedLead ? (
          <div className="flex-1 flex flex-col overflow-hidden bg-slate-50">
            {/* Chat Header */}
            <div className="flex items-center justify-between px-5 py-3 bg-white border-b border-slate-200">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-700 font-bold">
                  {selectedLead.name[0].toUpperCase()}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h4 className="font-semibold text-slate-900">{selectedLead.name}</h4>
                    <TempIcon className={clsx("w-4 h-4", tempColor)} />
                  </div>
                  <p className="text-xs text-slate-400">
                    {selectedLead.phone || selectedLead.email} · Score: {Math.round(selectedLead.score)}/100
                  </p>
                </div>
              </div>
              <div className="flex gap-2">
                {conversations.length === 0 && (
                  <button onClick={startConversation} className="btn-primary text-xs py-1.5 px-3">
                    <MessageSquare className="w-3.5 h-3.5" /> Start Chat
                  </button>
                )}
                {conversations.map((conv) => (
                  <button key={conv.id} onClick={() => selectConv(conv)}
                    className={clsx("text-xs px-2 py-1 rounded-md border transition-colors",
                      selectedConv?.id === conv.id
                        ? "bg-indigo-600 text-white border-indigo-600"
                        : "border-slate-200 text-slate-600 hover:bg-slate-50"
                    )}>
                    {conv.channel}
                  </button>
                ))}
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {messages.length === 0 && selectedConv && (
                <div className="text-center text-sm text-slate-400 py-8">
                  No messages yet. Start the conversation!
                </div>
              )}
              {!selectedConv && (
                <div className="text-center text-sm text-slate-400 py-8">
                  No conversation started. Click "Start Chat" to begin.
                </div>
              )}
              {messages.map((msg) => (
                <div key={msg.id} className={clsx("flex", msg.role === "user" ? "justify-start" : "justify-end")}>
                  <div className={clsx(
                    "max-w-xs lg:max-w-md px-4 py-2.5 rounded-2xl text-sm shadow-sm",
                    msg.role === "user"
                      ? "bg-white text-slate-800 rounded-tl-sm"
                      : msg.is_ai_generated
                        ? "bg-purple-600 text-white rounded-tr-sm"
                        : "bg-indigo-600 text-white rounded-tr-sm"
                  )}>
                    {msg.is_ai_generated && (
                      <div className="flex items-center gap-1 text-purple-200 text-xs mb-1">
                        <Bot className="w-3 h-3" /> AI Generated
                      </div>
                    )}
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                    <p className={clsx("text-xs mt-1", msg.role === "user" ? "text-slate-400" : "text-white/60")}>
                      {new Date(msg.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </p>
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>

            {/* AI Reply Suggestion */}
            {selectedLead.ai_generated_reply && messages.length === 0 && selectedConv && (
              <div className="mx-4 mb-2 p-3 bg-purple-50 border border-purple-100 rounded-xl flex items-start gap-2">
                <Bot className="w-4 h-4 text-purple-600 flex-shrink-0 mt-0.5" />
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-purple-700 mb-1">AI Suggested Reply</p>
                  <p className="text-sm text-slate-700 italic">"{selectedLead.ai_generated_reply}"</p>
                </div>
                <button onClick={() => setInput(selectedLead.ai_generated_reply || "")}
                  className="text-xs px-2 py-1 bg-purple-100 text-purple-700 rounded-md hover:bg-purple-200 flex-shrink-0">
                  Use
                </button>
              </div>
            )}

            {/* Input */}
            {selectedConv && (
              <div className="p-3 bg-white border-t border-slate-200">
                <div className="flex items-center gap-2 mb-2">
                  <label className="flex items-center gap-1.5 text-xs text-slate-600 cursor-pointer">
                    <input type="checkbox" checked={useAI} onChange={(e) => setUseAI(e.target.checked)}
                      className="w-3.5 h-3.5 rounded border-slate-300 text-purple-600" />
                    <Bot className="w-3.5 h-3.5 text-purple-600" />
                    Use AI to generate reply
                  </label>
                </div>
                <div className="flex gap-2">
                  <input value={input} onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); } }}
                    placeholder={useAI ? "Let AI craft the reply..." : "Type a message..."}
                    className="input flex-1 bg-slate-50" />
                  <button onClick={sendMessage} disabled={!input.trim() || sending}
                    className="btn-primary px-4 disabled:opacity-40">
                    <Send className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center text-slate-400">
            <div className="text-center">
              <MessageSquare className="w-12 h-12 mx-auto mb-3 opacity-20" />
              <p className="font-medium">Select a lead to start chatting</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

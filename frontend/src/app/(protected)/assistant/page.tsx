"use client";

import { useState, useRef, useEffect } from "react";
import { Send } from "lucide-react";
import { orgApi } from "@/lib/api";
import { PageHeader } from "@/components/ui";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export default function AssistantPage() {
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", content: "Ask me about any risk, prediction, or recommendation — I'll ground my answer in the actual computed numbers, never guess." },
  ]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function send() {
    if (!input.trim() || sending) return;
    const question = input.trim();
    setMessages((m) => [...m, { role: "user", content: question }]);
    setInput("");
    setSending(true);
    try {
      const res = await orgApi.chat(question, {});
      setMessages((m) => [...m, { role: "assistant", content: res.answer }]);
    } catch {
      setMessages((m) => [...m, { role: "assistant", content: "Couldn't reach the backend — check that the API is running." }]);
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="h-screen flex flex-col">
      <PageHeader eyebrow="FR-602" title="AI Assistant" subtitle="Explains pre-computed results. Never performs its own calculations." />
      <div className="flex-1 overflow-y-auto px-8 py-6 space-y-4">
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-lg rounded px-4 py-2.5 text-sm ${
                m.role === "user" ? "bg-signal text-graphite-950" : "border hairline bg-graphite-900/50 text-ink-100"
              }`}
            >
              {m.content}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
      <div className="border-t hairline p-4">
        <div className="flex gap-2 max-w-2xl">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send()}
            placeholder="Why is this project at risk?"
            className="flex-1 bg-graphite-800 border hairline rounded px-3 py-2 text-sm text-ink-100 outline-none focus:border-signal"
          />
          <button
            onClick={send}
            disabled={sending}
            className="bg-signal text-graphite-950 px-3 rounded hover:opacity-90 disabled:opacity-50 flex items-center justify-center"
          >
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}

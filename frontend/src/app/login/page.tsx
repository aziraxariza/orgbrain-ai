"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { ApiError } from "@/lib/api";

export default function LoginPage() {
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [email, setEmail] = useState("admin@acmedemo.com");
  const [password, setPassword] = useState("password123");
  const [orgName, setOrgName] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const { login, signup } = useAuth();
  const router = useRouter();

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      if (mode === "login") {
        await login(email, password);
      } else {
        await signup(orgName, email, password, fullName);
      }
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Is the backend running?");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <div className="font-display italic text-3xl text-ink-100">OrgBrain</div>
          <p className="text-sm text-ink-500 mt-2">
            Deterministic simulation and risk detection for how work actually moves through your org.
          </p>
        </div>

        <div className="border hairline rounded bg-graphite-900/50 p-6">
          <div className="flex gap-1 mb-6 border hairline rounded p-0.5">
            <button
              onClick={() => setMode("login")}
              className={`flex-1 text-sm py-1.5 rounded transition-colors ${mode === "login" ? "bg-graphite-700 text-ink-100" : "text-ink-500"}`}
            >
              Log in
            </button>
            <button
              onClick={() => setMode("signup")}
              className={`flex-1 text-sm py-1.5 rounded transition-colors ${mode === "signup" ? "bg-graphite-700 text-ink-100" : "text-ink-500"}`}
            >
              Create org
            </button>
          </div>

          <form onSubmit={onSubmit} className="space-y-3">
            {mode === "signup" && (
              <>
                <Field label="Organization name" value={orgName} onChange={setOrgName} required />
                <Field label="Your name" value={fullName} onChange={setFullName} required />
              </>
            )}
            <Field label="Email" type="email" value={email} onChange={setEmail} required />
            <Field label="Password" type="password" value={password} onChange={setPassword} required />

            {error && <p className="text-sm text-severity-critical">{error}</p>}

            <button
              type="submit"
              disabled={submitting}
              className="w-full bg-signal text-graphite-950 font-medium text-sm py-2 rounded hover:opacity-90 transition-opacity disabled:opacity-50"
            >
              {submitting ? "Working…" : mode === "login" ? "Log in" : "Create organization"}
            </button>
          </form>

          {mode === "login" && (
            <p className="text-xs text-ink-500 mt-4">
              Demo login: <span className="font-mono">admin@acmedemo.com</span> / <span className="font-mono">password123</span>
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

function Field({
  label, value, onChange, type = "text", required,
}: { label: string; value: string; onChange: (v: string) => void; type?: string; required?: boolean }) {
  return (
    <label className="block">
      <span className="text-xs text-ink-500">{label}</span>
      <input
        type={type}
        required={required}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="mt-1 w-full bg-graphite-800 border hairline rounded px-3 py-2 text-sm text-ink-100 focus:border-signal outline-none"
      />
    </label>
  );
}

import { cn } from "@/lib/utils";

export function Card({ className, children }: { className?: string; children: React.ReactNode }) {
  return (
    <div className={cn("border hairline rounded bg-graphite-900/50 p-5", className)}>
      {children}
    </div>
  );
}

export function PageHeader({ title, subtitle, eyebrow }: { title: string; subtitle?: string; eyebrow?: string }) {
  return (
    <div className="border-b hairline px-8 py-6">
      {eyebrow && <div className="text-[11px] uppercase tracking-wide text-signal mb-1.5">{eyebrow}</div>}
      <h1 className="font-display text-2xl text-ink-100">{title}</h1>
      {subtitle && <p className="text-sm text-ink-500 mt-1">{subtitle}</p>}
    </div>
  );
}

export function Stat({ label, value, tone }: { label: string; value: string | number; tone?: "signal" | "calm" | "default" }) {
  const toneClass = tone === "signal" ? "text-signal" : tone === "calm" ? "text-calm" : "text-ink-100";
  return (
    <div>
      <div className="text-[11px] uppercase tracking-wide text-ink-500 mb-1">{label}</div>
      <div className={cn("font-display text-3xl tabular", toneClass)}>{value}</div>
    </div>
  );
}

export function Badge({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <span className={cn("inline-flex items-center px-2 py-0.5 rounded text-xs border font-mono", className)}>
      {children}
    </span>
  );
}

export function EmptyState({ message }: { message: string }) {
  return <div className="text-sm text-ink-500 py-12 text-center border hairline rounded border-dashed">{message}</div>;
}

export function Loading() {
  return <div className="text-sm text-ink-500 py-12 text-center">Loading…</div>;
}

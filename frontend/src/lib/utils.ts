import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function severityColor(sev: string): string {
  switch (sev) {
    case "critical":
      return "text-severity-critical border-severity-critical/40 bg-severity-critical/10";
    case "high":
      return "text-severity-high border-severity-high/40 bg-severity-high/10";
    case "medium":
      return "text-severity-medium border-severity-medium/40 bg-severity-medium/10";
    default:
      return "text-severity-low border-severity-low/40 bg-severity-low/10";
  }
}

export function bandColor(band: string): string {
  switch (band) {
    case "overloaded":
      return "text-severity-critical";
    case "at_capacity":
      return "text-severity-medium";
    case "healthy":
      return "text-calm";
    default:
      return "text-ink-500";
  }
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("orgbrain_token");
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      /* non-JSON error body, keep statusText */
    }
    throw new ApiError(detail, res.status);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "POST", body: body ? JSON.stringify(body) : undefined }),
};

// ---- Auth ----
export interface TokenResponse {
  access_token: string;
  token_type: string;
  tenant_id: string;
  role: string;
}

export const authApi = {
  login: (email: string, password: string) =>
    api.post<TokenResponse>("/api/v1/auth/login", { email, password }),
  signup: (organization_name: string, email: string, password: string, full_name: string) =>
    api.post<TokenResponse>("/api/v1/auth/signup", { organization_name, email, password, full_name }),
};

// ---- Entities ----
export interface Employee {
  employee_id: string;
  name: string;
  role: string;
  manager_id: string | null;
  skills: string[];
  available_hours_per_week: number;
  current_workload_hours: number;
  is_active: boolean;
  hire_date: string | null;
}

export interface Project {
  project_id: string;
  name: string;
  description: string;
  start_date: string | null;
  target_end_date: string | null;
  status: "planned" | "active" | "at_risk" | "blocked" | "completed";
}

export interface Task {
  task_id: string;
  project_id: string;
  name: string;
  assigned_person_id: string | null;
  estimated_hours: number;
  actual_hours_completed: number;
  progress_percent: number;
  start_date: string | null;
  deadline: string | null;
  priority: "P0" | "P1" | "P2" | "P3";
  status: "todo" | "in_progress" | "blocked" | "done";
}

export interface WorkloadEntry {
  employee_id: string;
  name: string;
  available_hours_per_week: number;
  remaining_committed_hours: number;
  utilization_ratio: number;
  band: "overloaded" | "at_capacity" | "healthy" | "underutilized";
  active_task_count: number;
}

export interface RiskFinding {
  risk_type: "execution_drift" | "bottleneck" | "dependency_concentration" | "capacity_violation";
  severity: "low" | "medium" | "high" | "critical";
  severity_score: number;
  task_id: string | null;
  project_id: string | null;
  employee_id: string | null;
  description: string;
  evidence: Record<string, unknown>;
}

export interface GraphNode {
  id: string;
  type: "employee" | "task" | "project";
  name: string;
  [key: string]: unknown;
}

export interface GraphEdge {
  source: string;
  target: string;
  type: string;
}

export const orgApi = {
  employees: () => api.get<Employee[]>("/api/v1/employees"),
  workload: () => api.get<WorkloadEntry[]>("/api/v1/employees/workload"),
  projects: () => api.get<Project[]>("/api/v1/projects"),
  projectTasks: (projectId: string) => api.get<Task[]>(`/api/v1/projects/${projectId}/tasks`),
  tasks: () => api.get<Task[]>("/api/v1/tasks"),
  graph: () => api.get<{ nodes: GraphNode[]; edges: GraphEdge[]; node_count: number; edge_count: number }>("/api/v1/graph"),
  risks: () => api.get<RiskFinding[]>("/api/v1/risks"),
  capacityViolations: () => api.get<WorkloadEntry[]>("/api/v1/capacity-violations"),
  workloadImbalances: () =>
    api.get<{
      overloaded_count: number;
      underutilized_count: number;
      overloaded: WorkloadEntry[];
      underutilized: WorkloadEntry[];
      org_avg_utilization: number;
    }>("/api/v1/workload-imbalances"),
  criticalPath: (projectId: string) =>
    api.get<{ critical_path: { task_id: string; name: string; duration_days: number }[]; total_duration_days: number; error?: string }>(
      `/api/v1/projects/${projectId}/critical-path`
    ),
  monteCarlo: (projectId: string, iterations = 1000) =>
    api.post<{
      simulation_run_id: string; iterations: number; mean_days: number; p50_days: number;
      p80_days: number; p95_days: number; min_days: number; max_days: number; error?: string;
    }>(`/api/v1/projects/${projectId}/monte-carlo?iterations=${iterations}`),
  prediction: (projectId: string) =>
    api.get<{
      project_id: string; days_available?: number; success_probability: number | null;
      active_project_risks?: number; note?: string; error?: string;
    }>(`/api/v1/projects/${projectId}/prediction`),
  timelineForecast: (projectId: string) =>
    api.get<{
      critical_path: { task_id: string; name: string; duration_days: number }[];
      forecast_duration_days: number; forecast_end_date: string | null;
      target_end_date: string | null; buffer_days: number | null; at_risk: boolean; error?: string;
    }>(`/api/v1/projects/${projectId}/timeline-forecast`),
  whatIf: (projectId: string, reassign: object[], addCapacity: object[]) =>
    api.post<{
      baseline: { critical_path_days: number; monte_carlo_p80: number };
      scenario: { critical_path_days: number; monte_carlo_p80: number };
      delta_critical_path_days: number | null;
    }>("/api/v1/simulate", { project_id: projectId, reassign, add_capacity: addCapacity }),
  validateDecision: (payload: { type: string; affected_employee_ids: string[]; disruption_weeks: number; target_skill?: string }) =>
    api.post<Record<string, unknown> & { recommendation_id: string; explanation: string }>("/api/v1/validate-decision", payload),
  allocationRecommendations: () =>
    api.get<
      { overloaded_employee: string; underutilized_employee: string; shared_skills: string[]; action: string; confidence: number }[]
    >("/api/v1/recommendations/allocation"),
  chat: (question: string, context: object = {}) =>
    api.post<{ question: string; answer: string }>("/api/v1/chat", { question, context }),
};

"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { useRouter } from "next/navigation";
import { authApi } from "./api";

interface AuthState {
  token: string | null;
  tenantId: string | null;
  role: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (orgName: string, email: string, password: string, fullName: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [tenantId, setTenantId] = useState<string | null>(null);
  const [role, setRole] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    setToken(localStorage.getItem("orgbrain_token"));
    setTenantId(localStorage.getItem("orgbrain_tenant"));
    setRole(localStorage.getItem("orgbrain_role"));
    setLoading(false);
  }, []);

  function persist(t: string, tenant: string, r: string) {
    localStorage.setItem("orgbrain_token", t);
    localStorage.setItem("orgbrain_tenant", tenant);
    localStorage.setItem("orgbrain_role", r);
    setToken(t);
    setTenantId(tenant);
    setRole(r);
  }

  async function login(email: string, password: string) {
    const res = await authApi.login(email, password);
    persist(res.access_token, res.tenant_id, res.role);
  }

  async function signup(orgName: string, email: string, password: string, fullName: string) {
    const res = await authApi.signup(orgName, email, password, fullName);
    persist(res.access_token, res.tenant_id, res.role);
  }

  function logout() {
    localStorage.removeItem("orgbrain_token");
    localStorage.removeItem("orgbrain_tenant");
    localStorage.removeItem("orgbrain_role");
    setToken(null);
    setTenantId(null);
    setRole(null);
    router.push("/login");
  }

  return (
    <AuthContext.Provider value={{ token, tenantId, role, loading, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

/**
 * APIクライアント
 */

const API_BASE =
  typeof window !== "undefined"
    ? (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000")
    : "http://backend:8000";

/** 認証トークンの取得 */
function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("token");
}

/** 認証トークンの保存 */
export function setToken(token: string): void {
  localStorage.setItem("token", token);
}

/** 認証トークンの削除（ログアウト） */
export function removeToken(): void {
  localStorage.removeItem("token");
}

/** API共通リクエスト */
async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "エラーが発生しました" }));
    const message = typeof error.detail === "string" ? error.detail : `HTTP ${res.status}`;
    throw new Error(message);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

/** 認証API */
export const authApi = {
  login: (email: string, password: string) =>
    request<import("@/types").TokenResponse>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  register: (name: string, email: string, password: string, role = "viewer") =>
    request<import("@/types").TokenResponse>("/api/v1/auth/register", {
      method: "POST",
      body: JSON.stringify({ name, email, password, role }),
    }),
  me: () => request<import("@/types").User>("/api/v1/auth/me"),
};

/** 企業API */
export const companiesApi = {
  list: (params?: { category?: string; is_active?: boolean }) => {
    const query = new URLSearchParams();
    if (params?.category) query.set("category", params.category);
    if (params?.is_active !== undefined) query.set("is_active", String(params.is_active));
    const qs = query.toString();
    return request<import("@/types").Company[]>(`/api/v1/companies/${qs ? `?${qs}` : ""}`);
  },
  get: (id: number) =>
    request<import("@/types").Company>(`/api/v1/companies/${id}`),
  create: (data: { name: string; category: string; website_url?: string; description?: string }) =>
    request<import("@/types").Company>("/api/v1/companies/", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  update: (id: number, data: Record<string, unknown>) =>
    request<import("@/types").Company>(`/api/v1/companies/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  delete: (id: number) =>
    request<void>(`/api/v1/companies/${id}`, { method: "DELETE" }),
};

/** クロールソースAPI */
export const crawlSourcesApi = {
  list: (companyId?: number) => {
    const qs = companyId ? `?company_id=${companyId}` : "";
    return request<import("@/types").CrawlSource[]>(`/api/v1/crawl-sources/${qs}`);
  },
  create: (data: { company_id: number; source_type: string; url: string; crawl_frequency?: string }) =>
    request<import("@/types").CrawlSource>("/api/v1/crawl-sources/", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  update: (id: number, data: Record<string, unknown>) =>
    request<import("@/types").CrawlSource>(`/api/v1/crawl-sources/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  delete: (id: number) =>
    request<void>(`/api/v1/crawl-sources/${id}`, { method: "DELETE" }),
};

/** クロール実行API */
export const crawlApi = {
  runSingle: (sourceId: number) =>
    request<{ source_id: number; source_type: string; url: string; success: boolean; items_count: number; error: string | null }>(
      `/api/v1/crawl/run/${sourceId}`,
      { method: "POST" }
    ),
  runAll: (companyId?: number) => {
    const qs = companyId ? `?company_id=${companyId}` : "";
    return request<{ total_success: number; total_failure: number; crawlers: Record<string, unknown> }>(
      `/api/v1/crawl/run-all${qs}`,
      { method: "POST" }
    );
  },
};

/** ダッシュボードAPI */
export const dashboardApi = {
  stats: () =>
    request<{ company_count: number; news_count: number; unread_alerts: number; job_count: number }>(
      "/api/v1/dashboard/stats"
    ),
  news: (params?: { company_id?: number; limit?: number }) => {
    const query = new URLSearchParams();
    if (params?.company_id) query.set("company_id", String(params.company_id));
    if (params?.limit) query.set("limit", String(params.limit));
    const qs = query.toString();
    return request<Array<Record<string, unknown>>>(`/api/v1/dashboard/news${qs ? `?${qs}` : ""}`);
  },
  alerts: (params?: { severity?: string; is_read?: boolean; limit?: number }) => {
    const query = new URLSearchParams();
    if (params?.severity) query.set("severity", params.severity);
    if (params?.is_read !== undefined) query.set("is_read", String(params.is_read));
    if (params?.limit) query.set("limit", String(params.limit));
    const qs = query.toString();
    return request<Array<Record<string, unknown>>>(`/api/v1/dashboard/alerts${qs ? `?${qs}` : ""}`);
  },
  markAlertRead: (id: number) =>
    request<void>(`/api/v1/dashboard/alerts/${id}/read`, { method: "PATCH" }),
  markAllAlertsRead: () =>
    request<void>("/api/v1/dashboard/alerts/read-all", { method: "PATCH" }),
  companyReviews: (companyId: number) =>
    request<Array<Record<string, unknown>>>(`/api/v1/dashboard/companies/${companyId}/reviews`),
  companyJobs: (companyId: number) =>
    request<Array<Record<string, unknown>>>(`/api/v1/dashboard/companies/${companyId}/jobs`),
  compare: (companyIds: number[]) =>
    request<Array<Record<string, unknown>>>(`/api/v1/dashboard/compare?company_ids=${companyIds.join(",")}`),
};

/** 分析API */
export const analysisApi = {
  run: (companyId: number) =>
    request<Record<string, unknown>>(`/api/v1/analysis/run/${companyId}`, { method: "POST" }),
  latest: (companyId: number) =>
    request<Record<string, unknown>>(`/api/v1/analysis/latest/${companyId}`),
};

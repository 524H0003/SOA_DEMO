export type AbsentStatus = "pending" | "approved" | "rejected";

export type AbsentRequest = {
  id: number;
  employee_name: string;
  employee_email: string;
  manager_email: string;
  absent_type: string;
  start_date: string;
  end_date: string;
  reason: string;
  status: AbsentStatus;
  created_at: string;
  decided_at: string | null;
};

export type AbsentRequestPayload = Omit<AbsentRequest, "id" | "status" | "created_at" | "decided_at">;
export type AbsentRequestFormPayload = Omit<AbsentRequestPayload, "manager_email" | "employee_email" | "employee_name">;

export type LoginPayload = {
  username: string;
  password: string;
};

export type AuthToken = {
  access_token: string;
  token_type: string;
};

const API_URL = import.meta.env.VITE_API_URL ?? "";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
    },
    credentials: 'include',
    ...options,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? "Không thể kết nối tới hệ thống");
  }
  return response.json() as Promise<T>;
}

export function createAbsentRequest(payload: AbsentRequestFormPayload) {
  return request<AbsentRequest>("/api/absent-requests", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listAbsentRequests() {
  return request<AbsentRequest[]>("/api/absent-requests");
}

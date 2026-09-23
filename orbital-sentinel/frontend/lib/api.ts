import type { Event, Freshness, OrbitalObject } from "./types";

const BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { cache: "no-store", ...init });
  if (!res.ok) throw new Error((await res.text()) || `Request failed: ${res.status}`);
  return res.json();
}

export async function fetchEvents(): Promise<{ events: Event[] }> {
  return request("/api/events?limit=25");
}

export async function fetchObjects(): Promise<{ objects: OrbitalObject[]; data_freshness: Freshness }> {
  return request("/api/objects?window_hours=3&step_seconds=120&limit=80");
}

export async function explainEvent(id: string): Promise<{ event_id: string; explanation: string; source: string }> {
  return request(`/api/events/${id}/explain`, { method: "POST" });
}

export async function runScreen(): Promise<Record<string, unknown>> {
  return request("/api/screen", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ window_hours: 3, coarse_step_seconds: 60, refine_step_seconds: 1, max_objects: 80 }),
  });
}

"use client";

import type { Event, RiskTier } from "@/lib/types";

function riskLabel(risk: RiskTier) {
  return risk === "HIGH" ? "High" : risk === "MEDIUM" ? "Medium" : "Low";
}

export function Sidebar({ events, selectedId, onSelect, onRefresh, running }: {
  events: Event[];
  selectedId: string | null;
  onSelect: (event: Event) => void;
  onRefresh: () => void;
  running: boolean;
}) {
  const priority = { HIGH: 0, MEDIUM: 1, LOW: 2 } as const;
  const displayEvents = [...events].sort((a, b) => priority[a.screening_risk] - priority[b.screening_risk] || new Date(a.tca).getTime() - new Date(b.tca).getTime());

  return (
    <aside className="w-[360px] shrink-0 border-r border-white/10 bg-[#070a10] px-4 py-5">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-[11px] tracking-[0.28em] text-sky-300/70">MISSION CONTROL</div>
          <h1 className="mt-1 text-xl font-semibold tracking-tight">ORBITAL SENTINEL</h1>
        </div>
        <button
          onClick={onRefresh}
          disabled={running}
          className="rounded-lg border border-white/10 bg-white/[0.03] px-3 py-2 text-xs text-white/80 hover:bg-white/[0.07] disabled:opacity-50"
        >
          {running ? "SCREENING" : "RE-SCREEN"}
        </button>
      </div>

      <div className="mt-6 flex items-center justify-between rounded-xl border border-white/10 bg-white/[0.025] px-3 py-2.5">
        <div>
          <div className="text-[10px] uppercase tracking-[0.22em] text-white/40">Alert stream</div>
          <div className="mt-1 text-sm text-white/80">{events.length} screened events</div>
        </div>
        <div className="h-2.5 w-2.5 rounded-full bg-emerald-400 shadow-[0_0_12px_rgba(52,211,153,.65)]" />
      </div>

      <div className="mt-5 space-y-2 overflow-y-auto" style={{ maxHeight: "calc(100vh - 180px)" }}>
        {events.length === 0 && <div className="py-10 text-center text-sm text-white/35">No conjunctions loaded yet.</div>}
        {displayEvents.map((event) => {
          const high = event.screening_risk === "HIGH";
          return (
            <button
              key={event.id}
              onClick={() => onSelect(event)}
              className={`w-full rounded-xl border px-3.5 py-3 text-left transition ${selectedId === event.id ? "border-sky-300/30 bg-sky-300/[0.08]" : "border-white/8 bg-white/[0.02] hover:bg-white/[0.045]"}`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="truncate text-sm font-medium">{event.object_a.name}</div>
                  <div className="mt-0.5 truncate text-xs text-white/40">↕ {event.object_b.name}</div>
                </div>
                <span className={`shrink-0 rounded-full px-2 py-1 text-[10px] font-semibold uppercase tracking-wider ${high ? "bg-rose-400/12 text-rose-300" : event.screening_risk === "MEDIUM" ? "bg-amber-300/12 text-amber-200" : "bg-white/6 text-white/50"}`}>{riskLabel(event.screening_risk)}</span>
              </div>
              <div className="mt-3 flex items-end justify-between">
                <div>
                  <div className="mono text-sm tabular-nums">{(event.miss_distance_m / 1000).toFixed(3)} km</div>
                  <div className="mt-1 text-[10px] uppercase tracking-[0.16em] text-white/30">miss distance</div>
                </div>
                <div className="text-right text-[10px] text-white/35">{new Date(event.tca).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })} UTC</div>
              </div>
            </button>
          );
        })}
      </div>
    </aside>
  );
}

"use client";

import { useEffect, useState } from "react";
import type { Event } from "@/lib/types";
import { explainEvent } from "@/lib/api";

export function Inspector({ event }: { event: Event | null }) {
  const [loading, setLoading] = useState(false);
  const [explanation, setExplanation] = useState(event?.explanation ?? "");
  useEffect(() => setExplanation(event?.explanation ?? ""), [event?.id, event?.explanation]);

  if (!event) {
    return <div className="glass rounded-2xl p-5 text-sm text-white/30">Select a conjunction event to inspect TCA, miss distance, and the grounded explanation.</div>;
  }

  async function handleExplain() {
    setLoading(true);
    try {
      const result = await explainEvent(event.id);
      setExplanation(result.explanation);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="glass rounded-2xl p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="text-[10px] uppercase tracking-[0.18em] text-white/35">Event detail</div>
          <div className="mt-1 text-lg font-medium">{event.object_a.name}</div>
          <div className="text-sm text-white/35">↕ {event.object_b.name}</div>
        </div>
        <div className={`rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-widest ${event.screening_risk === "HIGH" ? "bg-rose-400/12 text-rose-300" : event.screening_risk === "MEDIUM" ? "bg-amber-300/12 text-amber-200" : "bg-white/6 text-white/45"}`}>{event.screening_risk} SCREENING</div>
      </div>

      <div className="mt-5 grid grid-cols-3 gap-2">
        <Metric label="TCA" value={new Date(event.tca).toLocaleTimeString([], { hour12: false })} />
        <Metric label="Miss" value={`${(event.miss_distance_m / 1000).toFixed(3)} km`} />
        <Metric label="Rel. speed" value={`${(event.relative_speed_mps / 1000).toFixed(3)} km/s`} />
      </div>

      <div className="mt-5 flex items-center justify-between">
        <div className="text-[10px] uppercase tracking-[0.18em] text-white/30">Grounded operator summary</div>
        <button onClick={handleExplain} disabled={loading} className="rounded-lg border border-white/10 px-3 py-1.5 text-xs text-white/65 hover:bg-white/[0.06] disabled:opacity-50">{loading ? "GENERATING" : "GENERATE"}</button>
      </div>
      <div className="mt-3 rounded-xl border border-white/8 bg-black/10 p-3.5 text-sm leading-6 text-white/65">
        {explanation || "No explanation generated yet. The explanation service receives only deterministic event facts."}
      </div>
      <div className="mt-3 text-[10px] leading-4 text-white/25">Data snapshot: {new Date(event.data_retrieved_at).toLocaleString()}</div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return <div className="rounded-xl border border-white/8 bg-white/[0.02] p-3"><div className="text-[9px] uppercase tracking-[0.18em] text-white/28">{label}</div><div className="mono mt-1.5 text-xs tabular-nums text-white/75">{value}</div></div>;
}

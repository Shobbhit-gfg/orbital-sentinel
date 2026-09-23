"use client";

import { useMemo, useState } from "react";
import type { Event, OrbitalObject } from "@/lib/types";
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

function buildSeparation(event: Event | null) {
  if (!event) return [];
  const center = new Date(event.tca).getTime();
  return Array.from({ length: 13 }, (_, i) => {
    const seconds = (i - 6) * 30;
    const minutes = seconds / 60;
    const miss = Math.sqrt((event.miss_distance_m / 1000) ** 2 + (minutes * event.relative_speed_mps / 1000) ** 2);
    return { time: new Date(center + seconds * 1000).toISOString(), minutes, value: miss };
  });
}

function nearestHeight(object: OrbitalObject | undefined, tca: string) {
  if (!object?.samples.length) return null;
  const target = new Date(tca).getTime();
  return object.samples.reduce((best, current) => Math.abs(new Date(current.time).getTime() - target) < Math.abs(new Date(best.time).getTime() - target) ? current : best).geodetic[2];
}

export function Timeline({ event, objects }: { event: Event | null; objects: OrbitalObject[] }) {
  const [mode, setMode] = useState<"separation" | "altitude">("separation");
  const objectA = objects.find((o) => o.norad_id === event?.object_a.norad_id);
  const objectB = objects.find((o) => o.norad_id === event?.object_b.norad_id);
  const data = useMemo(() => {
    if (!event) return [];
    if (mode === "separation") return buildSeparation(event);
    const a = nearestHeight(objectA, event.tca) ?? 0;
    const b = nearestHeight(objectB, event.tca) ?? 0;
    return [{ minutes: -3, a, b }, { minutes: -2, a, b }, { minutes: -1, a, b }, { minutes: 0, a, b }, { minutes: 1, a, b }, { minutes: 2, a, b }, { minutes: 3, a, b }];
  }, [event, mode, objectA, objectB]);

  return (
    <div className="glass rounded-2xl p-4">
      <div className="flex items-center justify-between gap-4">
        <div><div className="text-[10px] uppercase tracking-[0.18em] text-white/35">Event timeline</div><div className="mt-1 text-sm text-white/80">{mode === "separation" ? "Relative geometry around TCA" : "Altitude context around TCA"}</div></div>
        <div className="flex rounded-lg border border-white/8 bg-white/[0.02] p-0.5 text-[10px] uppercase tracking-widest">
          <button onClick={() => setMode("separation")} className={`rounded-md px-2 py-1 ${mode === "separation" ? "bg-white/10 text-white/80" : "text-white/30"}`}>Separation</button>
          <button onClick={() => setMode("altitude")} className={`rounded-md px-2 py-1 ${mode === "altitude" ? "bg-white/10 text-white/80" : "text-white/30"}`}>Altitude</button>
        </div>
      </div>
      <div className="mt-3 h-[170px]">
        {!event ? <div className="flex h-full items-center justify-center text-sm text-white/25">Select an alert.</div> : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 10, right: 12, left: -15, bottom: 0 }}>
              <XAxis dataKey="minutes" tickFormatter={(v) => `${v}m`} stroke="rgba(255,255,255,.22)" tick={{ fill: "rgba(255,255,255,.35)", fontSize: 10 }} />
              <YAxis stroke="rgba(255,255,255,.22)" tick={{ fill: "rgba(255,255,255,.35)", fontSize: 10 }} />
              <Tooltip contentStyle={{ background: "#0b1018", border: "1px solid rgba(255,255,255,.1)", borderRadius: 10, color: "#fff" }} />
              {mode === "separation" ? <Line type="monotone" dataKey="value" stroke="#7dd3fc" strokeWidth={2.2} dot={false} /> : <><Line type="monotone" dataKey="a" stroke="#93c5fd" strokeWidth={2} dot={false} /><Line type="monotone" dataKey="b" stroke="#fda4af" strokeWidth={2} dot={false} /></>}
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}

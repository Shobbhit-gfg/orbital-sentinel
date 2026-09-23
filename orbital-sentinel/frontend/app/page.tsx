"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { fetchEvents, fetchObjects, runScreen } from "@/lib/api";
import type { Event, Freshness, OrbitalObject } from "@/lib/types";
import Globe from "@/components/Globe";
import { Sidebar } from "@/components/Sidebar";
import { Freshness as FreshnessBadge } from "@/components/Freshness";
import { Inspector } from "@/components/Inspector";
import { Timeline } from "@/components/Timeline";
import { TimeScrubber } from "@/components/TimeScrubber";

export default function Page() {
  const [events, setEvents] = useState<Event[]>([]);
  const [objects, setObjects] = useState<OrbitalObject[]>([]);
  const [freshness, setFreshness] = useState<Freshness>(null);
  const [selected, setSelected] = useState<Event | null>(null);
  const [running, setRunning] = useState(false);
  const [viewer, setViewer] = useState<any>(null);

  const load = useCallback(async () => {
    const [eventsResult, objectsResult] = await Promise.all([fetchEvents(), fetchObjects()]);
    setEvents(eventsResult.events);
    setObjects(objectsResult.objects);
    setFreshness(objectsResult.data_freshness);
    setSelected((current) => current ? (eventsResult.events.find((e) => e.id === current.id) ?? eventsResult.events[0] ?? null) : (eventsResult.events[0] ?? null));
  }, []);

  useEffect(() => { load().catch(console.error); }, [load]);

  async function handleScreen() {
    setRunning(true);
    try {
      await runScreen();
      await load();
    } catch (error) {
      console.error(error);
    } finally {
      setRunning(false);
    }
  }

  const highCount = useMemo(() => events.filter((e) => e.screening_risk === "HIGH").length, [events]);

  return (
    <main className="flex h-screen overflow-hidden bg-[#06080d] text-white">
      <Sidebar events={events} selectedId={selected?.id ?? null} onSelect={setSelected} onRefresh={handleScreen} running={running} />
      <section className="relative min-w-0 flex-1">
        <Globe objects={objects} events={events} selectedEvent={selected} onReady={setViewer} />

        <div className="pointer-events-none absolute inset-x-0 top-0 z-10 flex items-start justify-between p-5">
          <div className="pointer-events-auto">
            <FreshnessBadge freshness={freshness} />
          </div>
          <div className="flex items-center gap-2">
            <div className="glass rounded-xl px-3 py-2 text-right">
              <div className="text-[9px] uppercase tracking-[0.18em] text-white/30">3h screening window</div>
              <div className="mt-0.5 text-xs text-white/60">{highCount} high-priority · {events.length} total</div>
            </div>
            <div className="glass rounded-xl px-3 py-2 text-right">
              <div className="text-[9px] uppercase tracking-[0.18em] text-white/30">Coordinate frame</div>
              <div className="mono mt-0.5 text-xs text-white/60">ECEF / WGS84</div>
            </div>
          </div>
        </div>

        <div className="absolute inset-x-5 bottom-5 z-10 ml-[380px] grid grid-cols-[1.05fr_.95fr] gap-3">
          <Timeline event={selected} objects={objects} />
          <Inspector event={selected} />
        </div>
        <div className="absolute inset-x-5 bottom-[250px] z-10 ml-[380px] max-w-[780px]">
          <TimeScrubber viewer={viewer} />
        </div>
      </section>
    </main>
  );
}

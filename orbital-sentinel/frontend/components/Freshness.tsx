import type { Freshness } from "@/lib/types";

export function Freshness({ freshness }: { freshness: Freshness }) {
  if (!freshness) return <div className="glass rounded-xl px-3 py-2 text-xs text-white/35">DATA OFFLINE</div>;
  const ageMin = Math.max(0, (Date.now() - new Date(freshness.retrieved_at).getTime()) / 60000);
  const status = freshness.status === "SUCCESS" && ageMin < 180 ? "LIVE DATA" : "STALE DATA";
  return (
    <div className="glass flex items-center gap-3 rounded-xl px-3 py-2.5">
      <div className={`h-2 w-2 rounded-full ${status === "LIVE DATA" ? "bg-emerald-400 shadow-[0_0_12px_rgba(52,211,153,.7)]" : "bg-amber-300"}`} />
      <div>
        <div className="text-[9px] font-semibold uppercase tracking-[0.18em] text-white/40">{status}</div>
        <div className="mt-0.5 text-[11px] text-white/65">retrieved {Math.round(ageMin)} min ago · {freshness.record_count} records</div>
      </div>
    </div>
  );
}

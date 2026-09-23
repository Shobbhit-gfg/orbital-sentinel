
"use client";

import { useEffect, useState } from "react";

export function TimeScrubber({ viewer }: { viewer: any }) {
  const [value, setValue] = useState(0);
  const [playing, setPlaying] = useState(false);

  useEffect(() => {
    if (!viewer?.clock) return;
    const update = () => {
      const C = requireCesium();
      const span = C.JulianDate.secondsDifference(viewer.clock.stopTime, viewer.clock.startTime);
      const elapsed = C.JulianDate.secondsDifference(viewer.clock.currentTime, viewer.clock.startTime);
      setValue(Math.max(0, Math.min(1000, span > 0 ? (elapsed / span) * 1000 : 0)));
    };
    viewer.clock.onTick.addEventListener(update);
    update();
    return () => viewer.clock.onTick.removeEventListener(update);
  }, [viewer]);

  if (!viewer?.clock) return null;

  async function seek(next: number) {
    const C = await import("cesium");
    setValue(next);
    const span = C.JulianDate.secondsDifference(viewer.clock.stopTime, viewer.clock.startTime);
    const seconds = (next / 1000) * span;
    viewer.clock.currentTime = C.JulianDate.addSeconds(viewer.clock.startTime, seconds, new C.JulianDate());
  }

  const current = requireCesium().JulianDate.toDate(viewer.clock.currentTime).toISOString();

  return (
    <div className="glass rounded-2xl px-4 py-3 shadow-2xl shadow-black/30">
      <div className="flex items-center justify-between gap-4">
        <div>
          <div className="text-[10px] uppercase tracking-[0.2em] text-white/35">Prediction window</div>
          <div className="mt-1 mono text-xs text-white/70">{current}</div>
        </div>
        <button
          onClick={() => { viewer.clock.shouldAnimate = !viewer.clock.shouldAnimate; setPlaying(viewer.clock.shouldAnimate); }}
          className="rounded-lg border border-white/10 bg-white/[0.03] px-3 py-1.5 text-xs text-white/65"
        >{playing ? "PAUSE" : "PLAY"}</button>
      </div>
      <input aria-label="Prediction time" type="range" min={0} max={1000} step={1} value={value} onChange={(e) => seek(Number(e.target.value))} className="mt-3 w-full accent-sky-300" />
      <div className="mt-1 flex justify-between text-[9px] uppercase tracking-wider text-white/25"><span>Now</span><span>+3h</span></div>
    </div>
  );
}

let cesiumModule: any = null;
function requireCesium() {
  // Browser-only component; the dynamic import is kicked off by Globe and cached here after load.
  if (cesiumModule) return cesiumModule;
  // A synchronous require is not available under ESM Next server execution, so callers should prefer seek/onTick.
  // This fallback keeps the render path minimal until the globe has initialized.
  return (window as any).Cesium ?? { JulianDate: { toDate: (x: any) => new Date(), secondsDifference: () => 1 } };
}

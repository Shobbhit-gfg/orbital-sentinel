"use client";

import { useEffect, useRef } from "react";
import type { Event, OrbitalObject } from "@/lib/types";

export default function Globe({ objects, events, selectedEvent, onReady }: {
  objects: OrbitalObject[];
  events: Event[];
  selectedEvent: Event | null;
  onReady?: (viewer: any) => void;
}) {
  const ref = useRef<HTMLDivElement | null>(null);
  const viewerRef = useRef<any>(null);

  useEffect(() => {
    let disposed = false;
    let viewer: any;

    (async () => {
      const Cesium = await import("cesium");
      if (disposed || !ref.current) return;
      if (process.env.NEXT_PUBLIC_CESIUM_ION_TOKEN) Cesium.Ion.defaultAccessToken = process.env.NEXT_PUBLIC_CESIUM_ION_TOKEN;
      (window as any).CESIUM_BASE_URL = "/cesium/";
      (window as any).Cesium = Cesium;

      viewer = new Cesium.Viewer(ref.current, {
        animation: false,
        timeline: false,
        geocoder: false,
        homeButton: false,
        sceneModePicker: false,
        navigationHelpButton: false,
        baseLayerPicker: false,
        fullscreenButton: false,
        infoBox: false,
        selectionIndicator: false,
        shouldAnimate: false,
        baseLayer: new Cesium.ImageryLayer(new Cesium.UrlTemplateImageryProvider({ url: "https://tile.openstreetmap.org/{z}/{x}/{y}.png" })),
      });

      viewer.scene.globe.enableLighting = false;
      viewer.scene.backgroundColor = Cesium.Color.fromCssColorString("#05070b");
      viewerRef.current = viewer;
      onReady?.(viewer);
    })();

    return () => {
      disposed = true;
      if (viewerRef.current && !viewerRef.current.isDestroyed()) viewerRef.current.destroy();
      viewerRef.current = null;
    };
  }, [onReady]);

  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer || !objects.length) return;
    let cancelled = false;
    (async () => {
      const Cesium = await import("cesium");
      if (cancelled) return;
      viewer.entities.removeAll();

      for (const object of objects) {
        const property = new Cesium.SampledPositionProperty(Cesium.ReferenceFrame.FIXED);
        const times: any[] = [];
        const positions: any[] = [];
        for (const sample of object.samples) {
          times.push(Cesium.JulianDate.fromIso8601(sample.time));
          positions.push(new Cesium.Cartesian3(sample.ecef[0], sample.ecef[1], sample.ecef[2]));
        }
        if (!positions.length) continue;
        property.addSamples(times, positions);
        property.forwardExtrapolationType = Cesium.ExtrapolationType.HOLD;
        property.backwardExtrapolationType = Cesium.ExtrapolationType.HOLD;

        viewer.entities.add({
          id: `object-${object.norad_id}`,
          name: object.name,
          position: property,
          point: { pixelSize: 5, color: Cesium.Color.fromCssColorString("#9bdcff"), outlineColor: Cesium.Color.fromCssColorString("#0b1220"), outlineWidth: 2 },
          path: { show: true, width: 1.2, material: Cesium.Color.fromCssColorString("#60a5fa").withAlpha(0.35), leadTime: 10800, trailTime: 60 },
          properties: { norad_id: object.norad_id },
        });
      }

      const allSamples = objects.flatMap((object) => object.samples);
      if (allSamples.length) {
        const start = Cesium.JulianDate.fromIso8601(allSamples[0].time);
        const stop = Cesium.JulianDate.fromIso8601(allSamples[allSamples.length - 1].time);
        viewer.clock.startTime = start.clone();
        viewer.clock.stopTime = stop.clone();
        viewer.clock.currentTime = start.clone();
        viewer.clock.multiplier = 60;
        viewer.clock.shouldAnimate = false;
      }

      // Render every persisted conjunction at its own TCA. The selected event is re-styled below.
      for (const event of events) {
        const a = viewer.entities.getById(`object-${event.object_a.norad_id}`);
        const b = viewer.entities.getById(`object-${event.object_b.norad_id}`);
        if (!a?.position || !b?.position) continue;
        const tca = Cesium.JulianDate.fromIso8601(event.tca);
        const pa = a.position.getValue(tca);
        const pb = b.position.getValue(tca);
        if (!pa || !pb) continue;
        viewer.entities.add({
          id: `event-line-${event.id}`,
          show: true,
          polyline: {
            positions: [pa, pb],
            width: event.screening_risk === "HIGH" ? 3.2 : 1.6,
            material: (event.screening_risk === "HIGH" ? Cesium.Color.fromCssColorString("#fb7185") : Cesium.Color.fromCssColorString("#fbbf24")).withAlpha(0.55),
          },
          properties: { event_id: event.id },
        });
      }
    })();
    return () => { cancelled = true; };
  }, [objects, events]);

  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer || !selectedEvent) return;
    let cancelled = false;
    (async () => {
      const Cesium = await import("cesium");
      if (cancelled) return;
      const a = viewer.entities.getById(`object-${selectedEvent.object_a.norad_id}`);
      const b = viewer.entities.getById(`object-${selectedEvent.object_b.norad_id}`);
      if (!a?.position || !b?.position) return;
      const tca = Cesium.JulianDate.fromIso8601(selectedEvent.tca);
      const pa = a.position.getValue(tca);
      const pb = b.position.getValue(tca);
      if (!pa || !pb) return;
      const mid = Cesium.Cartesian3.midpoint(pa, pb, new Cesium.Cartesian3());
      viewer.clock.currentTime = tca;
      viewer.camera.flyToBoundingSphere(new Cesium.BoundingSphere(mid, 400000), { duration: 0.8 });
    })();
    return () => { cancelled = true; };
  }, [selectedEvent]);

  return <div ref={ref} className="absolute inset-0" />;
}

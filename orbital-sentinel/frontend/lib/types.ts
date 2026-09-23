export type RiskTier = "LOW" | "MEDIUM" | "HIGH";

export type OrbitSample = {
  time: string;
  ecef: [number, number, number];
  geodetic: [number, number, number];
};

export type OrbitalObject = {
  norad_id: string;
  name: string;
  epoch: string | null;
  retrieved_at: string;
  source_url: string;
  samples: OrbitSample[];
};

export type Event = {
  id: string;
  object_a: { norad_id: string; name: string };
  object_b: { norad_id: string; name: string };
  tca: string;
  miss_distance_m: number;
  relative_speed_mps: number;
  screening_risk: RiskTier;
  window_start: string;
  window_end: string;
  data_retrieved_at: string;
  explanation?: string | null;
};

export type Freshness = {
  retrieved_at: string;
  source_url: string;
  record_count: number;
  checksum_sha256: string;
  status: string;
} | null;

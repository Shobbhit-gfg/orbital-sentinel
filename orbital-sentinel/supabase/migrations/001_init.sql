create extension if not exists pgcrypto;

create table if not exists public.objects (
  norad_id text primary key,
  name text not null,
  object_type text not null default 'PAYLOAD_OR_OTHER',
  epoch timestamptz,
  omm_json jsonb not null,
  source_url text not null,
  retrieved_at timestamptz not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.ingestion_runs (
  id uuid primary key default gen_random_uuid(),
  source_url text not null,
  retrieved_at timestamptz not null,
  record_count integer not null default 0,
  checksum_sha256 text not null,
  status text not null default 'SUCCESS',
  created_at timestamptz not null default now()
);

create table if not exists public.conjunction_events (
  id text primary key,
  object_a_norad text not null references public.objects(norad_id) on delete cascade,
  object_b_norad text not null references public.objects(norad_id) on delete cascade,
  tca timestamptz not null,
  miss_distance_m double precision not null check (miss_distance_m >= 0),
  relative_speed_mps double precision not null check (relative_speed_mps >= 0),
  screening_risk text not null check (screening_risk in ('LOW', 'MEDIUM', 'HIGH')),
  window_start timestamptz not null,
  window_end timestamptz not null,
  data_retrieved_at timestamptz not null,
  algorithm_version text not null,
  explanation text,
  explanation_model text,
  created_at timestamptz not null default now()
);

create index if not exists conjunction_events_tca_idx on public.conjunction_events(tca);
create index if not exists conjunction_events_risk_idx on public.conjunction_events(screening_risk);

create table if not exists public.trajectory_cache (
  norad_id text not null references public.objects(norad_id) on delete cascade,
  sample_time timestamptz not null,
  ecef_x_m double precision not null,
  ecef_y_m double precision not null,
  ecef_z_m double precision not null,
  lat_deg double precision not null,
  lon_deg double precision not null,
  height_km double precision not null,
  data_retrieved_at timestamptz not null,
  created_at timestamptz not null default now(),
  primary key (norad_id, sample_time)
);

create index if not exists trajectory_cache_sample_time_idx on public.trajectory_cache(sample_time);

-- Backend only: keep Data API access locked down. The API server uses the service-role key.
alter table public.objects enable row level security;
alter table public.ingestion_runs enable row level security;
alter table public.conjunction_events enable row level security;
alter table public.trajectory_cache enable row level security;

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists objects_set_updated_at on public.objects;
create trigger objects_set_updated_at before update on public.objects
for each row execute function public.set_updated_at();

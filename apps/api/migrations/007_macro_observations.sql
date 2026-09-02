create table if not exists public.macro_observations (
    id uuid primary key default gen_random_uuid(),
    source text not null,
    series_id text not null,
    period text not null,
    value double precision not null,
    released_at timestamptz,
    retrieved_at timestamptz not null,
    vintage_date timestamptz,
    created_at timestamptz not null default now(),
    unique (source, series_id, period, vintage_date)
);

create index if not exists macro_observations_series_period_idx
    on public.macro_observations (series_id, period desc);

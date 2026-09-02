create table if not exists public.news_event_clusters (
    logical_event_key text primary key,
    canonical_provider text not null,
    canonical_provider_id text not null,
    event_count integer not null check (event_count > 0),
    providers jsonb not null default '[]'::jsonb,
    first_available_at timestamptz not null,
    last_available_at timestamptz not null,
    updated_at timestamptz not null default now()
);

create index if not exists news_event_clusters_updated_idx
    on public.news_event_clusters (updated_at desc);

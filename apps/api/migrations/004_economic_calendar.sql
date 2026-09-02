create table if not exists public.economic_calendar_events (
    id uuid primary key default gen_random_uuid(),
    provider text not null,
    provider_event_id text not null,
    event text not null,
    currency text not null,
    impact text not null,
    scheduled_at timestamptz not null,
    actual double precision,
    forecast double precision,
    previous double precision,
    available_at timestamptz not null,
    created_at timestamptz not null default now(),
    unique (provider, provider_event_id)
);

create index if not exists economic_calendar_scheduled_idx
    on public.economic_calendar_events (scheduled_at);

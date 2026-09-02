create table if not exists public.macro_reactions (
    id uuid primary key default gen_random_uuid(),
    event_id uuid not null references public.economic_calendar_events(id) on delete cascade,
    instrument text not null,
    horizon text not null,
    return_points double precision,
    return_pct double precision,
    observed_at timestamptz not null,
    created_at timestamptz not null default now(),
    unique (event_id, instrument, horizon)
);

create index if not exists macro_reactions_event_idx on public.macro_reactions (event_id);

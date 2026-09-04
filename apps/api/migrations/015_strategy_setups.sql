create table if not exists public.strategy_setups (
    id uuid primary key default gen_random_uuid(),
    strategy_id uuid not null references public.strategies(id) on delete restrict,
    session_date date not null,
    trigger_at timestamptz not null,
    conditions jsonb not null default '[]'::jsonb,
    created_at timestamptz not null default now(),
    unique(strategy_id, session_date)
);

create index if not exists strategy_setups_session_idx on public.strategy_setups (session_date, trigger_at);

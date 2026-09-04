create table if not exists public.strategy_outcomes (
    id uuid primary key default gen_random_uuid(),
    setup_id uuid not null unique references public.strategy_setups(id) on delete restrict,
    strategy_id uuid not null references public.strategies(id) on delete restrict,
    session_date date not null,
    observed_at timestamptz not null,
    return_pct double precision,
    mfe double precision,
    mae double precision,
    created_at timestamptz not null default now()
);

create index if not exists strategy_outcomes_strategy_idx on public.strategy_outcomes (strategy_id, observed_at);

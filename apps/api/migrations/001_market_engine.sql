create table if not exists public.market_contracts (
    id uuid primary key default gen_random_uuid(),
    product text not null,
    raw_contract_symbol text not null,
    continuous_symbol text not null,
    expiration date,
    roll_date date,
    created_at timestamptz not null default now(),
    unique (product, raw_contract_symbol)
);

create table if not exists public.market_bars (
    id uuid primary key default gen_random_uuid(),
    symbol text not null,
    timestamp timestamptz not null,
    timeframe text not null,
    open double precision not null,
    high double precision not null,
    low double precision not null,
    close double precision not null,
    volume double precision not null default 0,
    provider text not null,
    ingested_at timestamptz not null,
    available_at timestamptz not null,
    unique (symbol, timestamp, timeframe, provider)
);

create index if not exists market_bars_timestamp_idx on public.market_bars (symbol, timestamp);

create table if not exists public.market_sessions (
    session_date date primary key,
    contract_id uuid not null references public.market_contracts(id),
    nq_open double precision not null,
    nq_high double precision not null,
    nq_low double precision not null,
    nq_close double precision not null,
    overnight_open double precision not null,
    overnight_high double precision not null,
    overnight_low double precision not null,
    overnight_close double precision not null,
    prior_day_high double precision,
    prior_day_low double precision,
    prior_day_close double precision,
    gap_points double precision,
    gap_pct double precision,
    overnight_return double precision,
    overnight_range double precision not null,
    atr_14 double precision,
    created_at timestamptz not null default now()
);

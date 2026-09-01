create table if not exists public.market_contract_rollovers (
    id uuid primary key default gen_random_uuid(),
    product text not null,
    from_contract text not null,
    to_contract text not null,
    roll_date date not null,
    provider text not null,
    created_at timestamptz not null default now(),
    unique (product, from_contract, to_contract)
);

create index if not exists market_contract_rollovers_date_idx
    on public.market_contract_rollovers (product, roll_date);

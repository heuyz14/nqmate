create table if not exists public.strategies (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    description text not null default '',
    allowed_regimes jsonb not null default '[]'::jsonb,
    required_conditions jsonb not null default '[]'::jsonb,
    confirmation_conditions jsonb not null default '[]'::jsonb,
    invalidation_conditions jsonb not null default '[]'::jsonb,
    entry_logic text not null,
    target_logic text not null,
    stop_logic text not null,
    active boolean not null default true,
    created_at timestamptz not null default now()
);

create index if not exists strategies_active_idx on public.strategies (active, created_at desc);

create table if not exists public.session_feature_snapshots (
    id uuid primary key default gen_random_uuid(),
    session_date date not null,
    snapshot_timestamp timestamptz not null,
    symbol text not null,
    contract text not null,
    feature_version text not null,
    features jsonb not null default '{}'::jsonb,
    available_at timestamptz not null,
    created_at timestamptz not null default now(),
    unique (session_date, snapshot_timestamp, symbol, contract, feature_version)
);

create index if not exists session_feature_snapshots_date_idx
    on public.session_feature_snapshots (session_date, snapshot_timestamp);

alter table public.session_feature_snapshots enable row level security;
revoke all on public.session_feature_snapshots from anon, authenticated;
grant all on public.session_feature_snapshots to service_role;

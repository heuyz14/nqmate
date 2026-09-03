create table if not exists public.analogue_vectors (
    session_date date primary key,
    features jsonb not null,
    outcomes jsonb not null default '{}'::jsonb,
    available_at timestamptz not null,
    feature_version text not null,
    created_at timestamptz not null default now()
);

create index if not exists analogue_vectors_available_idx
    on public.analogue_vectors (available_at, session_date);

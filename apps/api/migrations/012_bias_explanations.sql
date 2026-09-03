create table if not exists public.bias_explanations (
    id uuid primary key default gen_random_uuid(),
    prediction_id uuid not null references public.bias_predictions(id) on delete cascade,
    direction text not null,
    confidence double precision not null check (confidence between 0 and 1),
    summary text not null,
    bull_case jsonb not null default '[]'::jsonb,
    bear_case jsonb not null default '[]'::jsonb,
    invalidation jsonb not null default '[]'::jsonb,
    risks jsonb not null default '[]'::jsonb,
    created_at timestamptz not null default now()
);

create index if not exists bias_explanations_prediction_idx
    on public.bias_explanations (prediction_id, created_at desc);

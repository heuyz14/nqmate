create table if not exists public.bias_predictions (
    id uuid primary key default gen_random_uuid(),
    direction text not null,
    score double precision not null,
    confidence double precision not null,
    recommendation text not null,
    catalyst_risk text,
    evidence jsonb not null default '[]'::jsonb,
    bull_case jsonb not null default '[]'::jsonb,
    bear_case jsonb not null default '[]'::jsonb,
    invalidation jsonb not null default '[]'::jsonb,
    uncertainty jsonb not null default '[]'::jsonb,
    model_version text not null,
    feature_version text not null,
    created_at timestamptz not null default now()
);

create index if not exists bias_predictions_created_idx
    on public.bias_predictions (created_at desc);

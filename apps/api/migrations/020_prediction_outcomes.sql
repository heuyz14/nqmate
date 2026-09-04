create table if not exists public.bias_prediction_outcomes (
    id uuid primary key default gen_random_uuid(),
    prediction_id uuid not null references public.bias_predictions(id) on delete cascade,
    session_date date not null,
    horizon text not null,
    realized_return double precision,
    realized_direction boolean,
    correct boolean,
    observed_at timestamptz not null,
    source text not null default 'historical_session_outcome',
    created_at timestamptz not null default now(),
    unique (prediction_id, horizon)
);

create index if not exists bias_prediction_outcomes_prediction_idx
    on public.bias_prediction_outcomes (prediction_id, horizon);

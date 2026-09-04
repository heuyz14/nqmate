create table if not exists public.ml_datasets (
    id uuid primary key default gen_random_uuid(),
    version text not null unique,
    target text not null,
    feature_version text not null,
    row_count integer not null check (row_count >= 0),
    start_date date not null,
    end_date date not null,
    created_at timestamptz not null default now()
);

create table if not exists public.ml_models (
    id uuid primary key default gen_random_uuid(),
    name text not null unique,
    target text not null,
    algorithm text not null,
    algorithm_version text not null,
    feature_version text not null,
    dataset_version text not null references public.ml_datasets(version) on delete restrict,
    metrics jsonb not null default '{}'::jsonb,
    hyperparameters jsonb not null default '{}'::jsonb,
    artifact_path text not null,
    training_start date not null,
    training_end date not null,
    active boolean not null default false,
    created_at timestamptz not null default now()
);

create index if not exists ml_models_target_idx on public.ml_models (target, created_at desc);

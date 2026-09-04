alter table public.bias_predictions
    add column if not exists input_snapshot jsonb not null default '{}'::jsonb;

create index if not exists bias_predictions_model_feature_idx
    on public.bias_predictions (model_version, feature_version, created_at desc);

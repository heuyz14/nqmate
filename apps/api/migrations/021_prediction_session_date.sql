alter table public.bias_predictions
    add column if not exists session_date date;

create index if not exists bias_predictions_session_date_idx
    on public.bias_predictions (session_date, created_at desc);

alter table public.session_feature_snapshots
    add column if not exists availability_policy text not null default 'strict'
    check (availability_policy in ('strict', 'event_time_reconstructed'));

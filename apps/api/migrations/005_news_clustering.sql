alter table public.news_events
    add column if not exists logical_event_key text;

create index if not exists news_events_logical_event_key_idx
    on public.news_events (logical_event_key);

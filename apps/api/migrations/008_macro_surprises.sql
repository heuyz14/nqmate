alter table public.economic_calendar_events
    add column if not exists surprise double precision;

alter table public.economic_calendar_events
    add column if not exists expected_nq_direction text,
    add column if not exists surprise_interpretation text;

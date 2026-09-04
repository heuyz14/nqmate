alter table public.strategy_outcomes
    add column if not exists regime text;

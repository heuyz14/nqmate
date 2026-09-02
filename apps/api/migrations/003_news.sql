create table if not exists public.news_articles (
    id uuid primary key default gen_random_uuid(), provider text not null, provider_id text not null,
    url text not null, headline text not null, source text not null,
    published_at timestamptz not null, available_at timestamptz not null, summary text,
    entities jsonb not null default '[]'::jsonb, topics jsonb not null default '[]'::jsonb,
    created_at timestamptz not null default now(), unique (provider, provider_id)
);

create table if not exists public.news_events (
    id uuid primary key default gen_random_uuid(), article_id uuid not null references public.news_articles(id) on delete cascade,
    event_type text not null, event_subtype text, event_timestamp timestamptz not null,
    stance text not null, sentiment double precision, nq_direction text not null, impact text,
    nq_relevance_score double precision not null check (nq_relevance_score between 0 and 1),
    impact_horizon text not null, themes jsonb not null default '[]'::jsonb, confidence double precision,
    summary text, reason text, model_version text not null, created_at timestamptz not null,
    unique (article_id)
);

create index if not exists news_articles_published_idx on public.news_articles (published_at desc);
create index if not exists news_events_relevance_idx on public.news_events (nq_relevance_score desc);

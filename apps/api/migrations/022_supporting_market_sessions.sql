-- Additive: existing NQ writers and consumers keep their table and conflict key.
begin;
alter table public.market_contracts
    add constraint market_contracts_id_product_key unique (id, product);

create table public.market_supporting_sessions (
    like public.market_sessions including defaults including constraints,
    product text not null default 'ES' check (product = 'ES'),
    primary key (product, session_date),
    foreign key (contract_id, product) references public.market_contracts(id, product)
);
alter table public.market_supporting_sessions rename column nq_open to regular_open;
alter table public.market_supporting_sessions rename column nq_high to regular_high;
alter table public.market_supporting_sessions rename column nq_low to regular_low;
alter table public.market_supporting_sessions rename column nq_close to regular_close;

alter table public.market_supporting_sessions enable row level security;
revoke all on public.market_supporting_sessions from anon, authenticated;
revoke all on public.market_supporting_sessions from service_role;
grant select, insert, update on public.market_supporting_sessions to service_role;
comment on table public.market_supporting_sessions is
    'Shared market context for NQ research; server-side writes only, not user-owned data.';
commit;

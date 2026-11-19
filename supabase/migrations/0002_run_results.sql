-- Store each run's reconciliation output (rows, counts, invoice checks, reviews)
-- with the run itself, so any API instance can serve it.
alter table runs add column if not exists result jsonb not null default '{}'::jsonb;

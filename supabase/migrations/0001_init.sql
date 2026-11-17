create extension if not exists vector;

create table firms (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  daily_token_cap int not null default 200000,
  daily_inr_cap numeric not null default 50,
  created_at timestamptz not null default now()
);

create table memberships (
  user_id uuid not null references auth.users(id) on delete cascade,
  firm_id uuid not null references firms(id) on delete cascade,
  role text not null check (role in ('owner', 'member')),
  primary key (user_id, firm_id)
);

create table clients (
  id uuid primary key default gen_random_uuid(),
  firm_id uuid not null references firms(id) on delete cascade,
  name text not null,
  gstin text not null,
  created_at timestamptz not null default now()
);

create table runs (
  id uuid primary key default gen_random_uuid(),
  firm_id uuid not null references firms(id) on delete cascade,
  client_id uuid not null references clients(id) on delete cascade,
  period text not null,
  status text not null default 'queued',
  created_by uuid references auth.users(id),
  created_at timestamptz not null default now()
);

create table gstr2b_rows (
  id bigserial primary key,
  firm_id uuid not null references firms(id) on delete cascade,
  run_id uuid not null references runs(id) on delete cascade,
  supplier_gstin text not null,
  invoice_no text not null,
  invoice_date date not null,
  taxable_value numeric not null,
  igst numeric not null default 0, cgst numeric not null default 0,
  sgst numeric not null default 0, cess numeric not null default 0
);

create table book_rows (
  id bigserial primary key,
  firm_id uuid not null references firms(id) on delete cascade,
  run_id uuid not null references runs(id) on delete cascade,
  row_id int not null,
  supplier_gstin text not null,
  invoice_no text not null,
  invoice_date date not null,
  taxable_value numeric not null,
  igst numeric not null default 0, cgst numeric not null default 0,
  sgst numeric not null default 0, cess numeric not null default 0
);

create table matches (
  id bigserial primary key,
  firm_id uuid not null references firms(id) on delete cascade,
  run_id uuid not null references runs(id) on delete cascade,
  verdict text not null,
  gstr2b_id bigint,
  book_id bigint,
  reasons text[] not null default '{}'
);

create table agent_outputs (
  id bigserial primary key,
  firm_id uuid not null references firms(id) on delete cascade,
  run_id uuid not null references runs(id) on delete cascade,
  row_key text not null,
  agent text not null,
  output jsonb not null,
  created_at timestamptz not null default now()
);

create table reviews (
  id bigserial primary key,
  firm_id uuid not null references firms(id) on delete cascade,
  run_id uuid not null references runs(id) on delete cascade,
  row_key text not null,
  decision text not null check (decision in ('accept', 'reject')),
  note text,
  reviewer_id uuid references auth.users(id),
  created_at timestamptz not null default now()
);

create table legal_chunks (
  id bigserial primary key,
  source text not null,
  citation text not null unique,
  body text not null,
  embedding vector(768)
);

create table rate_limits (
  key text primary key,
  tokens numeric not null,
  updated_at timestamptz not null default now()
);

create table cost_ledger (
  id bigserial primary key,
  firm_id uuid not null references firms(id) on delete cascade,
  run_id uuid references runs(id) on delete cascade,
  step text not null,
  model text not null,
  input_tokens int not null,
  output_tokens int not null,
  inr numeric not null,
  at timestamptz not null default now()
);

create table audit_log (
  id bigserial primary key,
  firm_id uuid references firms(id) on delete cascade,
  actor_id uuid,
  action text not null,
  at timestamptz not null default now()
);

-- Tenant isolation: a user sees only rows of firms they belong to.
create or replace function is_member(target uuid) returns boolean
language sql stable security definer set search_path = public as $$
  select exists (
    select 1 from memberships m
    where m.firm_id = target and m.user_id = auth.uid()
  );
$$;

alter table firms enable row level security;
alter table memberships enable row level security;
alter table clients enable row level security;
alter table runs enable row level security;
alter table gstr2b_rows enable row level security;
alter table book_rows enable row level security;
alter table matches enable row level security;
alter table agent_outputs enable row level security;
alter table reviews enable row level security;
alter table cost_ledger enable row level security;
alter table audit_log enable row level security;

create policy firms_member on firms for select using (is_member(id));
create policy memberships_self on memberships for select using (user_id = auth.uid());
create policy clients_member on clients for all using (is_member(firm_id)) with check (is_member(firm_id));
create policy runs_member on runs for all using (is_member(firm_id)) with check (is_member(firm_id));
create policy gstr2b_member on gstr2b_rows for all using (is_member(firm_id)) with check (is_member(firm_id));
create policy book_member on book_rows for all using (is_member(firm_id)) with check (is_member(firm_id));
create policy matches_member on matches for all using (is_member(firm_id)) with check (is_member(firm_id));
create policy agent_member on agent_outputs for all using (is_member(firm_id)) with check (is_member(firm_id));
create policy reviews_member on reviews for all using (is_member(firm_id)) with check (is_member(firm_id));
create policy cost_member on cost_ledger for select using (is_member(firm_id));
create policy audit_member on audit_log for select using (is_member(firm_id));
-- rate_limits and legal_chunks are service-role only: RLS on, no policies for end users.
alter table rate_limits enable row level security;
alter table legal_chunks enable row level security;

-- On sign-up: create a firm and make the new user its owner.
create or replace function handle_new_user() returns trigger
language plpgsql security definer set search_path = public as $$
declare new_firm uuid;
begin
  insert into firms (name) values (coalesce(new.email, 'New firm')) returning id into new_firm;
  insert into memberships (user_id, firm_id, role) values (new.id, new_firm, 'owner');
  return new;
end;
$$;

create trigger on_auth_user_created after insert on auth.users
  for each row execute function handle_new_user();

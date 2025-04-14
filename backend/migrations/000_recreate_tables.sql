-- Drop existing tables if they exist
drop table if exists user_history;
drop table if exists policies;
drop table if exists domains;

-- Create domains table
create table domains (
    id bigint primary key generated always as identity,
    name text unique not null,
    base_url text not null,
    legal_entity_name text,
    processing_status text default 'not_processed',
    created_at timestamp with time zone default timezone('utc'::text, now()),
    updated_at timestamp with time zone default timezone('utc'::text, now()),
    policy_count integer default 0
);

-- Create policies table
create table policies (
    id bigint primary key generated always as identity,
    domain_id bigint references domains(id) on delete cascade,
    policy_type text,
    page_name text,
    page_url text,
    processing_status text default 'not_processed',
    last_updated_at timestamp with time zone default timezone('utc'::text, now()),
    checksum text,
    llm_details text,
    llm_prompt text,
    processing_output text
);

-- Create user_history table
create table user_history (
    id bigint primary key generated always as identity,
    user_id text not null,
    domain_id bigint references domains(id) on delete cascade,
    visited_at timestamp with time zone default timezone('utc'::text, now())
);

-- Create indexes for better performance
create index idx_domains_name on domains(name);
create index idx_policies_domain_id on policies(domain_id);
create index idx_policies_url on policies(page_url);
create index idx_user_history_user on user_history(user_id);

-- Enable Row Level Security (RLS)
alter table domains enable row level security;
alter table policies enable row level security;
alter table user_history enable row level security;
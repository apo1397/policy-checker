-- Enable RLS (Row Level Security)
alter table domains enable row level security;
alter table policies enable row level security;
alter table user_history enable row level security;

-- Create indexes for better performance
create index if not exists idx_domains_name on domains(name);
create index if not exists idx_policies_domain_id on policies(domain_id);
create index if not exists idx_user_history_user_id on user_history(user_id);

-- Add constraints
alter table domains
  add constraint check_processing_status 
  check (processing_status in ('not_processed', 'processing', 'processed', 'failed'));

-- Down migration (for rollback)
/* 
-- Drop indexes
drop index if exists idx_domains_name;
drop index if exists idx_policies_domain_id;
drop index if exists idx_user_history_user_id;

-- Drop constraints
alter table domains drop constraint if exists check_processing_status;

-- Disable RLS
alter table domains disable row level security;
alter table policies disable row level security;
alter table user_history disable row level security;
*/
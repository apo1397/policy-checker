-- WARNING: Only use in development
begin;
  -- Truncate all tables in correct order
  truncate table user_history cascade;
  truncate table policies cascade;
  truncate table domains cascade;
  
  -- Reset sequences
  alter sequence domains_id_seq restart with 1;
  alter sequence policies_id_seq restart with 1;
  alter sequence user_history_id_seq restart with 1;
commit;
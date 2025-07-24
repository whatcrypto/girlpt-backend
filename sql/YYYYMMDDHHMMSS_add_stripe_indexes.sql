-- Create a new migration file: supabase/migrations/YYYYMMDDHHMMSS_add_stripe_indexes.sql

-- Add index on stripe_customer_id
CREATE INDEX IF NOT EXISTS idx_users_stripe_customer_id ON public.users (stripe_customer_id)
WHERE stripe_customer_id IS NOT NULL;

-- Add index on subscription_id
CREATE INDEX IF NOT EXISTS idx_users_subscription_id ON public.users (subscription_id)
WHERE subscription_id IS NOT NULL;

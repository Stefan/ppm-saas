-- Cache-Tabelle für Help Chat Responses
CREATE TABLE IF NOT EXISTS help_chat_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cache_key VARCHAR(64) UNIQUE NOT NULL,
    query TEXT NOT NULL,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    response JSONB NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index für schnelle Cache-Lookups
CREATE INDEX IF NOT EXISTS idx_cache_key ON help_chat_cache(cache_key);
CREATE INDEX IF NOT EXISTS idx_expires_at ON help_chat_cache(expires_at);

-- RLS Policy (Row Level Security)
ALTER TABLE help_chat_cache ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can read own cache" ON help_chat_cache;
CREATE POLICY "Users can read own cache"
    ON help_chat_cache FOR SELECT
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own cache" ON help_chat_cache;
CREATE POLICY "Users can insert own cache"
    ON help_chat_cache FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Cleanup Function für abgelaufene Cache-Einträge
CREATE OR REPLACE FUNCTION cleanup_expired_cache()
RETURNS void AS $$
BEGIN
    DELETE FROM help_chat_cache
    WHERE expires_at < NOW();
END;
$$ LANGUAGE plpgsql;

-- Cron Job (Supabase pg_cron extension) - optional
-- SELECT cron.schedule(
--     'cleanup-help-chat-cache',
--     '0 * * * *',  -- Jede Stunde
--     $$SELECT cleanup_expired_cache()$$
-- );

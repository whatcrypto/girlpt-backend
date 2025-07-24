CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    clerk_user_id TEXT UNIQUE,
    stripe_customer_id TEXT,
    subscription_status TEXT DEFAULT 'inactive',
    subscription_plan TEXT,
    subscription_id TEXT,
    subscription_start_date TIMESTAMPTZ,
    subscription_end_date TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE companions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL,
    personality TEXT NOT NULL CHECK (length(personality) >= 50 AND length(personality) <= 500),
    backstory TEXT NOT NULL CHECK (length(backstory) >= 100 AND length(backstory) <= 1000),
    avatar_url TEXT NOT NULL,
    greeting_message TEXT NOT NULL CHECK (length(greeting_message) >= 10 AND length(greeting_message) <= 200),
    conversation_style VARCHAR(20) NOT NULL CHECK (conversation_style IN ('casual', 'formal', 'playful', 'mysterious', 'romantic')),
    appearance JSONB,
    occupation VARCHAR(50),
    interests TEXT[] NOT NULL,
    hobbies TEXT[],
    traits TEXT[],
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT companions_name_check CHECK (length(name) >= 3),
    CONSTRAINT companions_interests_check CHECK (array_length(interests, 1) >= 1 AND array_length(interests, 1) <= 10),
    CONSTRAINT companions_hobbies_check CHECK (array_length(hobbies, 1) <= 5),
    CONSTRAINT companions_traits_check CHECK (array_length(traits, 1) <= 8)
);
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    companion_id UUID REFERENCES companions(id) ON DELETE CASCADE,
    character_id TEXT, 
    title TEXT,
    last_message_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT chat_sessions_companion_xor_character CHECK (
        (companion_id IS NOT NULL AND character_id IS NULL) OR
        (companion_id IS NULL AND character_id IS NOT NULL)
    )
);
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT chat_messages_content_check CHECK (length(trim(content)) > 0)
);
CREATE TABLE subscription_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    stripe_event_id TEXT,
    event_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE avatar_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    companion_id UUID REFERENCES companions(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    file_size INTEGER,
    content_type TEXT,
    bucket_name TEXT DEFAULT 'avatars',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT avatar_files_size_check CHECK (file_size > 0),
    CONSTRAINT avatar_files_content_type_check CHECK (content_type IN ('image/jpeg', 'image/png', 'image/webp', 'image/gif'))
);
CREATE TABLE user_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    messages_used_today INTEGER DEFAULT 0,
    last_reset_date DATE DEFAULT CURRENT_DATE,
    total_messages_sent INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT user_usage_messages_check CHECK (messages_used_today >= 0),
    CONSTRAINT user_usage_total_check CHECK (total_messages_sent >= 0)
);
CREATE INDEX idx_users_clerk_id ON users(clerk_user_id);
CREATE INDEX idx_users_stripe_customer ON users(stripe_customer_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_companions_user_id ON companions(user_id);
CREATE INDEX idx_companions_active ON companions(user_id, is_active);
CREATE INDEX idx_companions_created ON companions(created_at DESC);
CREATE INDEX idx_companions_name_search ON companions USING gin(name gin_trgm_ops);
CREATE INDEX idx_companions_personality_search ON companions USING gin(personality gin_trgm_ops);
CREATE INDEX idx_chat_sessions_user ON chat_sessions(user_id);
CREATE INDEX idx_chat_sessions_companion ON chat_sessions(companion_id);
CREATE INDEX idx_chat_sessions_character ON chat_sessions(character_id);
CREATE INDEX idx_chat_sessions_last_message ON chat_sessions(last_message_at DESC);
CREATE INDEX idx_chat_messages_session ON chat_messages(session_id);
CREATE INDEX idx_chat_messages_created ON chat_messages(created_at);
CREATE INDEX idx_subscription_events_user ON subscription_events(user_id);
CREATE INDEX idx_subscription_events_type ON subscription_events(event_type);
CREATE INDEX idx_subscription_events_stripe ON subscription_events(stripe_event_id);
CREATE INDEX idx_avatar_files_companion ON avatar_files(companion_id);
CREATE INDEX idx_user_usage_user ON user_usage(user_id);
CREATE INDEX idx_user_usage_date ON user_usage(last_reset_date);
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';
CREATE TRIGGER update_users_updated_at BEFORE UPDATE
    ON users FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_companions_updated_at BEFORE UPDATE
    ON companions FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_chat_sessions_updated_at BEFORE UPDATE
    ON chat_sessions FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_user_usage_updated_at BEFORE UPDATE
    ON user_usage FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE companions ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscription_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE avatar_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_usage ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view own data" ON users
    FOR ALL USING (clerk_user_id = auth.jwt() ->> 'sub');
CREATE POLICY "Users can manage own companions" ON companions
    FOR ALL USING (user_id IN (
        SELECT id FROM users WHERE clerk_user_id = auth.jwt() ->> 'sub'
    ));
CREATE POLICY "Users can manage own chat sessions" ON chat_sessions
    FOR ALL USING (user_id IN (
        SELECT id FROM users WHERE clerk_user_id = auth.jwt() ->> 'sub'
    ));
CREATE POLICY "Users can access own chat messages" ON chat_messages
    FOR ALL USING (session_id IN (
        SELECT cs.id FROM chat_sessions cs
        JOIN users u ON cs.user_id = u.id
        WHERE u.clerk_user_id = auth.jwt() ->> 'sub'
    ));
CREATE POLICY "Users can view own subscription events" ON subscription_events
    FOR ALL USING (user_id IN (
        SELECT id FROM users WHERE clerk_user_id = auth.jwt() ->> 'sub'
    ));
CREATE POLICY "Users can manage own avatar files" ON avatar_files
    FOR ALL USING (companion_id IN (
        SELECT c.id FROM companions c
        JOIN users u ON c.user_id = u.id
        WHERE u.clerk_user_id = auth.jwt() ->> 'sub'
    ));
CREATE POLICY "Users can view own usage data" ON user_usage
    FOR ALL USING (user_id IN (
        SELECT id FROM users WHERE clerk_user_id = auth.jwt() ->> 'sub'
    ));
CREATE OR REPLACE FUNCTION get_user_by_clerk_id(clerk_id TEXT)
RETURNS users AS $$
DECLARE
    user_record users%ROWTYPE;
BEGIN
    SELECT * INTO user_record FROM users WHERE clerk_user_id = clerk_id;
    RETURN user_record;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
CREATE OR REPLACE FUNCTION update_user_message_count(p_user_id UUID)
RETURNS VOID AS $$
BEGIN
    INSERT INTO user_usage (user_id, messages_used_today, total_messages_sent)
    VALUES (p_user_id, 1, 1)
    ON CONFLICT (user_id) DO UPDATE SET
        messages_used_today = CASE
            WHEN user_usage.last_reset_date < CURRENT_DATE THEN 1
            ELSE user_usage.messages_used_today + 1
        END,
        total_messages_sent = user_usage.total_messages_sent + 1,
        last_reset_date = CURRENT_DATE,
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
CREATE VIEW user_companion_stats AS
SELECT
    u.id as user_id,
    u.email,
    u.clerk_user_id,
    COUNT(c.id) as total_companions,
    COUNT(CASE WHEN c.is_active THEN 1 END) as active_companions,
    MAX(c.created_at) as last_companion_created
FROM users u
LEFT JOIN companions c ON u.id = c.user_id
GROUP BY u.id, u.email, u.clerk_user_id;
CREATE VIEW recent_chat_activity AS
SELECT
    cs.id as session_id,
    cs.user_id,
    cs.companion_id,
    cs.character_id,
    cs.title,
    cs.last_message_at,
    COUNT(cm.id) as message_count,
    MAX(cm.created_at) as last_message_time
FROM chat_sessions cs
LEFT JOIN chat_messages cm ON cs.id = cm.session_id
GROUP BY cs.id, cs.user_id, cs.companion_id, cs.character_id, cs.title, cs.last_message_at
ORDER BY cs.last_message_at DESC;

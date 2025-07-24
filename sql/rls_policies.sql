ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE characters ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscription_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_usage ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can read own data" ON users
    FOR SELECT USING (
        id = auth.uid()::text::uuid OR
        clerk_user_id = auth.jwt()->>'sub' OR
        email = auth.jwt()->>'email'
    );
CREATE POLICY "Users can update own data" ON users
    FOR UPDATE USING (
        id = auth.uid()::text::uuid OR
        clerk_user_id = auth.jwt()->>'sub' OR
        email = auth.jwt()->>'email'
    );
CREATE POLICY "Service role full access to users" ON users
    FOR ALL USING (
        auth.jwt()->>'role' = 'service_role' OR
        auth.role() = 'service_role'
    );
CREATE POLICY "Authenticated users can create accounts" ON users
    FOR INSERT WITH CHECK (
        auth.role() = 'authenticated' OR
        auth.jwt()->>'role' = 'service_role'
    );
CREATE POLICY "Users can read own characters" ON characters
    FOR SELECT USING (
        user_id IN (
            SELECT id FROM users WHERE
            id = auth.uid()::text::uuid OR
            clerk_user_id = auth.jwt()->>'sub' OR
            email = auth.jwt()->>'email'
        )
    );
CREATE POLICY "Users can create own characters" ON characters
    FOR INSERT WITH CHECK (
        user_id IN (
            SELECT id FROM users WHERE
            id = auth.uid()::text::uuid OR
            clerk_user_id = auth.jwt()->>'sub' OR
            email = auth.jwt()->>'email'
        )
    );
CREATE POLICY "Users can update own characters" ON characters
    FOR UPDATE USING (
        user_id IN (
            SELECT id FROM users WHERE
            id = auth.uid()::text::uuid OR
            clerk_user_id = auth.jwt()->>'sub' OR
            email = auth.jwt()->>'email'
        )
    );
CREATE POLICY "Users can delete own characters" ON characters
    FOR DELETE USING (
        user_id IN (
            SELECT id FROM users WHERE
            id = auth.uid()::text::uuid OR
            clerk_user_id = auth.jwt()->>'sub' OR
            email = auth.jwt()->>'email'
        )
    );
CREATE POLICY "Service role full access to characters" ON characters
    FOR ALL USING (
        auth.jwt()->>'role' = 'service_role' OR
        auth.role() = 'service_role'
    );
CREATE POLICY "Users can read own chat sessions" ON chat_sessions
    FOR SELECT USING (
        user_id IN (
            SELECT id FROM users WHERE
            id = auth.uid()::text::uuid OR
            clerk_user_id = auth.jwt()->>'sub' OR
            email = auth.jwt()->>'email'
        )
    );
CREATE POLICY "Users can create own chat sessions" ON chat_sessions
    FOR INSERT WITH CHECK (
        user_id IN (
            SELECT id FROM users WHERE
            id = auth.uid()::text::uuid OR
            clerk_user_id = auth.jwt()->>'sub' OR
            email = auth.jwt()->>'email'
        )
    );
CREATE POLICY "Users can update own chat sessions" ON chat_sessions
    FOR UPDATE USING (
        user_id IN (
            SELECT id FROM users WHERE
            id = auth.uid()::text::uuid OR
            clerk_user_id = auth.jwt()->>'sub' OR
            email = auth.jwt()->>'email'
        )
    );
CREATE POLICY "Users can delete own chat sessions" ON chat_sessions
    FOR DELETE USING (
        user_id IN (
            SELECT id FROM users WHERE
            id = auth.uid()::text::uuid OR
            clerk_user_id = auth.jwt()->>'sub' OR
            email = auth.jwt()->>'email'
        )
    );
CREATE POLICY "Service role full access to chat sessions" ON chat_sessions
    FOR ALL USING (
        auth.jwt()->>'role' = 'service_role' OR
        auth.role() = 'service_role'
    );
CREATE POLICY "Users can read own chat messages" ON chat_messages
    FOR SELECT USING (
        session_id IN (
            SELECT id FROM chat_sessions WHERE user_id IN (
                SELECT id FROM users WHERE
                id = auth.uid()::text::uuid OR
                clerk_user_id = auth.jwt()->>'sub' OR
                email = auth.jwt()->>'email'
            )
        )
    );
CREATE POLICY "Users can create messages in own sessions" ON chat_messages
    FOR INSERT WITH CHECK (
        session_id IN (
            SELECT id FROM chat_sessions WHERE user_id IN (
                SELECT id FROM users WHERE
                id = auth.uid()::text::uuid OR
                clerk_user_id = auth.jwt()->>'sub' OR
                email = auth.jwt()->>'email'
            )
        )
    );
CREATE POLICY "Users can update own chat messages" ON chat_messages
    FOR UPDATE USING (
        session_id IN (
            SELECT id FROM chat_sessions WHERE user_id IN (
                SELECT id FROM users WHERE
                id = auth.uid()::text::uuid OR
                clerk_user_id = auth.jwt()->>'sub' OR
                email = auth.jwt()->>'email'
            )
        )
    );
CREATE POLICY "Users can delete own chat messages" ON chat_messages
    FOR DELETE USING (
        session_id IN (
            SELECT id FROM chat_sessions WHERE user_id IN (
                SELECT id FROM users WHERE
                id = auth.uid()::text::uuid OR
                clerk_user_id = auth.jwt()->>'sub' OR
                email = auth.jwt()->>'email'
            )
        )
    );
CREATE POLICY "Service role full access to chat messages" ON chat_messages
    FOR ALL USING (
        auth.jwt()->>'role' = 'service_role' OR
        auth.role() = 'service_role'
    );
CREATE POLICY "Users can read own subscription events" ON subscription_events
    FOR SELECT USING (
        user_id IN (
            SELECT id FROM users WHERE
            id = auth.uid()::text::uuid OR
            clerk_user_id = auth.jwt()->>'sub' OR
            email = auth.jwt()->>'email'
        )
    );
CREATE POLICY "Service role can create subscription events" ON subscription_events
    FOR INSERT WITH CHECK (
        auth.jwt()->>'role' = 'service_role' OR
        auth.role() = 'service_role'
    );
CREATE POLICY "Service role full access to subscription events" ON subscription_events
    FOR ALL USING (
        auth.jwt()->>'role' = 'service_role' OR
        auth.role() = 'service_role'
    );
CREATE POLICY "Users can read own usage data" ON user_usage
    FOR SELECT USING (
        user_id IN (
            SELECT id FROM users WHERE
            id = auth.uid()::text::uuid OR
            clerk_user_id = auth.jwt()->>'sub' OR
            email = auth.jwt()->>'email'
        )
    );
CREATE POLICY "Users can update own usage data" ON user_usage
    FOR UPDATE USING (
        user_id IN (
            SELECT id FROM users WHERE
            id = auth.uid()::text::uuid OR
            clerk_user_id = auth.jwt()->>'sub' OR
            email = auth.jwt()->>'email'
        )
    );
CREATE POLICY "Service role can create usage records" ON user_usage
    FOR INSERT WITH CHECK (
        auth.jwt()->>'role' = 'service_role' OR
        auth.role() = 'service_role'
    );
CREATE POLICY "Service role full access to user usage" ON user_usage
    FOR ALL USING (
        auth.jwt()->>'role' = 'service_role' OR
        auth.role() = 'service_role'
    );
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'companion-avatars',
    'companion-avatars',
    true,
    52428800,
    ARRAY['image/jpeg', 'image/png', 'image/gif', 'image/webp']
) ON CONFLICT (id) DO NOTHING;
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'character-images',
    'character-images',
    true,
    26214400,
    ARRAY['image/jpeg', 'image/png', 'image/gif', 'image/webp']
) ON CONFLICT (id) DO NOTHING;
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'generated-content',
    'generated-content',
    true,
    52428800,
    ARRAY['image/jpeg', 'image/png', 'image/gif', 'image/webp']
) ON CONFLICT (id) DO NOTHING;
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'chat-attachments',
    'chat-attachments',
    true,
    104857600,
    ARRAY['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'application/pdf', 'text/plain']
) ON CONFLICT (id) DO NOTHING;
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'user-uploads',
    'user-uploads',
    true,
    104857600,
    ARRAY['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'application/pdf', 'text/plain']
) ON CONFLICT (id) DO NOTHING;
CREATE POLICY "Users can upload files to own folder" ON storage.objects
    FOR INSERT WITH CHECK (
        bucket_id IN ('companion-avatars', 'chat-attachments', 'user-uploads') AND
        auth.role() = 'authenticated' AND
        (
            name LIKE auth.jwt()->>'sub' || '/%' OR
            name LIKE (auth.jwt()->>'email') || '/%' OR
            auth.jwt()->>'role' = 'service_role'
        )
    );
CREATE POLICY "Users can read own files and public files" ON storage.objects
    FOR SELECT USING (
        bucket_id IN ('companion-avatars', 'character-images', 'generated-content', 'chat-attachments', 'user-uploads') AND
        (
            name LIKE auth.jwt()->>'sub' || '/%' OR
            name LIKE (auth.jwt()->>'email') || '/%' OR
            bucket_id IN ('character-images', 'generated-content') OR
            auth.jwt()->>'role' = 'service_role'
        )
    );
CREATE POLICY "Users can update own files" ON storage.objects
    FOR UPDATE USING (
        bucket_id IN ('companion-avatars', 'chat-attachments', 'user-uploads') AND
        (
            name LIKE auth.jwt()->>'sub' || '/%' OR
            name LIKE (auth.jwt()->>'email') || '/%' OR
            auth.jwt()->>'role' = 'service_role'
        )
    );
CREATE POLICY "Users can delete own files" ON storage.objects
    FOR DELETE USING (
        bucket_id IN ('companion-avatars', 'chat-attachments', 'user-uploads') AND
        (
            name LIKE auth.jwt()->>'sub' || '/%' OR
            name LIKE (auth.jwt()->>'email') || '/%' OR
            auth.jwt()->>'role' = 'service_role'
        )
    );
CREATE POLICY "Service role full access to storage" ON storage.objects
    FOR ALL USING (
        auth.jwt()->>'role' = 'service_role' OR
        auth.role() = 'service_role'
    );
CREATE OR REPLACE FUNCTION user_owns_companion(companion_uuid UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM characters c
        JOIN users u ON c.user_id = u.id
        WHERE c.id = companion_uuid
        AND (
            u.id = auth.uid()::text::uuid OR
            u.clerk_user_id = auth.jwt()->>'sub' OR
            u.email = auth.jwt()->>'email'
        )
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
CREATE OR REPLACE FUNCTION user_owns_chat_session(session_uuid UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM chat_sessions cs
        JOIN users u ON cs.user_id = u.id
        WHERE cs.id = session_uuid
        AND (
            u.id = auth.uid()::text::uuid OR
            u.clerk_user_id = auth.jwt()->>'sub' OR
            u.email = auth.jwt()->>'email'
        )
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
CREATE OR REPLACE FUNCTION get_current_user_id()
RETURNS UUID AS $$
DECLARE
    user_uuid UUID;
BEGIN
    user_uuid := auth.uid()::text::uuid;
    IF user_uuid IS NOT NULL THEN
        RETURN user_uuid;
    END IF;
    SELECT id INTO user_uuid
    FROM users
    WHERE clerk_user_id = auth.jwt()->>'sub'
    LIMIT 1;
    IF user_uuid IS NOT NULL THEN
        RETURN user_uuid;
    END IF;
    SELECT id INTO user_uuid
    FROM users
    WHERE email = auth.jwt()->>'email'
    LIMIT 1;
    RETURN user_uuid;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_name TEXT NOT NULL,
    operation TEXT NOT NULL,
    record_id UUID,
    old_values JSONB,
    new_values JSONB,
    user_id UUID,
    user_email TEXT,
    clerk_user_id TEXT,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Service role can read audit logs" ON audit_logs
    FOR SELECT USING (
        auth.jwt()->>'role' = 'service_role' OR
        auth.role() = 'service_role'
    );
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_logs (
        table_name,
        operation,
        record_id,
        old_values,
        new_values,
        user_id,
        user_email,
        clerk_user_id,
        ip_address,
        user_agent
    ) VALUES (
        TG_TABLE_NAME,
        TG_OP,
        COALESCE(NEW.id, OLD.id),
        CASE WHEN TG_OP = 'DELETE' THEN to_jsonb(OLD) ELSE NULL END,
        CASE WHEN TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN to_jsonb(NEW) ELSE NULL END,
        get_current_user_id(),
        auth.jwt()->>'email',
        auth.jwt()->>'sub',
        inet_client_addr(),
        current_setting('request.headers', true)::json->>'user-agent'
    );
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
CREATE TRIGGER audit_users_trigger
    AFTER INSERT OR UPDATE OR DELETE ON users
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
CREATE TRIGGER audit_characters_trigger
    AFTER INSERT OR UPDATE OR DELETE ON characters
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
CREATE TRIGGER audit_subscription_events_trigger
    AFTER INSERT OR UPDATE OR DELETE ON subscription_events
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
CREATE INDEX IF NOT EXISTS idx_users_clerk_user_id ON users(clerk_user_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_characters_user_id ON characters(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_subscription_events_user_id ON subscription_events(user_id);
CREATE INDEX IF NOT EXISTS idx_user_usage_user_id ON user_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_characters_user_active ON characters(user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_archived ON chat_sessions(user_id, is_archived);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_deleted ON chat_messages(session_id, is_deleted);
COMMENT ON TABLE users IS 'User accounts with subscription information';
COMMENT ON TABLE characters IS 'User-created AI characters with personality and appearance';
COMMENT ON TABLE chat_sessions IS 'Chat sessions between users and characters/characters';
COMMENT ON TABLE chat_messages IS 'Individual messages within chat sessions';
COMMENT ON TABLE subscription_events IS 'Audit trail for subscription changes from Stripe';
COMMENT ON TABLE user_usage IS 'Daily usage tracking for message limits';
COMMENT ON TABLE audit_logs IS 'Audit trail for sensitive operations';
COMMENT ON FUNCTION get_current_user_id() IS 'Get current user UUID from various auth methods';
COMMENT ON FUNCTION user_owns_companion(UUID) IS 'Check if current user owns a specific companion';
COMMENT ON FUNCTION user_owns_chat_session(UUID) IS 'Check if current user owns a specific chat session';

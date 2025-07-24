
CREATE TABLE Characters (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255),
  age INT,
  sexual_archetype TEXT,
  seduction_style TEXT,
  intimate_personality TEXT,
  emotional_availability TEXT,
  fantasy_role VARCHAR(255),
  conversation_approach TEXT,
  physical_traits TEXT,
  backstory_hook TEXT,
  image_filename VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Character_Tags (
  id SERIAL PRIMARY KEY,
  character_id INTEGER REFERENCES Characters(id),
  tag_name VARCHAR(255),
  tag_category TEXT
);

CREATE TABLE User_Preferences (
  id SERIAL PRIMARY KEY,
  user_id INTEGER, -- Assuming references a users table
  preferred_archetype VARCHAR(255),
  preferred_tags JSON,
  age_preference_min INT,
  age_preference_max INT,
  fantasy_categories JSON
);

CREATE TABLE Chat_Sessions (
  id SERIAL PRIMARY KEY,
  user_id INTEGER, -- Assuming references a users table
  character_id INTEGER REFERENCES Characters(id),
  session_start TIMESTAMP,
  session_end TIMESTAMP,
  message_count INT,
  engagement_score DECIMAL,
  nsfw_level TEXT
);

CREATE TABLE Character_Analytics (
  id SERIAL PRIMARY KEY,
  character_id INTEGER REFERENCES Characters(id),
  total_chats INT,
  avg_session_length DECIMAL,
  user_rating DECIMAL,
  popularity_score DECIMAL,
  conversion_rate DECIMAL,
  last_updated TIMESTAMP
);

sk_aui_proj_0b8hhuf9gxsm_0P6lMJTb6ZN94Qdd6KU07Y2Q2luSYJsq
cloud.assistant-ui.com/girlfriendpt/
sk_aui_proj_0b8hhuf9gxsm_0P6lMJTb6ZN94Qdd6KU07Y2Q2luSYJsq
cloud.assistant-ui.com/girlfriendpt/
-- Character Interaction Logs
CREATE TABLE Character_Interactions (
  id SERIAL PRIMARY KEY,
  user_id INTEGER,
  character_id INTEGER REFERENCES Characters(id),
  interaction_type VARCHAR(50), -- 'message', 'like', 'favorite', 'share'
  interaction_data JSON,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Character Personality Traits
CREATE TABLE Character_Personality_Traits (
  id SERIAL PRIMARY KEY,
  character_id INTEGER REFERENCES Characters(id),
  trait_name VARCHAR(100),
  trait_value DECIMAL(3,2), -- 0.00 to 1.00 scale
  trait_category VARCHAR(50) -- 'dominant', 'submissive', 'playful', 'serious', etc.
);

-- Character Dialogue Templates
CREATE TABLE Character_Dialogue_Templates (
  id SERIAL PRIMARY KEY,
  character_id INTEGER REFERENCES Characters(id),
  scenario_type VARCHAR(100),
  template_text TEXT,
  mood_context VARCHAR(50),
  nsfw_level VARCHAR(20)
);

-- Character Customization Options
CREATE TABLE Character_Customization_Options (
  id SERIAL PRIMARY KEY,
  character_id INTEGER REFERENCES Characters(id),
  option_type VARCHAR(50), -- 'outfit', 'hair', 'expression', 'pose'
  option_name VARCHAR(100),
  option_data JSON,
  unlock_requirement VARCHAR(100)
);

-- Character Usage Analytics
CREATE TABLE Character_Usage_Analytics (
  id SERIAL PRIMARY KEY,
  character_id INTEGER REFERENCES Characters(id),
  date DATE,
  total_interactions INTEGER DEFAULT 0,
  unique_users INTEGER DEFAULT 0,
  avg_session_duration DECIMAL,
  retention_rate DECIMAL
);

-- Character Content Moderation
CREATE TABLE Character_Content_Moderation (
  id SERIAL PRIMARY KEY,
  character_id INTEGER REFERENCES Characters(id),
  content_type VARCHAR(50), -- 'dialogue', 'description', 'image'
  moderation_status VARCHAR(20), -- 'approved', 'flagged', 'rejected'
  moderator_notes TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


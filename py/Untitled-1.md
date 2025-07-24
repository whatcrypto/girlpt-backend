# 🔐 GirlfriendPT Backend Architecture - Comprehensive Flow Tree


```
 backend/

├─ main.py (FastAPI Application Entry Point)
│  

 ├── Initialization Layer

│   │   ├──  FastAPI App Creation
│   │   │   ├── Title: "GirlfriendPT AI Backend"
│   │   │   ├── Description: "Backend API for AI companion chat application"
│   │   │   └── Version: "1.0.0"

│   │   ├──  CORS Configuration
│   │   │   ├── Origins: ["https://girlfriendpt.com"]
│   │   │   ├── Credentials: true
│   │   │   ├── Methods: ["*"]
│   │   │   └── Headers: ["*"]

│   │   ├──  Authentication Setup
│   │   │   ├── JWTBearer() Instance
│   │   │   └── API_KEY Verification

│   │   ├──  Stripe Integration
│   │   │   └── stripe.api_key Configuration
│   │   └──  Database Dependency Injection
│   │       └── get_db() → SupabaseOperations()
│   │

│   ├── 📋 Pydantic Models (Request/Response Schemas)
│   │   ├── 💬 Chat Models
│   │   │   ├── Message (role, content)
│   │   │   ├── ChatRequest (messages, temperature, max_tokens, user_email, companion_id, personality, backstory, conversation_style, greeting_message, character_id, character_name, character_description)
│   │   │   └── ChatResponse (content, role, usage)
│   │   ├── 👥 User Models
│   │   │   ├── UserCreate (email, clerk_user_id, stripe_customer_id)
│   │   │   └── UserUpdate (email, other_fields)
│   │   ├──  Companion Models
│   │   │   ├── CompanionCreate (name, personality, backstory, avatar_url, greeting_message, interests, conversation_style, appearance, occupation, hobbies, traits, user_id)
│   │   │   ├── CompanionFilters (user_id, search)
│   │   │   └── CompanionUpdate (name, personality, other_fields)
│   │   └── 🎨 Image Generation Models
│   │       └── ImageGenerationRequest (prompt, style, size)
│   │
│   ├── 🛣️ API Endpoints (RESTful Routes)
│   │   ├── 🏥 Health & Status
│   │   │   ├── GET / → Root status
│   │   │   └── GET /health → Health check
│   │   │
│   │   ├── 🤖 Character/Companion Management
│   │   │   ├── POST /api/characters → Create companion
│   │   │   │   ├──  JWT Authentication Required
│   │   │   │   ├──  User Authorization Check
│   │   │   │   ├── 🗄️ Database Operation: create_companion()
│   │   │   │   └── 📤 Response: Created companion data
│   │   │   ├── GET /api/characters → List companions
│   │   │   │   ├──  JWT Authentication Required
│   │   │   │   ├── 🔍 Optional Search Filtering
│   │   │   │   ├── 🗄️ Database Operation: get_characters_by_user()
│   │   │   │   └── 📤 Response: List of companions
│   │   │   ├── GET /api/characters/{companion_id} → Get single companion
│   │   │   │   ├──  JWT Authentication Required
│   │   │   │   ├── 🗄️ Database Operation: get_companion()
│   │   │   │   └── 📤 Response: Companion details
│   │   │   ├── PUT /api/characters/{companion_id} → Update companion
│   │   │   │   ├──  JWT Authentication Required
│   │   │   │   ├── 🗄️ Database Operation: update_companion()
│   │   │   │   └── 📤 Response: Updated companion data
│   │   │   └── DELETE /api/characters/{companion_id} → Delete companion
│   │   │       ├──  JWT Authentication Required
│   │   │       ├── 🗄️ Database Operation: delete_companion()
│   │   │       └── 📤 Response: Success confirmation
│   │   │
│   │   ├── 💬 Chat System
│   │   │   └── POST /api/chat → AI Chat Processing
│   │   │       ├──  JWT Authentication Required
│   │   │       ├── 🧠 System Message Building
│   │   │       │   ├── 📋 _build_system_message()
│   │   │       │   ├── 🤖 Companion-based: name, personality, backstory, traits, conversation_style
│   │   │       │   ├── 🎭 Character-based: name, intimate_personality, backstory_hook, traits_json
│   │   │       │   └── 🎯 Default: "You are a helpful AI"
│   │   │       ├── 🌐 OpenRouter API Integration
│   │   │       │   ├── Model: "cognitivecomputations/dolphin-mistral-24b-venice-edition:free"
│   │   │       │   ├── Headers: Authorization, Content-Type, HTTP-Referer, X-Title
│   │   │       │   ├── Parameters: messages, temperature, max_tokens, stream
│   │   │       │   └── Response Processing
│   │   │       ├──  Usage Tracking
│   │   │       │   ├── prompt_tokens
│   │   │       │   ├── completion_tokens
│   │   │       │   └── total_tokens
│   │   │       └── 📤 Response: AI-generated content + usage stats
│   │   │
│   │   ├── 👥 User Management
│   │   │   ├── POST /api/users → Create user
│   │   │   │   ├──  JWT Authentication Required
│   │   │   │   ├── 🗄️ Database Operation: create_or_update_user()
│   │   │   │   └── 📤 Response: Created user data
│   │   │   ├── GET /api/users/{user_id} → Get user
│   │   │   │   ├──  JWT Authentication Required
│   │   │   │   ├── 🗄️ Database Operation: get_user_by_clerk_id()
│   │   │   │   └── 📤 Response: User details
│   │   │   └── PUT /api/users/{user_id} → Update user
│   │   │       ├──  JWT Authentication Required
│   │   │       ├── 🗄️ Database Operation: create_or_update_user()
│   │   │       └── 📤 Response: Updated user data
│   │   │
│   │   ├──  Image Generation
│   │   │   └── POST /api/generate-image → AI Image Generation
│   │   │       ├──  JWT Authentication Required
│   │   │       ├── 🤖 HuggingFace InferenceClient
│   │   │       │   ├── Model: "stabilityai/stable-diffusion-2-1"
│   │   │       │   ├── Enhanced Prompt: "{prompt}, in {style} style, high quality, detailed"
│   │   │       │   ├── Parameters: height, width, num_inference_steps, guidance_scale
│   │   │       │   └── Image Processing
│   │   │       ├── 🔄 Base64 Encoding
│   │   │       └── 📤 Response: Base64 encoded image
│   │   │
│   │   └── 💳 Stripe Webhook Processing
│   │       └── POST /api/stripe/webhook → Subscription Management
│   │           ├── 🔐 Stripe Signature Verification
│   │           ├──  Event Processing
│   │           │   ├── customer.subscription.created
│   │           │   │   ├── Plan Mapping (price_id → plan_name)
│   │           │   │   ├── 🗄️ Database Operation: Update user subscription
│   │           │   │   └── Fields: stripe_customer_id, subscription_id, subscription_plan, subscription_status, subscription_start_date, subscription_end_date
│   │           │   ├── customer.subscription.updated
│   │           │   │   ├── Same as created
│   │           │   │   └── 🗄️ Database Operation: Update user subscription
│   │           │   └── customer.subscription.deleted
│   │           │       ├── 🗄️ Database Operation: Update subscription status to 'canceled'
│   │           │       └── Fields: subscription_status, subscription_end_date
│   │           └──  Response: Success/error status
│   │
│   └── 🚀 Application Startup
│       ├── Port Configuration (default: 8000)
│       ├── Host Configuration (default: "0.0.0.0")
│       └── Uvicorn Server Launch
│
├── 📦 py/ (Python Package)
│   ├── 🏷️ __init__.py (Package Initialization)
│   │   ├──  Version: "1.0.0"
│   │   ├── 👥 Author: "GirlfriendPT Team"
│   │   ├──  Module Exports
│   │   │   ├── get_supabase_config
│   │   │   ├── SupabaseConfig
│   │   │   ├── SupabaseOperations
│   │   │   ├── JWTBearer
│   │   │   ├── get_current_user
│   │   │   ├── get_database
│   │   │   └── init_database
│   │   └──  Public API Surface
│   │
│   ├──  auth_middleware.py (JWT Authentication System)
│   │   ├── 🔑 JWTBearer Class (HTTPBearer Extension)
│   │   │   ├── ️ Constructor
│   │   │   │   └── auto_error Parameter
│   │   │   ├── 🔄 __call__ Method (Async Request Processing)
│   │   │   │   ├── 📋 Credential Extraction
│   │   │   │   │   ├── HTTPAuthorizationCredentials Validation
│   │   │   │   │   ├── Bearer Scheme Verification
│   │   │   │   │   └── Token Extraction
│   │   │   │   ├── 🔐 JWT Token Verification
│   │   │   │   │   ├── 🌐 Supabase JWKS Fetch
│   │   │   │   │   │   ├── URL: {SUPABASE_URL}/auth/v1/.well-known/jwks.json
│   │   │   │   │   │   └── JSON Web Key Set Retrieval
│   │   │   │   │   ├──  RSA Key Matching
│   │   │   │   │   │   ├── Token Header Extraction (kid)
│   │   │   │   │   │   ├── JWKS Key Search Loop
│   │   │   │   │   │   ├── Key Properties: kty, kid, use, n, e
│   │   │   │   │   │   └── Key ID Matching
│   │   │   │   │   ├── 🎯 JWT Payload Decoding
│   │   │   │   │   │   ├── Algorithm: RS256
│   │   │   │   │   │   ├── Audience: "authenticated"
│   │   │   │   │   │   ├── Issuer: {SUPABASE_URL}/auth/v1
│   │   │   │   │   │   └── Payload Extraction
│   │   │   │   │   └── 👤 User State Assignment
│   │   │   │   │       ├── request.state.user Creation
│   │   │   │   │       ├── Fields: id (sub), email, role
│   │   │   │   │       └── User Object Return
│   │   │   │   └── ❌ Error Handling
│   │   │   │       ├── Invalid Credentials (401)
│   │   │   │       ├── Invalid Scheme (403)
│   │   │   │       ├── Missing Key (401)
│   │   │   │       └── JWT Error (403)
│   │   │   └── 🔄 Request Flow Integration
│   │   │
│   │   └── 👤 get_current_user Function (Dependency Injection)
│   │       ├── 📋 Request State Validation
│   │       ├──  User Object Retrieval
│   │       └── ❌ Authentication Error Handling (401)
│   │
│   ├── 🔗 compatibility_layer.py (Legacy Interface Adapter)
│   │   ├── 🏗️ Global Database Instance Management
│   │   │   ├── _db_instance Variable
│   │   │   ├── get_database() Function
│   │   │   │   ├── Singleton Pattern Implementation
│   │   │   │   ├── SupabaseOperations Instantiation
│   │   │   │   └── Global Instance Return
│   │   │   └──  Async-Sync Bridge
│   │   │       ├── _run_async() Function
│   │   │       │   ├── Event Loop Detection
│   │   │       │   ├── ThreadPoolExecutor Fallback
│   │   │       │   ├── asyncio.run() Fallback
│   │   │       │   └── Exception Handling
│   │   │
│   │   ├── 👥 User Management Functions (Sync Wrappers)
│   │   │   ├── get_user_by_email(email: str) → Optional[Dict]
│   │   │   │   └── 🗄️ Database Operation: get_user_by_email()
│   │   │   ├── get_user_by_clerk_id(clerk_user_id: str) → Optional[Dict]
│   │   │   │   └── 🗄️ Database Operation: get_user_by_clerk_id()
│   │   │   ├── get_user_by_stripe_customer_id(customer_id: str) → Optional[Dict]
│   │   │   │   └── 🗄️ Database Operation: get_user_by_stripe_customer_id()
│   │   │   ├── create_or_update_user(email, clerk_user_id, stripe_customer_id, **additional_fields) → Optional[Dict]
│   │   │   │   └── 🗄️ Database Operation: create_or_update_user()
│   │   │   ├── update_subscription(customer_id, subscription_id, status, plan, start_date, end_date) → bool
│   │   │   │   └── 🗄️ Database Operation: update_subscription()
│   │   │   ├── get_user_subscription(email: str) → Optional[Dict]
│   │   │   │   └── 🗄️ Database Operation: get_user_subscription()
│   │   │   ├── is_user_premium(email: str) → bool
│   │   │   │   └── 🗄️ Database Operation: is_user_premium()
│   │   │   └── log_subscription_event(customer_id, event_type, stripe_event_id, event_data) → bool
│   │   │       └── 🗄️ Database Operation: log_subscription_event()
│   │   │
│   │   ├── 🤖 Companion Management Functions (Sync Wrappers)
│   │   │   ├── save_companion(companion_data: Dict) → Optional[Dict]
│   │   │   │   └── 🗄️ Database Operation: save_companion()
│   │   │   ├── get_companions_by_user(user_id: str) → List[Dict]
│   │   │   │   └── 🗄️ Database Operation: get_companions_by_user()
│   │   │   ├── get_companion(companion_id: str, user_id: str) → Optional[Dict]
│   │   │   │   └── 🗄️ Database Operation: get_companion()
│   │   │   ├── update_companion(companion_id, user_id, updates) → Optional[Dict]
│   │   │   │   └── 🗄️ Database Operation: update_companion()
│   │   │   ├── delete_companion(companion_id: str, user_id: str) → bool
│   │   │   │   └── 🗄️ Database Operation: delete_companion()
│   │   │   ├── get_companion_count(user_id: str) → int
│   │   │   │   └── 🗄️ Database Operation: get_companion_count()
│   │   │   └── search_companions(user_id: str, query: str) → List[Dict]
│   │   │       └── 🗄️ Database Operation: search_companions()
│   │   │
│   │   ├── 💬 Chat System Functions (Sync Wrappers)
│   │   │   ├── create_chat_session(user_id, companion_id, character_id, title) → Optional[Dict]
│   │   │   │   └── 🗄️ Database Operation: create_chat_session()
│   │   │   ├── add_chat_message(session_id, role, content, metadata) → Optional[Dict]
│   │   │   │   └── 🗄️ Database Operation: add_chat_message()
│   │   │   ├── get_chat_sessions(user_id, limit) → List[Dict]
│   │   │   │   └── 🗄️ Database Operation: get_chat_sessions()
│   │   │   ├── get_chat_messages(session_id, limit) → List[Dict]
│   │   │   │   └── 🗄️ Database Operation: get_chat_messages()
│   │   │   ├── update_user_message_count(user_id: str) → bool
│   │   │   │   └── 🗄️ Database Operation: update_user_message_count()
│   │   │   ├── get_user_usage(user_id: str) → Dict
│   │   │   │   └── 🗄️ Database Operation: get_user_usage()
│   │   │   └── reset_daily_message_count(user_id: str) → bool
│   │   │       └── 🗄️ Database Operation: reset_daily_message_count()
│   │   │
│   │   └── 🔧 Legacy Interface Functions
│   │       ├── init_database() → bool
│   │       │   ├── SupabaseOperations Initialization
│   │       │   ├── Client Configuration
│   │       │   └── Success/Failure Status
│   │       ├── connect_db() → Legacy Alias
│   │       │   └── Calls init_database()
│   │       ├── close_db() → No-op
│   │       └── db → Global Database Instance
│   │
│   ├── ⚙️ supabase_config.py (Database Configuration & Connection Management)
│   │   ├── 🏗️ SupabaseConfig Class (Centralized Configuration)
│   │   │   ├── 🔧 Constructor & Environment Variables
│   │   │   │   ├── SUPABASE_URL
│   │   │   │   ├── SUPABASE_KEY (anon)
│   │   │   │   ├── SUPABASE_SERVICE_KEY
│   │   │   │   ├── DATABASE_URL
│   │   │   │   ├── DATABASE_URL (non-pooling)
│   │   │   │   └── Configuration Validation
│   │   │   │       ├── Required Variables Check
│   │   │   │       ├── Missing Variables Detection
│   │   │   │       └── ValueError on Missing Config
│   │   │   │
│   │   │   ├── 🔌 Client Initialization (initialize_clients)
│   │   │   │   ├── 🔐 Supabase Client (Anonymous)
│   │   │   │   │   ├── URL: supabase_url
│   │   │   │   │   └── Key: supabase_anon_key
│   │   │   │   ├── 🔑 Supabase Service Client (Admin)
│   │   │   │   │   ├── URL: supabase_url
│   │   │   │   │   └── Key: supabase_service_role_key
│   │   │   │   ├── ️ SQLAlchemy Engine (Sync)
│   │   │   │   │   ├── URL: postgres_url
│   │   │   │   │   ├── Pool Size: 20
│   │   │   │   │   ├── Max Overflow: 0
│   │   │   │   │   ├── Pool Pre-ping: true
│   │   │   │   │   └── Echo: false
│   │   │   │   └── 🗄️ SQLAlchemy Async Engine
│   │   │   │       ├── URL: postgresql+asyncpg://
│   │   │   │       ├── Pool Size: 20
│   │   │   │       ├── Max Overflow: 0
│   │   │   │       ├── Pool Pre-ping: true
│   │   │   │       └── Echo: false
│   │   │   │
│   │   │   ├──  Connection Testing (test_connection)
│   │   │   │   ├── Simple Query: "SELECT 1"
│   │   │   │   ├── Result Validation
│   │   │   │   └── Success/Failure Status
│   │   │   │
│   │   │   ├──  Schema Migration (run_schema_migration)
│   │   │   │   ├── SQL File Reading
│   │   │   │   ├── Statement Splitting
│   │   │   │   ├── Sequential Execution
│   │   │   │   └── Transaction Management
│   │   │   │
│   │   │   ├── 🔄 Async Query Execution (async_execute)
│   │   │   │   ├── Async Session Management
│   │   │   │   ├── Parameter Binding
│   │   │   │   ├── Transaction Handling
│   │   │   │   └── Error Management
│   │   │   │
│   │   │   ├── 👥 User Operations
│   │   │   │   ├── get_user_by_clerk_id(clerk_id: str) → Optional[Dict]
│   │   │   │   │   ├── Service Client Query
│   │   │   │   │   ├── Table: 'users'
│   │   │   │   │   ├── Filter: clerk_user_id = clerk_id
│   │   │   │   │   └── Single Result Return
│   │   │   │   ├── create_user(user_data: Dict) → Optional[Dict]
│   │   │   │   │   ├── Service Client Insert
│   │   │   │   │   ├── Table: 'users'
│   │   │   │   │   ├── Data Validation
│   │   │   │   │   └── Created User Return
│   │   │   │   ├── get_characters_by_user(user_id: str) → List[Dict]
│   │   │   │   │   ├── Service Client Query
│   │   │   │   │   ├── Table: 'characters'
│   │   │   │   │   ├── Filter: user_id = user_id
│   │   │   │   │   └── List Return
│   │   │   │   └── create_companion(companion_data: Dict) → Optional[Dict]
│   │   │   │       ├── Service Client Insert
│   │   │   │       ├── Table: 'characters'
│   │   │   │       ├── Data Validation
│   │   │   │       └── Created Companion Return
│   │   │   │
│   │   │   ├──  Storage Management (setup_storage_buckets)
│   │   │   │   ├── Bucket: 'avatars'
│   │   │   │   ├── Public Access: true
│   │   │   │   ├── Allowed MIME Types: image/jpeg, image/png, image/webp, image/gif
│   │   │   │   ├── File Size Limit: 5MB
│   │   │   │   └── Error Handling
│   │   │   │
│   │   │   └──  Connection Cleanup (close_connections)
│   │   │       ├── Engine Disposal
│   │   │       ├── Async Engine Disposal
│   │   │       └── Error Handling
│   │   │
│   │   ├── 🌐 Global Configuration Management
│   │   │   ├── supabase_config → Global Instance
│   │   │   ├── get_supabase_config() → SupabaseConfig
│   │   │   │   └── Global Instance Return
│   │   │   └── initialize_supabase() → bool
│   │   │       ├── Configuration Initialization
│   │   │       ├── Connection Testing
│   │   │       ├── Schema Migration
│   │   │       ├── Storage Setup
│   │   │       └── Success/Failure Status
│   │   │
│   │   └── 🧪 Testing & Validation
│   │       ├── Main Execution Block
│   │       ├── Logging Configuration
│   │       ├── Full Setup Testing
│   │       ├── Test User Creation
│   │       └── Connection Cleanup
│   │
│   └── 🗄️ supabase_operations.py (Core Database Operations)
│       ├── 🏗️ SupabaseOperations Class (Main Database Interface)
│       │   ├── 🔧 Constructor
│       │   │   ├── SupabaseConfig Instance
│       │   │   └── Service Client Access
│       │   │
│       │   ├── 🔑 Service Client Management
│       │   │   └── get_service_client() → Client
│       │   │       └── Supabase Service Client Return
│       │   │
│       │   ├── 👥 User Management Operations
│       │   │   ├── get_user_by_email(email: str) → Optional[Dict]
│       │   │   │   ├── Service Client Query
│       │   │   │   ├── Table: 'users'
│       │   │   │   ├── Filter: email = email
│       │   │   │   └── Single Result Return
│       │   │   ├── get_user_by_clerk_id(clerk_user_id: str) → Optional[Dict]
│       │   │   │   ├── Service Client Query
│       │   │   │   ├── Table: 'users'
│       │   │   │   ├── Filter: clerk_user_id = clerk_user_id
│       │   │   │   └── Single Result Return
│       │   │   ├── get_user_by_stripe_customer_id(customer_id: str) → Optional[Dict]
│       │   │   │   ├── Service Client Query
│       │   │   │   ├── Table: 'users'
│       │   │   │   ├── Filter: stripe_customer_id = customer_id
│       │   │   │   └── Single Result Return
│       │   │   ├── create_or_update_user(email, clerk_user_id, stripe_customer_id, **additional_fields) → Optional[Dict]
│       │   │   │   ├── Existing User Check
│       │   │   │   ├── User Data Preparation
│       │   │   │   │   ├── Required Fields: email, clerk_user_id, stripe_customer_id
│       │   │   │   │   ├── Timestamps: created_at, updated_at
│       │   │   │   │   └── Additional Fields Processing
│       │   │   │   ├── Conditional Operation
│       │   │   │   │   ├── Update: If user exists
│       │   │   │   │   └── Insert: If user doesn't exist
│       │   │   │   └── User Object Return
│       │   │   ├── update_subscription(customer_id, subscription_id, status, plan, start_date, end_date) → bool
│       │   │   │   ├── User Lookup by Stripe Customer ID
│       │   │   │   ├── Subscription Data Preparation
│       │   │   │   │   ├── subscription_status
│       │   │   │   │   ├── subscription_plan
│       │   │   │   │   ├── subscription_id
│       │   │   │   │   ├── subscription_start_date
│       │   │   │   │   ├── subscription_end_date
│       │   │   │   │   └── updated_at
│       │   │   │   ├── Database Update Operation
│       │   │   │   └── Success/Failure Status
│       │   │   ├── get_user_subscription(email: str) → Optional[Dict]
│       │   │   │   ├── User Lookup by Email
│       │   │   │   ├── Subscription Data Extraction
│       │   │   │   │   ├── status
│       │   │   │   │   ├── plan
│       │   │   │   │   ├── subscription_id
│       │   │   │   │   ├── start_date
│       │   │   │   │   ├── end_date
│       │   │   │   │   └── stripe_customer_id
│       │   │   │   └── Subscription Object Return
│       │   │   ├── is_user_premium(email: str) → bool
│       │   │   │   ├── Subscription Lookup
│       │   │   │   ├── Status Validation
│       │   │   │   │   ├── 'active' → true
│       │   │   │   │   └── 'trialing' → true
│       │   │   │   └── Boolean Return
│       │   │   └── log_subscription_event(customer_id, event_type, stripe_event_id, event_data) → bool
│       │   │       ├── User Lookup by Stripe Customer ID
│       │   │       ├── Event Data Processing
│       │   │       │   ├── JSON String Parsing
│       │   │       │   └── Raw Data Fallback
│       │   │       ├── Event Record Creation
│       │   │       │   ├── user_id
│       │   │       │   ├── event_type
│       │   │       │   ├── stripe_event_id
│       │   │       │   ├── event_data
│       │   │       │   └── created_at
│       │   │       ├── Database Insert Operation
│       │   │       └── Success/Failure Status
│       │   │
│       │   ├── 🤖 Companion/Character Management Operations
│       │   │   ├── save_companion(companion_data: Dict) → Optional[Dict]
│       │   │   │   ├── User ID Resolution
│       │   │   │   │   ├── Direct user_id Check
│       │   │   │   │   ├── Clerk ID Lookup
│       │   │   │   │   └── User Validation
│       │   │   │   ├── Database Schema Mapping
│       │   │   │   │   ├── Field Mapping: avatarUrl → avatar_url
│       │   │   │   │   ├── Field Mapping: greetingMessage → greeting_message
│       │   │   │   │   ├── Field Mapping: conversationStyle → conversation_style
│       │   │   │   │   ├── Field Mapping: isActive → is_active
│       │   │   │   │   └── Timestamps: created_at, updated_at
│       │   │   │   ├── Data Validation & Cleaning
│       │   │   │   ├── Database Insert Operation
│       │   │   │   └── Created Companion Return
│       │   │   ├── get_characters_by_user(user_id: str) → List[Dict]
│       │   │   │   ├── User ID Resolution
│       │   │   │   │   ├── Clerk ID to User ID Conversion
│       │   │   │   │   └── User Validation
│       │   │   │   ├── Service Client Query
│       │   │   │   │   ├── Table: 'characters'
│       │   │   │   │   ├── Filter: user_id = user_id AND is_active = true
│       │   │   │   │   └── List Return
│       │   │   │   └── Character Count Logging
│       │   │   ├── get_companion(companion_id: str) → Optional[Dict]
│       │   │   │   ├── Service Client Query
│       │   │   │   ├── Table: 'characters'
│       │   │   │   ├── Filter: id = companion_id
│       │   │   │   └── Single Result Return
│       │   │   ├── get_character(character_id: str) → Optional[Dict]
│       │   │   │   ├── Service Client Query
│       │   │   │   ├── Table: 'characters'
│       │   │   │   ├── Filter: id = character_id
│       │   │   │   └── Single Result Return
│       │   │   ├── get_companion(companion_id: str, user_id: str) → Optional[Dict]
│       │   │   │   ├── User ID Resolution
│       │   │   │   ├── Service Client Query
│       │   │   │   │   ├── Table: 'characters'
│       │   │   │   │   ├── Filter: id = companion_id AND user_id = user_id
│       │   │   │   │   └── Single Result Return
│       │   │   │   └── User Authorization
│       │   │   ├── update_companion(companion_id, user_id, updates) → Optional[Dict]
│       │   │   │   ├── User ID Resolution
│       │   │   │   ├── Update Data Preparation
│       │   │   │   │   ├── Timestamp: updated_at
│       │   │   │   │   ├── Field Mapping
│       │   │   │   │   └── Data Validation
│       │   │   │   ├── Database Update Operation
│       │   │   │   │   ├── Table: 'characters'
│       │   │   │   │   ├── Filter: id = companion_id AND user_id = user_id
│       │   │   │   │   └── Updated Data Return
│       │   │   │   └── Success Logging
│       │   │   ├── delete_companion(companion_id: str, user_id: str) → bool
│       │   │   │   ├── User ID Resolution
│       │   │   │   ├── Soft Delete Operation
│       │   │   │   │   ├── is_active: false
│       │   │   │   │   └── updated_at: current timestamp
│       │   │   │   ├── Database Update Operation
│       │   │   │   └── Success/Failure Status
│       │   │   ├── get_companion_count(user_id: str) → int
│       │   │   │   ├── Character List Retrieval
│       │   │   │   └── List Length Return
│       │   │   ├── search_characters(user_id: str, query: str) → List[Dict]
│       │   │   │   ├── User ID Resolution
│       │   │   │   ├── Full-Text Search Implementation
│       │   │   │   │   ├── PostgreSQL to_tsvector
│       │   │   │   │   ├── plainto_tsquery
│       │   │   │   │   ├── ILIKE Pattern Matching
│       │   │   │   │   └── ts_rank Scoring
│       │   │   │   ├── Search Query Structure
│       │   │   │   │   ├── User Filtering
│       │   │   │   │   ├── Active Character Filtering
│       │   │   │   │   ├── Text Search (name + personality)
│       │   │   │   │   ├── Pattern Matching
│       │   │   │   │   └── Result Ordering
│       │   │   │   ├── Fallback Search
│       │   │   │   │   ├── Simple String Matching
│       │   │   │   │   └── Case-Insensitive Search
│       │   │   │   └── Search Results Return
│       │   │   └── create_companion(data: Dict) → Optional[Dict]
│       │   │       ├── Service Client Insert
│       │   │       ├── Table: 'characters'
│       │   │       └── Created Companion Return
│       │   │
│       │   ├── 💬 Chat System Operations
│       │   │   ├── create_chat_session(user_id, companion_id, character_id, title) → Optional[Dict]
│       │   │   │   ├── User ID Resolution
│       │   │   │   ├── Session Data Preparation
│       │   │   │   │   ├── user_id
│       │   │   │   │   ├── companion_id
│       │   │   │   │   ├── character_id
│       │   │   │   │   ├── title (default: "Chat {timestamp}")
│       │   │   │   │   ├── created_at
│       │   │   │   │   ├── updated_at
│       │   │   │   │   └── last_message_at
│       │   │   │   ├── Database Insert Operation
│       │   │   │   └── Created Session Return
│       │   │   ├── add_chat_message(session_id, role, content, metadata) → Optional[Dict]
│       │   │   │   ├── Message Data Preparation
│       │   │   │   │   ├── session_id
│       │   │   │   │   ├── role
│       │   │   │   │   ├── content
│       │   │   │   │   ├── metadata
│       │   │   │   │   └── created_at
│       │   │   │   ├── Database Insert Operation
│       │   │   │   ├── Session Timestamp Update
│       │   │   │   └── Created Message Return
│       │   │   ├── update_chat_session_timestamp(session_id: str)
│       │   │   │   ├── Timestamp Update
│       │   │   │   │   ├── last_message_at: current timestamp
│       │   │   │   │   └── updated_at: current timestamp
│       │   │   │   └── Database Update Operation
│       │   │   ├── get_chat_sessions(user_id: str, limit: int) → List[Dict]
│       │   │   │   ├── User ID Resolution
│       │   │   │   ├── Service Client Query
│       │   │   │   │   ├── Table: 'chat_sessions'
│       │   │   │   │   ├── Filter: user_id = user_id
│       │   │   │   │   ├── Order: last_message_at DESC
│       │   │   │   │   └── Limit: limit
│       │   │   │   └── Session List Return
│       │   │   ├── get_chat_messages(session_id: str, limit: int) → List[Dict]
│       │   │   │   ├── Service Client Query
│       │   │   │   │   ├── Table: 'chat_messages'
│       │   │   │   │   ├── Filter: session_id = session_id
│       │   │   │   │   ├── Order: created_at ASC
│       │   │   │   │   └── Limit: limit
│       │   │   │   └── Message List Return
│       │   │   ├── update_user_message_count(user_id: str) → bool
│       │   │   │   ├── User ID Resolution
│       │   │   │   ├── Database Function Call
│       │   │   │   │   └── update_user_message_count(user_id)
│       │   │   │   ├── Transaction Management
│       │   │   │   └── Success/Failure Status
│       │   │   ├── get_user_usage(user_id: str) → Dict
│       │   │   │   ├── User ID Resolution
│       │   │   │   ├── Service Client Query
│       │   │   │   │   ├── Table: 'user_usage'
│       │   │   │   │   ├── Filter: user_id = user_id
│       │   │   │   │   └── Single Result Return
│       │   │   │   ├── Daily Reset Logic
│       │   │   │   │   ├── Today's Date Check
│       │   │   │   │   ├── Last Reset Date Comparison
│       │   │   │   │   ├── Automatic Reset Trigger
│       │   │   │   │   └── Usage Data Return
│       │   │   │   └── Usage Statistics Return
│       │   │   │       ├── messages_used_today
│       │   │   │       └── total_messages_sent
│       │   │   └── reset_daily_message_count(user_id: str) → bool
│       │   │       ├── Service Client Update
│       │   │       │   ├── Table: 'user_usage'
│       │   │       │   ├── messages_used_today: 0
│       │   │       │   ├── last_reset_date: today
│       │   │       │   └── updated_at: current timestamp
│       │   │       └── Success/Failure Status
│       │   │
│       │   ├── 🔄 Companion Update Operations
│       │   │   ├── update_co
```

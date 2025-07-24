from fastapi import FastAPI, HTTPException, Request, Depends, Path, Body, status, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import requests
import json
import os
from dotenv import load_dotenv
import logging
import stripe
from datetime import datetime
from backend.py.supabase_operations import SupabaseOperations
from backend.py.auth_middleware import JWTBearer, get_current_user
from huggingface_hub import InferenceClient
from io import BytesIO
import base64

# Load environment variables
load_dotenv('.env.railway')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="GirlfriendPT AI Backend",
    description="Backend API for AI companion chat application",
    version="1.0.0"
)

# Configure CORS
cors_origins = os.getenv("CORS_ORIGINS", "https://girlfriendpt.com").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize JWT Bearer authentication
auth_scheme = JWTBearer()

# API Key for internal service communication
API_KEY = os.getenv("API_KEY")

def verify_api_key(api_key: str = Header(..., description="API Key for internal service communication")):
    """Verify API key for internal service communication"""
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    return api_key

def get_db() -> SupabaseOperations:
    """Dependency to get database instance"""
    return SupabaseOperations()

# Models
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1000
    user_email: Optional[str] = None
    companion_id: Optional[str] = None
    personality: Optional[str] = None
    backstory: Optional[str] = None
    conversation_style: Optional[str] = None
    greeting_message: Optional[str] = None
    character_id: Optional[str] = None
    character_name: Optional[str] = None
    character_description: Optional[str] = None

class ChatResponse(BaseModel):
    content: str
    role: str = "assistant"
    usage: Optional[Dict[str, int]] = None

class CompanionCreate(BaseModel):
    name: str
    personality: str
    backstory: str
    avatar_url: Optional[str] = None
    greeting_message: str
    interests: List[str]
    conversation_style: str
    appearance: Optional[Dict[str, str]] = None
    occupation: Optional[str] = None
    hobbies: List[str]
    traits: List[str]
    user_id: str  # Clerk user ID

class CompanionFilters(BaseModel):
    user_id: str
    search: Optional[str] = None

class CompanionUpdate(BaseModel):
    name: Optional[str] = None
    personality: Optional[str] = None
    # Add other optional fields...

class UserCreate(BaseModel):
    email: str
    clerk_user_id: Optional[str] = None
    stripe_customer_id: Optional[str] = None

class UserUpdate(BaseModel):
    email: Optional[str] = None
    # Add other fields

class ImageGenerationRequest(BaseModel):
    prompt: str
    style: Optional[str] = "realistic"
    size: Optional[str] = "512x512"

# Initialize Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

# Health check endpoint
@app.get("/")
async def root():
    return {"status": "ok", "message": "GirlfriendPT API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Companion endpoints
@app.post("/api/characters")
async def create_companion(
    companion: CompanionCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: SupabaseOperations = Depends(get_db)
):
    if companion.user_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create companion for another user"
        )
    created = await db.create_companion(companion.dict())
    if not created:
        raise HTTPException(status_code=500, detail="Failed to create companion")
    return created

@app.get("/api/characters")
async def get_characters(
    filters: CompanionFilters = Body(...),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: SupabaseOperations = Depends(get_db)
):
    if filters.user_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to get characters for another user"
        )
    characters = await db.get_characters_by_user(filters.user_id)
    if filters.search:
        characters = [c for c in characters if filters.search.lower() in c['name'].lower() or filters.search.lower() in c['personality'].lower()]
    return characters

@app.get("/api/characters/{companion_id}")
async def get_single_companion(
    companion_id: str = Path(...),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: SupabaseOperations = Depends(get_db)
):
    companion = await db.get_companion(companion_id, current_user["id"])
    if not companion:
        raise HTTPException(status_code=404, detail="Companion not found")
    return companion

@app.put("/api/characters/{companion_id}")
async def update_companion(
    companion_id: str = Path(...),
    updates: CompanionUpdate = Body(...),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: SupabaseOperations = Depends(get_db)
):
    updated = await db.update_companion(companion_id, current_user["id"], updates.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to update companion")
    return updated

@app.delete("/api/characters/{companion_id}")
async def delete_companion_endpoint(
    companion_id: str = Path(...),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: SupabaseOperations = Depends(get_db)
):
    deleted = await db.delete_companion(companion_id, current_user["id"])
    if not deleted:
        raise HTTPException(status_code=404, detail="Companion not found")
    return {"success": True}

# Chat endpoint with JWT authentication
@app.post("/api/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: SupabaseOperations = Depends(get_db)
):
    """
    Main chat endpoint that processes messages and returns AI responses
    """
    try:
        system_message = await _build_system_message(request, db)
        openrouter_messages = [
            {"role": "system", "content": system_message}
        ]
        for msg in request.messages:
            openrouter_messages.append({
                "role": msg.role,
                "content": msg.content
            })
        logger.info(f"Sending request to OpenRouter with {len(openrouter_messages)} messages")
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {os.getenv('OPEN_ROUTER_API_KEY')}",
                "Content-Type": "application/json",
                "HTTP-Referer": os.getenv("PUBLIC_URL", "https://girlfriendpt.com"),
                "X-Title": "GirlfriendPT AI",
            },
            data=json.dumps({
                "model": "cognitivecomputations/dolphin-mistral-24b-venice-edition:free",
                "messages": openrouter_messages,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "stream": False
            })
        )
        if response.status_code != 200:
            logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"OpenRouter API error: {response.text}"
            )
        data = response.json()
        assistant_message = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        if request.user_email:
            logger.info(f"Chat request from user: {request.user_email}")
        return ChatResponse(
            content=assistant_message,
            role="assistant",
            usage={
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0)
            }
        )
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"API request failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Stripe webhook endpoint
@app.post("/api/stripe/webhook")
async def stripe_webhook(request: Request, db: SupabaseOperations = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.getenv('STRIPE_WEBHOOK_SECRET')
        )
    except ValueError:
        raise HTTPException(status_code=400, detail='Invalid payload')
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail='Invalid signature')

    client = db.get_service_client()

    if event['type'] == 'customer.subscription.created' or event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        customer_id = subscription['customer']
        plan_id = subscription['items']['data'][0]['price']['id']

        # Map price ID to plan (use actual IDs from creation)
        if plan_id == 'price_1Q7Z4gY2nY1Y7Z9Z':
            plan = 'basic'
        elif plan_id == 'price_1Q7Z5hZ3oZ2Z8A0A':
            plan = 'premium'
        else:
            plan = 'unknown'

        update_data = {
            'stripe_customer_id': customer_id,
            'subscription_id': subscription['id'],
            'subscription_plan': plan,
            'subscription_status': 'active',
            'subscription_start_date': datetime.fromtimestamp(subscription['current_period_start']).isoformat(),
            'subscription_end_date': datetime.fromtimestamp(subscription['current_period_end']).isoformat(),
            'updated_at': datetime.now().isoformat()
        }

        # Find user by stripe_customer_id and update
        response = client.table('users').update(update_data).eq('stripe_customer_id', customer_id).execute()

        if not response.data:
            logger.error(f"Failed to update user for subscription {subscription['id']}")
            return {'status': 'error'}

    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        customer_id = subscription['customer']

        update_data = {
            'subscription_status': 'canceled',
            'subscription_end_date': datetime.fromtimestamp(subscription['current_period_end']).isoformat(),
            'updated_at': datetime.now().isoformat()
        }

        response = client.table('users').update(update_data).eq('stripe_customer_id', customer_id).execute()

        if not response.data:
            logger.error(f"Failed to update user for canceled subscription {subscription['id']}")
            return {'status': 'error'}

    return {'status': 'success'}

# User endpoints
@app.post("/api/users")
async def create_user(
    user: UserCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: SupabaseOperations = Depends(get_db)
):
    if user.clerk_user_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create user for another user"
        )
    created = await db.create_or_update_user(user.email, user.clerk_user_id, user.stripe_customer_id)
    if not created:
        raise HTTPException(status_code=500, detail="Failed to create user")
    return created

@app.get("/api/users/{user_id}")
async def get_user(
    user_id: str = Path(...),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: SupabaseOperations = Depends(get_db)
):
    if user_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to get user for another user"
        )
    user = await db.get_user_by_clerk_id(user_id)  # Assuming user_id is clerk_id
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.put("/api/users/{user_id}")
async def update_user(
    user_id: str = Path(...),
    updates: UserUpdate = Body(...),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: SupabaseOperations = Depends(get_db)
):
    if user_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update user for another user"
        )
    updated = await db.create_or_update_user(None, user_id, **updates.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to update user")
    return updated

# Character endpoints
@app.get("/api/characters")
async def get_characters(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: SupabaseOperations = Depends(get_db)
):
    client = db.get_service_client()
    response = client.table('characters').select('*').execute()
    return response.data or []

@app.get("/api/characters/{character_id}")
async def get_single_character(
    character_id: str = Path(...),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: SupabaseOperations = Depends(get_db)
):
    character = await db.get_character(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return character

# Image generation endpoint
@app.post("/api/generate-image")
async def generate_image(
    req: ImageGenerationRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: SupabaseOperations = Depends(get_db)
):
    try:
        client = InferenceClient(model="stabilityai/stable-diffusion-2-1")

        # Enhance prompt with style
        enhanced_prompt = f"{req.prompt}, in {req.style} style, high quality, detailed"

        # Generate image
        image = client.text_to_image(
            prompt=enhanced_prompt,
            height=int(req.size.split('x')[1]),
            width=int(req.size.split('x')[0]),
            num_inference_steps=50,
            guidance_scale=7.5
        )

        # Convert to base64
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        return {
            "success": True,
            "image": f"data:image/png;base64,{img_str}"
        }
    except Exception as e:
        logger.error(f"Image generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def _build_system_message(request: ChatRequest, db: SupabaseOperations) -> str:
    """
    Build system message based on companion or character data
    """
    if request.companion_id:
        companion = await db.get_companion(request.companion_id)  # Assume method exists or add it
        if companion:
            return f"You are {companion['name']}. Personality: {companion['personality']}. Backstory: {companion['backstory']}. Traits: {', '.join(companion.get('traits', []))}. Conversation Style: {companion['conversation_style']}. Respond in character."
        else:
            return "You are a default AI companion."
    elif request.character_id:
        character = await db.get_character(request.character_id)  # Assume method exists
        if character:
            return f"You are {character['name']}. Personality: {character['intimate_personality']}. Backstory: {character['backstory_hook']}. Traits: {character.get('traits_json', {})}"
        else:
            return "You are a default AI character."
    return "You are a helpful AI."

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("API_HOST", "0.0.0.0")
    uvicorn.run("main:app", host=host, port=port, reload=True)

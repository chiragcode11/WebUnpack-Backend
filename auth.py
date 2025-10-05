from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config import settings
from database import get_database
from models import User
from datetime import datetime, timedelta
import httpx
import jwt
import json
from cachetools import TTLCache
import asyncio

security = HTTPBearer()

jwks_cache = TTLCache(maxsize=1, ttl=3600)
user_cache = TTLCache(maxsize=1000, ttl=300)
profile_update_tracker = TTLCache(maxsize=1000, ttl=3600)
cache_lock = asyncio.Lock()

class ClerkAuth:
    def __init__(self):
        self.jwks_url = settings.CLERK_JWKS_URL
    
    async def get_jwks(self):
        async with cache_lock:
            if "jwks" in jwks_cache:
                return jwks_cache["jwks"]
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(self.jwks_url)
                if response.status_code == 200:
                    jwks_data = response.json()
                    async with cache_lock:
                        jwks_cache["jwks"] = jwks_data
                    return jwks_data
            except Exception as e:
                raise HTTPException(status_code=503, detail=f"Could not fetch JWKS: {str(e)}")
        
        raise HTTPException(status_code=503, detail="Could not fetch JWKS")
    
    async def verify_token(self, token: str):
        try:
            jwks = await self.get_jwks()
            if not jwks:
                raise HTTPException(status_code=401, detail="Could not fetch JWKS")

            header = jwt.get_unverified_header(token)
            kid = header.get('kid')

            key = None
            for jwk in jwks['keys']:
                if jwk['kid'] == kid:
                    key = jwk
                    break
            
            if not key:
                raise HTTPException(status_code=401, detail="Invalid token")

            public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key))

            payload = jwt.decode(
                token, 
                public_key, 
                algorithms=['RS256'],
                audience=None, 
                options={"verify_aud": False}
            )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Token verification failed: {str(e)}")

clerk_auth = ClerkAuth()

async def get_or_create_user(clerk_user_id: str) -> User:
    cache_key = f"user_{clerk_user_id}"
    
    async with cache_lock:
        if cache_key in user_cache:
            return user_cache[cache_key]
    
    database = await get_database()
    collection = database["users"]
    
    existing_user = await collection.find_one({"clerk_id": clerk_user_id})
    
    if existing_user:
        if "reactify_count" not in existing_user:
            await collection.update_one(
                {"clerk_id": clerk_user_id},
                {"$set": {"reactify_count": 0}}
            )
            existing_user["reactify_count"] = 0
        
        existing_user["id"] = str(existing_user["_id"])
        user = User(**existing_user)
        async with cache_lock:
            user_cache[cache_key] = user
        return user
    
    new_user_data = {
        "clerk_id": clerk_user_id,
        "email": None,
        "name": None,
        "avatar_url": None,
        "single_page_count": 0,
        "multi_page_count": 0,
        "reactify_count": 0,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await collection.insert_one(new_user_data)
    new_user_data["id"] = str(result.inserted_id)
    
    user = User(**new_user_data)
    async with cache_lock:
        user_cache[cache_key] = user
    
    asyncio.create_task(update_user_profile_once(clerk_user_id))
    
    return user


async def update_user_profile_once(clerk_user_id: str):
    update_key = f"update_{clerk_user_id}"
    
    async with cache_lock:
        if update_key in profile_update_tracker:
            return
        profile_update_tracker[update_key] = True
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            headers = {"Authorization": f"Bearer {settings.CLERK_SECRET_KEY}"}
            response = await client.get(
                f"https://api.clerk.dev/v1/users/{clerk_user_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                clerk_user_data = response.json()
                
                database = await get_database()
                collection = database["users"]
                
                update_data = {
                    "email": clerk_user_data.get("email_addresses", [{}])[0].get("email_address"),
                    "name": f"{clerk_user_data.get('first_name', '')} {clerk_user_data.get('last_name', '')}".strip(),
                    "avatar_url": clerk_user_data.get("image_url"),
                    "updated_at": datetime.utcnow()
                }
                
                await collection.update_one(
                    {"clerk_id": clerk_user_id},
                    {"$set": update_data}
                )
                
                cache_key = f"user_{clerk_user_id}"
                async with cache_lock:
                    if cache_key in user_cache:
                        del user_cache[cache_key]
    except:
        pass

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    payload = await clerk_auth.verify_token(credentials.credentials)

    clerk_user_id = payload.get("sub")
    if not clerk_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: no user ID"
        )

    user = await get_or_create_user(clerk_user_id)
    
    return user
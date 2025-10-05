from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request, Header
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import os
import uvicorn
import nest_asyncio
from datetime import datetime
import secrets
import logging
import traceback
from bson import ObjectId
from typing import Optional
import re
from models import (
    ScrapeRequest, ScrapeResponse, DiscoverPagesRequest, DiscoverPagesResponse,
    User, WaitlistRequest, WaitlistResponse
)
from services.scraper_service import ScraperService
from services.usage_service import usage_service
from auth import get_current_user, get_or_create_user, clerk_auth
from database import connect_to_mongo, close_mongo_connection, get_database
from services.reactify_service import ReactifyService
from models import ReactifyRequest, ReactifyDiscoverRequest
from services.communication_service import communication_service
from models import ContactRequest, FeedbackRequest, ContactResponse, FeedbackResponse

logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

nest_asyncio.apply()

reactify_service = ReactifyService(os.getenv('GEMINI_API_KEY', ''))

ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000').split(',')
PRODUCTION = os.getenv('ENVIRONMENT', 'development') == 'production'
MAX_REQUEST_SIZE = 1000 * 1024 * 1024

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = "default-src 'self'"
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.cache = {}
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        current_time = datetime.utcnow().timestamp()
        
        if client_ip not in self.cache:
            self.cache[client_ip] = []
        
        self.cache[client_ip] = [
            timestamp for timestamp in self.cache[client_ip]
            if current_time - timestamp < self.period
        ]
        
        if len(self.cache[client_ip]) >= self.calls:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please try again later."}
            )
        
        self.cache[client_ip].append(current_time)
        response = await call_next(request)
        return response

def serialize_doc(doc):
    if doc is None:
        return None
    
    doc = dict(doc)
    
    if "_id" in doc:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
    
    for key, value in doc.items():
        if isinstance(value, ObjectId):
            doc[key] = str(value)
        elif isinstance(value, datetime):
            doc[key] = value.isoformat()
        elif isinstance(value, list):
            doc[key] = [
                str(item) if isinstance(item, ObjectId) else 
                item.isoformat() if isinstance(item, datetime) else item
                for item in value
            ]
    
    return doc

def sanitize_url(url: str) -> str:
    url = url.strip()
    if not re.match(r'^https?://', url):
        raise ValueError("Invalid URL protocol")
    if len(url) > 2048:
        raise ValueError("URL too long")
    return url

def generate_secure_job_id() -> str:
    return f"job_{secrets.token_urlsafe(16)}"

app = FastAPI(
    title="SiteScraper API", 
    version="1.0.0",
    docs_url="/docs" if not PRODUCTION else None,
    redoc_url="/redoc" if not PRODUCTION else None
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware, calls=100, period=60)

if PRODUCTION:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=[os.getenv('ALLOWED_HOST', 'yourdomain.com')]
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["Content-Type"],
    max_age=600
)

scraper_service = ScraperService()

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": "An error occurred", "type": "http_exception"}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": "Invalid request data", "type": "validation_error"}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception: {str(exc)}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred", "type": "server_error"}
    )

@app.middleware("http")
async def check_request_size(request: Request, call_next):
    if request.method in ["POST", "PUT", "PATCH"]:
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_REQUEST_SIZE:
            return JSONResponse(
                status_code=413,
                content={"detail": "Request body too large"}
            )
    response = await call_next(request)
    return response

@app.on_event("startup")
async def startup_event():
    try:
        await connect_to_mongo()
        logger.info("API started successfully")
    except Exception as e:
        logger.error(f"Failed to start API: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    try:
        await close_mongo_connection()
        logger.info("API shutdown completed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

@app.get("/")
async def root():
    return {"message": "API", "status": "running"}

@app.get("/health")
async def health_check():
    try:
        database = await get_database()
        await database.list_collection_names()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat()
            }
        )

@app.get("/me")
async def get_user_profile(current_user: User = Depends(get_current_user)):
    try:
        usage = await usage_service.get_user_usage(current_user.clerk_id)
        
        return {
            "email": current_user.email,
            "name": current_user.name,
            "avatar_url": current_user.avatar_url,
            "usage": {
                "single_page_used": usage.single_page_used,
                "single_page_limit": usage.single_page_limit,
                "multi_page_used": usage.multi_page_used,
                "multi_page_limit": usage.multi_page_limit,
                "can_scrape_single": usage.can_scrape_single,
                "can_scrape_multi": usage.can_scrape_multi
            }
        }
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve profile")

@app.get("/my-jobs")
async def get_user_jobs(current_user: User = Depends(get_current_user)):
    try:
        database = await get_database()
        collection = database["scrape_jobs"]
        
        cursor = collection.find(
            {"user_id": current_user.clerk_id}
        ).sort("created_at", -1).limit(50)
        
        jobs = []
        async for job_data in cursor:
            serialized_job = serialize_doc(job_data)
            if serialized_job:
                safe_job = {
                    "id": serialized_job.get("id"),
                    "job_id": serialized_job.get("job_id"),
                    "url": serialized_job.get("url"),
                    "site_type": serialized_job.get("site_type"),
                    "scrape_mode": serialized_job.get("scrape_mode"),
                    "status": serialized_job.get("status"),
                    "created_at": serialized_job.get("created_at"),
                    "completed_at": serialized_job.get("completed_at"),
                    "pages_scraped": serialized_job.get("pages_scraped", 0)
                }
                jobs.append(safe_job)
        
        return {"jobs": jobs}
    except Exception as e:
        logger.error(f"Error getting user jobs: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve jobs")

@app.post("/discover-pages", response_model=DiscoverPagesResponse)
async def discover_pages(
    request: DiscoverPagesRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        url = sanitize_url(str(request.url))
        logger.info(f"User discovering pages")
        
        result = await scraper_service.discover_pages(url, request.site_type.value)
        
        return DiscoverPagesResponse(**result)
    except ValueError as e:
        return DiscoverPagesResponse(
            success=False,
            message="Invalid URL provided",
            pages=[]
        )
    except Exception as e:
        logger.error(f"Error in discover-pages: {e}")
        return DiscoverPagesResponse(
            success=False,
            message="Page discovery failed",
            pages=[]
        )

async def perform_scraping(job_id: str, user_id: str, request: ScrapeRequest):
    database = await get_database()
    collection = database["scrape_jobs"]
    
    try:
        logger.info(f"Starting scraping for job")
        
        await collection.update_one(
            {"job_id": job_id},
            {"$set": {"status": "processing"}}
        )
        
        result = await scraper_service.scrape_site(
            str(request.url), 
            request.site_type.value,
            request.scrape_mode.value,
            request.selected_pages,
            job_id=job_id
        )
        
        if result and result.get("success"):
            logger.info(f"Scraping completed")
            
            await collection.update_one(
                {"job_id": job_id},
                {"$set": {
                    "status": "completed",
                    "file_path": result.get("file_path"),
                    "download_url": f"/download/{job_id}",
                    "completed_at": datetime.utcnow(),
                    "pages_scraped": len(request.selected_pages) if request.selected_pages else 1
                }}
            )
        else:
            logger.error(f"Scraping failed")
            await collection.update_one(
                {"job_id": job_id},
                {"$set": {
                    "status": "failed",
                    "error_message": "Scraping failed",
                    "completed_at": datetime.utcnow()
                }}
            )
            await usage_service.decrement_usage(user_id, request.scrape_mode.value)
            
    except Exception as e:
        logger.error(f"Scraping error: {e}")
        await collection.update_one(
            {"job_id": job_id},
            {"$set": {
                "status": "failed",
                "error_message": "Processing error",
                "completed_at": datetime.utcnow()
            }}
        )
        await usage_service.decrement_usage(user_id, request.scrape_mode.value)
        
@app.post("/scrape", response_model=ScrapeResponse)
async def scrape_site(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    try:
        url = sanitize_url(str(request.url))
        request.url = url
        
        can_scrape = await usage_service.can_user_scrape(
            current_user.clerk_id, 
            request.scrape_mode.value
        )
        
        if not can_scrape:
            usage = await usage_service.get_user_usage(current_user.clerk_id)
            limit_type = "single-page" if request.scrape_mode.value == "single_page" else "multi-page"
            limit_value = usage.single_page_limit if request.scrape_mode.value == "single_page" else usage.multi_page_limit
            return ScrapeResponse(
                success=False,
                message=f"You have reached your {limit_type} limit ({limit_value})"
            )
        
        logger.info(f"Starting scrape")
        
        await usage_service.increment_usage(current_user.clerk_id, request.scrape_mode.value)
        
        job_id = generate_secure_job_id()
        
        database = await get_database()
        collection = database["scrape_jobs"]
        
        scrape_job_data = {
            "user_id": current_user.clerk_id,
            "job_id": job_id,
            "url": url,
            "site_type": request.site_type.value,
            "scrape_mode": request.scrape_mode.value,
            "selected_pages": request.selected_pages[:25] if request.selected_pages else [],
            "status": "pending",
            "created_at": datetime.utcnow(),
            "pages_scraped": 0
        }
        
        await collection.insert_one(scrape_job_data)
        
        background_tasks.add_task(
            perform_scraping,
            job_id,
            current_user.clerk_id,
            request
        )
        
        return ScrapeResponse(
            success=True,
            message="Scraping started successfully",
            job_id=job_id
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid URL provided")
    except Exception as e:
        logger.error(f"Error in scrape endpoint: {e}")
        raise HTTPException(status_code=500, detail="Failed to start scraping")

@app.get("/job-status/{job_id}")
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    try:
        if not re.match(r'^job_[A-Za-z0-9_-]+$', job_id):
            raise HTTPException(status_code=400, detail="Invalid job ID")
        
        database = await get_database()
        collection = database["scrape_jobs"]
        
        job = await collection.find_one({
            "job_id": job_id,
            "user_id": current_user.clerk_id
        })
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        safe_job = {
            "job_id": job.get("job_id"),
            "status": job.get("status"),
            "created_at": job.get("created_at").isoformat() if job.get("created_at") else None,
            "completed_at": job.get("completed_at").isoformat() if job.get("completed_at") else None,
            "error_message": job.get("error_message"),
            "pages_scraped": job.get("pages_scraped", 0)
        }
        
        return safe_job
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get status")

@app.get("/download/{job_id}")
async def download_file(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    try:
        if not re.match(r'^job_[A-Za-z0-9_-]+$', job_id):
            raise HTTPException(status_code=400, detail="Invalid job ID")
        
        database = await get_database()
        collection = database["scrape_jobs"]
        
        job = await collection.find_one({
            "job_id": job_id,
            "user_id": current_user.clerk_id,
            "status": "completed"
        })
        
        if not job:
            raise HTTPException(status_code=404, detail="File not found")
        
        safe_filename = re.sub(r'[^A-Za-z0-9_-]', '', job_id)
        file_path = f"app/static/{safe_filename}.zip"
        
        if not os.path.exists(file_path):
            file_path = f"static/{safe_filename}.zip"
            if not os.path.exists(file_path):
                raise HTTPException(status_code=404, detail="File not available")
        
        real_path = os.path.realpath(file_path)
        allowed_dir = os.path.realpath("app/static")
        
        if not real_path.startswith(allowed_dir) and not real_path.startswith(os.path.realpath("static")):
            raise HTTPException(status_code=403, detail="Access denied")
        
        return FileResponse(
            file_path, 
            filename=f"export_{safe_filename}.zip", 
            media_type="application/zip"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        raise HTTPException(status_code=500, detail="Download failed")

@app.post("/waitlist", response_model=WaitlistResponse)
async def join_waitlist(request: WaitlistRequest, http_request: Request):
    try:
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', request.email):
            return WaitlistResponse(
                success=False,
                message="Invalid email address"
            )
        
        database = await get_database()
        collection = database["waitlist"]
        
        existing_entry = await collection.find_one({"email": request.email})
        if existing_entry:
            return WaitlistResponse(
                success=True,
                message="You're already on the waitlist!"
            )
        
        waitlist_entry = {
            "email": request.email,
            "created_at": datetime.utcnow()
        }
        
        await collection.insert_one(waitlist_entry)
        
        logger.info(f"New waitlist entry")
        
        return WaitlistResponse(
            success=True,
            message="Welcome to the waitlist!"
        )
        
    except Exception as e:
        logger.error(f"Error adding to waitlist: {e}")
        return WaitlistResponse(
            success=False,
            message="Failed to join waitlist"
        )

async def get_current_user_optional(authorization: str = Header(None)) -> Optional[User]:
    if not authorization:
        return None
    
    try:
        if not authorization.startswith("Bearer "):
            return None
        
        token = authorization.split(" ")[1]
        
        if len(token) > 2048:
            return None
        
        payload = await clerk_auth.verify_token(token)
        clerk_user_id = payload.get("sub")
        
        if not clerk_user_id:
            return None
        
        user = await get_or_create_user(clerk_user_id)
        return user
    except Exception as e:
        logger.warning(f"Optional auth failed: {e}")
        return None

@app.post("/contact", response_model=ContactResponse)
async def submit_contact_form(
    request: ContactRequest,
    current_user: User = Depends(get_current_user_optional)
):
    try:
        user_id = current_user.clerk_id if current_user else None
        
        logger.info(f"Contact form submission")
        
        result = await communication_service.submit_contact_form(request, user_id)
        
        return ContactResponse(**result)
        
    except Exception as e:
        logger.error(f"Error in contact form: {e}")
        return ContactResponse(
            success=False,
            message="Failed to submit message"
        )

@app.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    request: FeedbackRequest,
    current_user: User = Depends(get_current_user_optional)
):
    try:
        user_id = current_user.clerk_id if current_user else None
        
        logger.info(f"Feedback submission")
        
        result = await communication_service.submit_feedback(request, user_id)
        
        return FeedbackResponse(**result)
        
    except Exception as e:
        logger.error(f"Error in feedback: {e}")
        return FeedbackResponse(
            success=False,
            message="Failed to submit feedback"
        )

@app.get("/my-submissions")
async def get_user_submissions(
    current_user: User = Depends(get_current_user)
):
    try:
        result = await communication_service.get_user_submissions(current_user.clerk_id)
        return result
    except Exception as e:
        logger.error(f"Error getting submissions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get submissions")

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=not PRODUCTION,
        log_level="warning"
    )
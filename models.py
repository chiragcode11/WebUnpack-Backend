from pydantic import BaseModel, HttpUrl, Field, ConfigDict, EmailStr
from typing import Optional, List, Any, Dict 
from enum import Enum
from datetime import datetime
from bson import ObjectId


class SiteType(str, Enum):
    FRAMER = "framer"
    WEBFLOW = "webflow"
    WORDPRESS = "wordpress"
    WIX = "wix"
    SHOPIFY = "shopify"
    BOLT = "bolt"
    LOVABLE = "lovable"
    GUMROAD = "gumroad"
    REPLIT = "replit"
    SQUARESPACE = "squarespace"
    NOTION = "notion"
    ROCKET = "rocket"
    GENERAL = "general"


class ScrapeMode(str, Enum):
    SINGLE_PAGE = "single_page"
    MULTI_PAGE = "multi_page"


class PageInfo(BaseModel):
    url: str
    title: str
    path: str


class DiscoverPagesRequest(BaseModel):
    url: HttpUrl
    site_type: SiteType = SiteType.FRAMER


class DiscoverPagesResponse(BaseModel):
    success: bool
    message: str
    pages: List[PageInfo] = []


class ScrapeRequest(BaseModel):
    url: HttpUrl
    site_type: SiteType = SiteType.FRAMER
    scrape_mode: ScrapeMode = ScrapeMode.SINGLE_PAGE
    selected_pages: Optional[List[str]] = None


class ScrapeResponse(BaseModel):
    success: bool
    message: str
    download_url: Optional[str] = None
    file_path: Optional[str] = None
    job_id: Optional[str] = None


class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler):
        from pydantic_core import core_schema
        return core_schema.union_schema([
            core_schema.is_instance_schema(ObjectId),
            core_schema.no_info_plain_validator_function(cls.validate),
        ])

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")


class User(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    clerk_id: str
    email: Optional[str]
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    single_page_count: int = 0
    multi_page_count: int = 0
    reactify_count: int = 0
    created_at: datetime
    updated_at: datetime


class UserUsage(BaseModel):
    single_page_used: int
    multi_page_used: int
    reactify_used: int = 0
    single_page_limit: int = 25
    multi_page_limit: int = 10
    reactify_limit: int = 1
    can_scrape_single: bool
    can_scrape_multi: bool
    can_reactify: bool = True


class ScrapeJob(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    user_id: str 
    job_id: str 
    url: str
    site_type: str
    scrape_mode: str
    selected_pages: Optional[List[str]] = None
    status: str
    file_path: Optional[str] = None
    download_url: Optional[str] = None
    pages_scraped: int = 0
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class WaitlistRequest(BaseModel):
    email: EmailStr


class WaitlistResponse(BaseModel):
    success: bool
    message: str


class ReactifyDiscoverRequest(BaseModel):
    url: HttpUrl


class ConversionOptions(BaseModel):
    framework: str = "nextjs"
    styling: str = "css_modules"
    typescript: bool = True
    optimization_level: str = "standard"
    include_tests: bool = True


class ReactifyRequest(BaseModel):
    page_url: HttpUrl
    conversion_options: Optional[ConversionOptions] = None


class ReactifyResponse(BaseModel):
    success: bool
    message: str
    job_id: Optional[str] = None
    estimated_time: Optional[str] = None


class ReactifyJob(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    user_id: str
    job_id: str
    page_url: str
    conversion_options: Dict = {}
    status: str
    download_url: Optional[str] = None
    file_size_mb: Optional[float] = None
    components_generated: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

class ContactRequest(BaseModel):
    name: str
    email: EmailStr
    subject: str
    message: str
    created_at: Optional[datetime] = None

class FeedbackRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    feedback_type: str = Field(..., pattern="^(general|feature|bug)$")
    title: str
    description: str
    priority: str = Field(..., pattern="^(low|medium|high|urgent)$")
    created_at: Optional[datetime] = None

class ContactResponse(BaseModel):
    success: bool
    message: str
    ticket_id: Optional[str] = None

class FeedbackResponse(BaseModel):
    success: bool
    message: str
    feedback_id: Optional[str] = None


from datetime import datetime
from typing import Optional, List
from database import get_database
from models import User, ScrapeJob

class UserService:
    def __init__(self):
        self.collection_name = "users"
        self.jobs_collection_name = "scrape_jobs"

    async def get_or_create_user(self, clerk_user_data: dict) -> User:
        """Get existing user or create new one from Clerk data"""
        database = await get_database()
        collection = database[self.collection_name]
        
        existing_user = await collection.find_one({"clerk_id": clerk_user_data["id"]})
        
        if existing_user:
            update_data = {
                "email": clerk_user_data.get("email_addresses", [{}])[0].get("email_address"),
                "name": f"{clerk_user_data.get('first_name', '')} {clerk_user_data.get('last_name', '')}".strip(),
                "avatar_url": clerk_user_data.get("image_url"),
                "updated_at": datetime.utcnow()
            }
            
            await collection.update_one(
                {"clerk_id": clerk_user_data["id"]},
                {"$set": update_data}
            )

            updated_user = await collection.find_one({"clerk_id": clerk_user_data["id"]})
            return User(**updated_user)
        else:
            new_user = User(
                clerk_id=clerk_user_data["id"],
                email=clerk_user_data.get("email_addresses", [{}])[0].get("email_address"),
                name=f"{clerk_user_data.get('first_name', '')} {clerk_user_data.get('last_name', '')}".strip(),
                avatar_url=clerk_user_data.get("image_url"),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            result = await collection.insert_one(new_user.dict(exclude={"id"}))
            new_user.id = result.inserted_id
            
            return new_user

    async def get_user_by_clerk_id(self, clerk_id: str) -> Optional[User]:
        """Get user by Clerk ID"""
        database = await get_database()
        collection = database[self.collection_name]
        
        user_data = await collection.find_one({"clerk_id": clerk_id})
        if user_data:
            return User(**user_data)
        return None

    async def update_scrape_count(self, clerk_id: str) -> bool:
        """Increment user's scrape count"""
        database = await get_database()
        collection = database[self.collection_name]
        
        result = await collection.update_one(
            {"clerk_id": clerk_id},
            {
                "$inc": {"scrape_count": 1},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        return result.modified_count > 0

    async def can_user_scrape(self, clerk_id: str) -> bool:
        """Check if user can perform another scrape based on their plan"""
        user = await self.get_user_by_clerk_id(clerk_id)
        if not user:
            return False
        
        return user.scrape_count < user.monthly_scrape_limit

    async def create_scrape_job(self, job_data: dict) -> ScrapeJob:
        """Create a new scrape job record"""
        database = await get_database()
        collection = database[self.jobs_collection_name]
        
        scrape_job = ScrapeJob(
            **job_data,
            created_at=datetime.utcnow()
        )
        
        result = await collection.insert_one(scrape_job.dict(exclude={"id"}))
        scrape_job.id = result.inserted_id
        
        return scrape_job

    async def update_scrape_job(self, job_id: str, update_data: dict) -> bool:
        """Update scrape job status and data"""
        database = await get_database()
        collection = database[self.jobs_collection_name]
        
        update_data["updated_at"] = datetime.utcnow()
        
        result = await collection.update_one(
            {"job_id": job_id},
            {"$set": update_data}
        )
        
        return result.modified_count > 0

    async def get_user_scrape_jobs(self, clerk_id: str, limit: int = 50) -> List[ScrapeJob]:
        """Get user's scrape job history"""
        database = await get_database()
        collection = database[self.jobs_collection_name]
        
        cursor = collection.find(
            {"user_id": clerk_id}
        ).sort("created_at", -1).limit(limit)
        
        jobs = []
        async for job_data in cursor:
            jobs.append(ScrapeJob(**job_data))
        
        return jobs

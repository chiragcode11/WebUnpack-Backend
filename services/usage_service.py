from datetime import datetime
from database import get_database
from models import User, UserUsage

class UsageService:
    def __init__(self):
        self.single_page_limit = 25
        self.multi_page_limit = 10
        self.reactify_limit = 1

    async def get_user_usage(self, user_id: str) -> UserUsage:
        database = await get_database()
        collection = database["users"]
        
        user = await collection.find_one({"clerk_id": user_id})
        if not user:
            return UserUsage(
                single_page_used=0,
                multi_page_used=0,
                reactify_used=0,
                can_scrape_single=True,
                can_scrape_multi=True,
                can_reactify=True
            )
        
        single_used = user.get("single_page_count", 0)
        multi_used = user.get("multi_page_count", 0)
        reactify_used = user.get("reactify_count", 0)
        
        return UserUsage(
            single_page_used=single_used,
            multi_page_used=multi_used,
            reactify_used=reactify_used,
            single_page_limit=self.single_page_limit,
            multi_page_limit=self.multi_page_limit,
            reactify_limit=self.reactify_limit,
            can_scrape_single=single_used < self.single_page_limit,
            can_scrape_multi=multi_used < self.multi_page_limit,
            can_reactify=reactify_used < self.reactify_limit
        )

    async def can_user_scrape(self, user_id: str, scrape_mode: str) -> bool:
        usage = await self.get_user_usage(user_id)
        
        if scrape_mode == "single_page":
            return usage.can_scrape_single
        elif scrape_mode == "multi_page":
            return usage.can_scrape_multi
        
        return False

    async def can_user_reactify(self, user_id: str) -> bool:
        usage = await self.get_user_usage(user_id)
        return usage.can_reactify

    async def increment_usage(self, user_id: str, scrape_mode: str):
        database = await get_database()
        collection = database["users"]
        
        if scrape_mode == "single_page":
            await collection.update_one(
                {"clerk_id": user_id},
                {
                    "$inc": {"single_page_count": 1},
                    "$set": {"updated_at": datetime.utcnow()}
                },
                upsert=True
            )
        elif scrape_mode == "multi_page":
            await collection.update_one(
                {"clerk_id": user_id},
                {
                    "$inc": {"multi_page_count": 1},
                    "$set": {"updated_at": datetime.utcnow()}
                },
                upsert=True
            )

    async def increment_reactify_usage(self, user_id: str):
        database = await get_database()
        collection = database["users"]
        
        await collection.update_one(
            {"clerk_id": user_id},
            {
                "$inc": {"reactify_count": 1},
                "$set": {"updated_at": datetime.utcnow()}
            },
            upsert=True
        )

    async def decrement_usage(self, user_id: str, scrape_mode: str):
        database = await get_database()
        collection = database["users"]
        
        if scrape_mode == "single_page":
            await collection.update_one(
                {"clerk_id": user_id, "single_page_count": {"$gt": 0}},
                {"$inc": {"single_page_count": -1}}
            )
        elif scrape_mode == "multi_page":
            await collection.update_one(
                {"clerk_id": user_id, "multi_page_count": {"$gt": 0}},
                {"$inc": {"multi_page_count": -1}}
            )

    async def decrement_reactify_usage(self, user_id: str):
        database = await get_database()
        collection = database["users"]
        
        await collection.update_one(
            {"clerk_id": user_id, "reactify_count": {"$gt": 0}},
            {"$inc": {"reactify_count": -1}}
        )

usage_service = UsageService()

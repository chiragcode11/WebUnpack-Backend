from motor.motor_asyncio import AsyncIOMotorClient
from config import settings
import logging
import certifi
import os

os.environ['PYMONGO_DISABLE_PYOPENSSL'] = '1'

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    database = None

db = Database()

async def get_database():
    return db.database

async def connect_to_mongo():
    try:
        logger.info("Connecting to MongoDB...")
        db.client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            socketTimeoutMS=20000,
            tls=True,
            tlsCAFile=certifi.where()
        )
        
        await db.client.admin.command('ping')
        db.database = db.client[settings.DATABASE_NAME]
        logger.info("Successfully connected to MongoDB")
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise

async def close_mongo_connection():
    try:
        if db.client:
            db.client.close()
            logger.info("MongoDB connection closed")
    except Exception as e:
        logger.error(f"Error closing MongoDB connection: {e}")
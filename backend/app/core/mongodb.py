import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings

logger = logging.getLogger("vitalens.mongodb")

mongo_client: Optional[AsyncIOMotorClient] = None
mongo_db: Optional[AsyncIOMotorDatabase] = None

async def init_mongo() -> bool:
    """
    Initializes and validates connection to MongoDB Atlas.
    Safe: will not crash the app if the password has not yet been filled in.
    """
    global mongo_client, mongo_db

    url = settings.MONGODB_URL
    if not url:
        logger.info("MongoDB: No MONGODB_URL configured. MongoDB integration inactive.")
        return False

    # Check for unreplaced password placeholders
    if "<PASSWORD>" in url or "<YOUR_PASSWORD" in url or "<password>" in url:
        logger.warning(
            "MongoDB Atlas: Placeholder '<PASSWORD>' detected in MONGODB_URL. "
            "Please paste your MongoDB password in backend/.env to connect."
        )
        return False

    try:
        logger.info("Connecting to MongoDB Atlas...")
        mongo_client = AsyncIOMotorClient(
            url,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000
        )
        # Test connection with admin ping
        await mongo_client.admin.command('ping')
        mongo_db = mongo_client[settings.MONGODB_DB_NAME]
        logger.info(f">> Connected to MongoDB Atlas successfully! [DB: {settings.MONGODB_DB_NAME}]")
        return True
    except Exception as e:
        logger.error(f"MongoDB Atlas connection check failed: {e}")
        mongo_client = None
        mongo_db = None
        return False

async def close_mongo() -> None:
    """Closes MongoDB client connection on shutdown."""
    global mongo_client, mongo_db
    if mongo_client:
        mongo_client.close()
        logger.info("MongoDB Atlas connection closed.")
        mongo_client = None
        mongo_db = None

def get_mongo_client() -> Optional[AsyncIOMotorClient]:
    """Returns the active Motor MongoDB client instance."""
    return mongo_client

def get_mongo_db() -> Optional[AsyncIOMotorDatabase]:
    """Returns the active MongoDB database instance."""
    return mongo_db

async def check_mongo_health() -> dict:
    """Performs a live ping probe on MongoDB Atlas."""
    if not mongo_client:
        return {"status": "disconnected", "reason": "Client not initialized (check MONGODB_URL in .env)"}
    try:
        await mongo_client.admin.command('ping')
        return {"status": "connected", "database": settings.MONGODB_DB_NAME}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

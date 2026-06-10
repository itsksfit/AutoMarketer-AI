import os
import json
import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from bson.errors import InvalidId
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("automarketer")

# Configuration
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/automarketer")

class DatabaseError(Exception):
    """Custom exception for MongoDB related failures."""
    pass

# Global client and db
client = None
db = None

# Offline Mock DB Configuration
use_mock_db = False
mock_db_file = "campaigns_mock_db.json"

def load_mock_db() -> list:
    """Loads campaigns from the local JSON fallback file."""
    if os.path.exists(mock_db_file):
        try:
            with open(mock_db_file, "r") as f:
                data = json.load(f)
                # Convert date strings back to datetime
                for item in data:
                    if "created_at" in item:
                        item["created_at"] = datetime.fromisoformat(item["created_at"])
                return data
        except Exception as e:
            logger.error(f"Failed to read mock DB file: {str(e)}")
            return []
    return []

def save_mock_db(data: list):
    """Saves campaigns to the local JSON fallback file."""
    try:
        # Convert datetimes to ISO strings for JSON serialization
        serialized = []
        for item in data:
            copy_item = item.copy()
            if isinstance(copy_item.get("created_at"), datetime):
                copy_item["created_at"] = copy_item["created_at"].isoformat()
            serialized.append(copy_item)
            
        with open(mock_db_file, "w") as f:
            json.dump(serialized, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to write mock DB file: {str(e)}")

def get_db():
    """Initializes and returns the async MongoDB database instance."""
    global client, db
    if db is not None:
        return db
        
    try:
        logger.info(f"Initializing MongoDB Client with URI: {MONGODB_URI.split('@')[-1]}")
        client = AsyncIOMotorClient(MONGODB_URI, serverSelectionTimeoutMS=2000)
        db_name = "automarketer"
        from urllib.parse import urlparse
        try:
            parsed = urlparse(MONGODB_URI)
            url_db_name = parsed.path.lstrip('/')
            if url_db_name:
                db_name = url_db_name
        except Exception:
            pass
        db = client[db_name]
        return db
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        raise DatabaseError(f"Database connection failed: {str(e)}")

async def check_connection() -> bool:
    """Verifies that the MongoDB connection is alive. Activates local JSON fallback if offline."""
    global use_mock_db
    try:
        database = get_db()
        await database.command("ping")
        logger.info("MongoDB connection is healthy.")
        use_mock_db = False
        return True
    except Exception as e:
        logger.warning(f"MongoDB connection failed: {str(e)}. Switching to local JSON Mock Database fallback.")
        use_mock_db = True
        return True # Return True to allow application startup in Mock mode

async def check_duplicate_campaign(url: str, window_minutes: int = 5) -> Optional[dict]:
    """Checks if a campaign for the given URL was created within the last `window_minutes` minutes."""
    cutoff_time = datetime.utcnow() - timedelta(minutes=window_minutes)
    
    if use_mock_db:
        logger.info(f"[Mock DB] Checking duplicate for URL: {url}")
        db_data = load_mock_db()
        for doc in db_data:
            if doc.get("url") == url and doc.get("created_at") >= cutoff_time:
                logger.info(f"[Mock DB] Duplicate campaign found for URL: {url}")
                return doc
        return None
        
    try:
        database = get_db()
        query = {
            "url": url,
            "created_at": {"$gte": cutoff_time}
        }
        duplicate = await database.campaigns.find_one(query)
        if duplicate:
            duplicate["_id"] = str(duplicate["_id"])
            return duplicate
        return None
    except Exception as e:
        logger.error(f"Error checking duplicate campaigns: {str(e)}")
        raise DatabaseError(f"Database error during duplicate check: {str(e)}")

async def insert_campaign(campaign_data: dict) -> str:
    """Inserts a new campaign and returns its campaign ID."""
    if "created_at" not in campaign_data:
        campaign_data["created_at"] = datetime.utcnow()
        
    if use_mock_db:
        logger.info(f"[Mock DB] Inserting campaign for: {campaign_data.get('url')}")
        campaign_id = uuid.uuid4().hex[:24]
        campaign_data["_id"] = campaign_id
        
        db_data = load_mock_db()
        db_data.append(campaign_data)
        save_mock_db(db_data)
        return campaign_id
        
    try:
        database = get_db()
        result = await database.campaigns.insert_one(campaign_data)
        return str(result.inserted_id)
    except Exception as e:
        logger.error(f"Error inserting campaign: {str(e)}")
        raise DatabaseError(f"Database error during insert: {str(e)}")

async def get_all_campaigns() -> list:
    """Retrieves all campaigns sorted by newest first."""
    if use_mock_db:
        logger.info("[Mock DB] Fetching all campaigns history.")
        db_data = load_mock_db()
        # Sort by created_at descending
        db_data.sort(key=lambda x: x.get("created_at"), reverse=True)
        # Convert _id to string just in case
        for doc in db_data:
            doc["_id"] = str(doc["_id"])
        return db_data
        
    try:
        database = get_db()
        cursor = database.campaigns.find().sort("created_at", -1)
        campaigns = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            campaigns.append(doc)
        return campaigns
    except Exception as e:
        logger.error(f"Error fetching campaigns: {str(e)}")
        raise DatabaseError(f"Database error during list campaigns: {str(e)}")

async def get_campaign_by_id(campaign_id: str) -> Optional[dict]:
    """Retrieves a specific campaign by its ID string."""
    if use_mock_db:
        logger.info(f"[Mock DB] Fetching campaign by ID: {campaign_id}")
        db_data = load_mock_db()
        for doc in db_data:
            if str(doc.get("_id")) == campaign_id:
                return doc
        return None
        
    try:
        database = get_db()
        obj_id = ObjectId(campaign_id)
        doc = await database.campaigns.find_one({"_id": obj_id})
        if doc:
            doc["_id"] = str(doc["_id"])
            return doc
        return None
    except InvalidId:
        logger.warning(f"Invalid campaign ID format: {campaign_id}")
        return None
    except Exception as e:
        logger.error(f"Error fetching campaign by ID: {str(e)}")
        raise DatabaseError(f"Database error during fetch by ID: {str(e)}")

async def delete_campaign_by_id(campaign_id: str) -> bool:
    """Deletes a specific campaign by its ID string. Returns True if deleted, False otherwise."""
    if use_mock_db:
        logger.info(f"[Mock DB] Deleting campaign by ID: {campaign_id}")
        db_data = load_mock_db()
        original_length = len(db_data)
        db_data = [doc for doc in db_data if str(doc.get("_id")) != campaign_id]
        if len(db_data) < original_length:
            save_mock_db(db_data)
            return True
        return False
        
    try:
        database = get_db()
        obj_id = ObjectId(campaign_id)
        result = await database.campaigns.delete_one({"_id": obj_id})
        return result.deleted_count > 0
    except InvalidId:
        logger.warning(f"Invalid campaign ID format for deletion: {campaign_id}")
        return False
    except Exception as e:
        logger.error(f"Error deleting campaign by ID: {str(e)}")
        raise DatabaseError(f"Database error during deletion by ID: {str(e)}")


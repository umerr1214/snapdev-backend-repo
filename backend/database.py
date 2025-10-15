import os
import certifi
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Database:
    client: AsyncIOMotorClient = None
    database = None

# Database instance
db = Database()

async def get_database() -> AsyncIOMotorClient:
    """Get database instance"""
    return db.database

async def connect_to_mongo():
    """Create database connection"""
    try:
        ca = certifi.where()
        db.client = AsyncIOMotorClient(os.getenv("MONGODB_URL"), tlsCAFile=ca, appname="snapdev")
        db.database = db.client[os.getenv("DATABASE_NAME", "snapdev_portal")]
        
        # Test the connection
        await db.client.admin.command('ping')
        print("✅ Successfully connected to MongoDB Atlas!")
        
    except Exception as e:
        print(f"❌ Error connecting to MongoDB: {e}")
        raise e

async def close_mongo_connection():
    """Close database connection"""
    if db.client:
        db.client.close()
        print("🔌 Disconnected from MongoDB")

# Collections
def get_users_collection():
    """Get users collection"""
    return db.database.users

def get_projects_collection():
    """Get projects collection"""
    return db.database.projects

def get_sessions_collection():
    """Get sessions collection"""
    return db.database.sessions
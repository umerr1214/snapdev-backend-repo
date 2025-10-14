from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

from database import connect_to_mongo, close_mongo_connection, get_database
from routes import auth, hours, sheets, salary

# Load environment variables
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        await connect_to_mongo()
    except Exception as e:
        print(f"Warning: Could not connect to MongoDB: {e}")
        print("Server will start without database connection")
    yield
    # Shutdown
    try:
        await close_mongo_connection()
    except Exception as e:
        print(f"Warning: Error closing MongoDB connection: {e}")

# Create FastAPI app
app = FastAPI(
    title="SnapDev Portal API",
    description="Backend API for SnapDev Portal - Admin Only",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Admin Authentication"])
app.include_router(hours.router, prefix="/api/hours", tags=["Client Hours"])
app.include_router(sheets.router, prefix="/api/sheets", tags=["Google Sheets"])
app.include_router(salary.router, prefix="/api/salary", tags=["Salary Calculator"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to SnapDev Portal API - Admin Panel",
        "version": "1.0.0",
        "status": "running",
        "access": "admin_only"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        db = await get_database()
        # Test database connection
        await db.command('ping')
        return {
            "status": "healthy",
            "database": "connected",
            "message": "All systems operational"
        }
    except Exception as e:
        return {
            "status": "healthy",
            "database": "disconnected",
            "message": f"Server running but database unavailable: {str(e)}"
        }

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )
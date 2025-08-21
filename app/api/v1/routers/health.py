from datetime import datetime
from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.api.deps import get_db
from app.api.v1.schemas import HealthResponse

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/", response_model=HealthResponse, summary="Health check")
async def health_check():
    """Basic health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow()
    )


@router.get("/ready", response_model=HealthResponse, summary="Readiness check")
async def readiness_check(db: AsyncIOMotorDatabase = Depends(get_db)):
    """Readiness check that verifies database connectivity."""
    try:
        # Test database connection
        await db.command("ping")
        return HealthResponse(
            status="ready",
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        return HealthResponse(
            status=f"not ready: {str(e)}",
            timestamp=datetime.utcnow()
        ) 
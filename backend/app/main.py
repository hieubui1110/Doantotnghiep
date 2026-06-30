import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import engine, Base, AsyncSessionLocal
from app.api.v1.router import api_router
from app.core.security import get_password_hash
from app.models.operator import Operator
from sqlalchemy.future import select

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to DB and auto-create tables if they don't exist
    print("[*] Starting application lifespan...")
    async with engine.begin() as conn:
        # Create all tables if not exists
        await conn.run_sync(Base.metadata.create_all)
        print("[+] Database tables initialized.")

    # Seed admin user if it does not exist
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(select(Operator).filter(Operator.username == "admin"))
            admin_user = result.scalars().first()
            
            if not admin_user:
                print("[*] Seeding default admin user...")
                hashed_pw = get_password_hash("admin123")
                admin = Operator(
                    username="admin",
                    email="admin@traffic.local",
                    hashed_password=hashed_pw,
                    full_name="System Administrator",
                    role="admin",
                    is_active=True
                )
                session.add(admin)
                await session.commit()
                print("[+] Default admin user seeded successfully (username: 'admin', password: 'admin123').")
            else:
                print("[+] Admin user already exists. Skipping seed.")
        except Exception as e:
            print(f"[-] Error seeding database: {e}")
            await session.rollback()

    yield
    # Shutdown
    await engine.dispose()
    print("[-] Application shutdown complete.")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="FastAPI Backend for Smart Traffic Monitoring System",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static folder for serving violation evidence images
evidence_dir = "static/evidence"
os.makedirs(evidence_dir, exist_ok=True)
app.mount("/evidence", StaticFiles(directory="static/evidence"), name="evidence")

# Include routers - mount under both /api and /api/v1 for maximum client compatibility
app.include_router(api_router, prefix="/api")
app.include_router(api_router, prefix="/api/v1")

@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "online",
        "system": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "version": settings.APP_VERSION
    }

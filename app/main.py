from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app.routes import auth, items, borrow_request
from app.models import user, item
from app.models import borrow_request as borrow_request_model
from app.routes import dashboard
from app.routes import admin
from app.config import settings

Base.metadata.create_all(bind=engine)

app = FastAPI(title="UniLend API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.CORS_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(items.router)
app.include_router(borrow_request.router)
app.include_router(dashboard.router)
app.include_router(admin.router)

@app.get("/")
def root():
    return {"message": "UniLend API is running"}
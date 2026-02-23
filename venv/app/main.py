from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from app.core.database import Base, engine
from app.core.exception_handler import (
    http_exception_handler,
    validation_exception_handler
)

# Import models so tables are created
from app.models import user, document, document_status_history

# Import routers
from app.routes import auth
from app.routes import document as document_route


app = FastAPI(
    title="Document Management API",
    description="Secure Document Management System with RBAC, Background Tasks, Filtering & Pagination",
    version="2.0.0",
    contact={
        "name": "Rajesh",
        "email": "rajesh@example.com"
    }
)

# ---------------- CORS ---------------- #

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- EXCEPTION HANDLERS ---------------- #

app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# ---------------- CREATE TABLES ---------------- #

Base.metadata.create_all(bind=engine)

# ---------------- INCLUDE ROUTERS ---------------- #

app.include_router(auth.router)
app.include_router(document_route.router)

# ---------------- ROOT ENDPOINT ---------------- #

@app.get("/")
def home():
    return {"message": "API Running Successfully"}

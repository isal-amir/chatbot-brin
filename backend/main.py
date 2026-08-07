from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta

from core.database import Base, engine, get_db
from models.user import User
from services.qdrant_service import init_qdrant, search_documents
from services.llm_service import generate_embedding, generate_response

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
JWT_SECRET = "super-secret-mock-key"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Qdrant collection
    try:
        await init_qdrant()
    except Exception as e:
        print(f"Could not connect to Qdrant on startup: {e}")
        
    # Startup: Initialize PostgreSQL and create mock user
    try:
        Base.metadata.create_all(bind=engine)
        db = next(get_db())
        if not db.query(User).filter(User.username == "student").first():
            hashed_pwd = pwd_context.hash("password123")
            new_user = User(username="student", hashed_password=hashed_pwd)
            db.add(new_user)
            db.commit()
            print("Mock user 'student' created.")
    except Exception as e:
        print(f"Could not connect to PostgreSQL on startup: {e}")
        
    yield
    # Shutdown 

app = FastAPI(title="Hermeneutic AI Tutor API", lifespan=lifespan)

# Allow CORS for local Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://192.168.1.209:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    query: str
    chat_history: str = "" # Optional formatted chat history

class ChatResponse(BaseModel):
    response: str

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    token: str

@app.get("/")
async def root():
    return {"message": "Welcome to the Hermeneutic AI Tutor API"}

@app.post("/auth/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == request.username).first()
    if not user or not pwd_context.verify(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Create simple JWT
    expire = datetime.utcnow() + timedelta(days=7)
    token = jwt.encode({"sub": user.username, "exp": expire}, JWT_SECRET, algorithm="HS256")
    return LoginResponse(token=token)

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    if not request.query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    try:
        # 1. Generate embedding for the user query
        query_vector = await generate_embedding(request.query)
        
        # 2. Retrieve relevant context from Qdrant
        context = await search_documents(query_vector)
        
        # 3. Generate response using LLM with hermeneutic prompt
        llm_response = await generate_response(
            query=request.query, 
            context=context, 
            chat_history=request.chat_history
        )
        
        return ChatResponse(response=llm_response)
        
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
from typing import List, Optional

from core.database import Base, engine, get_db
from models.user import User
from models.chat import ChatSession, ChatMessage
from services.qdrant_service import init_qdrant, search_documents
from services.llm_service import generate_embedding, generate_response

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
JWT_SECRET = "super-secret-mock-key"

def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        username = payload.get("sub")
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

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
    session_id: Optional[int] = None

class ChatResponse(BaseModel):
    response: str
    session_id: int

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    token: str

class MessageSchema(BaseModel):
    role: str
    content: str
    created_at: datetime

    class Config:
        orm_mode = True

class SessionSchema(BaseModel):
    id: int
    title: str
    created_at: datetime

    class Config:
        orm_mode = True

class SessionDetailSchema(SessionSchema):
    messages: List[MessageSchema]

class UpdateSessionRequest(BaseModel):
    title: str

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
async def chat_endpoint(request: ChatRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not request.query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    try:
        # Create or fetch session
        if request.session_id:
            session = db.query(ChatSession).filter(ChatSession.id == request.session_id, ChatSession.user_id == user.id).first()
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
        else:
            # Generate a title for the session based on the first query
            title = request.query[:30] + "..." if len(request.query) > 30 else request.query
            session = ChatSession(user_id=user.id, title=title)
            db.add(session)
            db.commit()
            db.refresh(session)
        
        # Save user message
        user_msg = ChatMessage(session_id=session.id, role="user", content=request.query)
        db.add(user_msg)
        db.commit()

        # Build chat history from previous messages
        past_messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session.id,
            ChatMessage.id != user_msg.id # exclude the one we just inserted
        ).order_by(ChatMessage.created_at.asc()).limit(10).all()
        
        chat_history_str = ""
        for msg in past_messages:
            prefix = "User: " if msg.role == "user" else "AI: "
            chat_history_str += f"{prefix}{msg.content}\n"

        # 1. Generate embedding for the user query
        query_vector = await generate_embedding(request.query)
        
        # 2. Retrieve relevant context from Qdrant
        context = await search_documents(query_vector)
        
        # 3. Generate response using LLM with hermeneutic prompt
        llm_response = await generate_response(
            query=request.query, 
            context=context, 
            chat_history=chat_history_str
        )
        
        # Save AI message
        ai_msg = ChatMessage(session_id=session.id, role="ai", content=llm_response)
        db.add(ai_msg)
        db.commit()

        return ChatResponse(response=llm_response, session_id=session.id)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/sessions", response_model=List[SessionSchema])
def get_sessions(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sessions = db.query(ChatSession).filter(ChatSession.user_id == user.id).order_by(ChatSession.created_at.desc()).all()
    return sessions

@app.post("/sessions", response_model=SessionSchema)
def create_session(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session = ChatSession(user_id=user.id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

@app.get("/sessions/{session_id}", response_model=SessionDetailSchema)
def get_session(session_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@app.put("/sessions/{session_id}", response_model=SessionSchema)
def update_session(session_id: int, req: UpdateSessionRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.title = req.title
    db.commit()
    db.refresh(session)
    return session

@app.delete("/sessions/{session_id}")
def delete_session(session_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(session)
    db.commit()
    return {"message": "Session deleted"}

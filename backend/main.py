from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager

from services.qdrant_service import init_qdrant, search_documents
from services.llm_service import generate_embedding, generate_response

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Qdrant collection
    try:
        await init_qdrant()
    except Exception as e:
        print(f"Could not connect to Qdrant on startup: {e}")
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

@app.get("/")
async def root():
    return {"message": "Welcome to the Hermeneutic AI Tutor API"}

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

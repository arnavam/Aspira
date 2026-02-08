
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
import logging
import tempfile
import os

from database import Database
from auth import verify_password, get_password_hash, create_access_token, ALGORITHM, SECRET_KEY, jwt, JWTError

# LangGraph checkpointer (in-memory for temporary storage)
from langgraph.checkpoint.memory import MemorySaver

# Initialize Database (only for auth now)
db = Database()

# Initialize MemorySaver for session state
memory = MemorySaver()

# Initialize API
app = FastAPI(title="Aspira Groq API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth Scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Pydantic Models
class UserCreate(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class ChatRequest(BaseModel):
    message: str

class ResumeRequest(BaseModel):
    content: str

# Store resume content per user (in-memory)
user_resumes: Dict[str, str] = {}

from logger_config import get_logger

# Logger
logger = get_logger(__name__)

# --- Dependencies ---
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.get_user(username)
    if user is None:
        raise credentials_exception
    
    return str(user["_id"])

# --- Auth Routes ---

@app.get("/")
async def check_health():
    return {"status": "ok"}

@app.post("/register", response_model=Token)
async def register(user: UserCreate):
    existing_user = db.get_user(user.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    hashed_password = get_password_hash(user.password)
    user_id = db.create_user(user.username, hashed_password)
    
    if not user_id:
        raise HTTPException(status_code=500, detail="Database error during registration")
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = db.get_user(form_data.username)
    if not user or not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

# --- Chat Routes ---

@app.post("/resume")
async def upload_resume(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user)
):
    """
    Upload and parse resume file using LlamaIndex.
    Supports PDF, DOCX, TXT, MD, HTML, RTF formats.
    """
    try:
        from llama_index.core import SimpleDirectoryReader
        
        # Save uploaded file to temp directory
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, file.filename)
            
            # Write uploaded file
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)
            
            # Parse with LlamaIndex
            reader = SimpleDirectoryReader(input_files=[file_path])
            documents = reader.load_data()
            
            # Combine all document text
            text = "\n".join([doc.text for doc in documents if doc.text])
        
        # Truncate if too long
        max_length = 10000  # ~2500 tokens
        text = text[:max_length] if len(text) > max_length else text
        
        # Store for this user
        user_resumes[user_id] = text
        
        logger.info(f"Resume stored for user {user_id}: {len(text)} chars from {file.filename}")
        return {"message": "Resume processed successfully", "chars": len(text), "filename": file.filename}
        
    except Exception as e:
        logger.error(f"Error processing resume: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat")
async def chat(request: ChatRequest, user_id: str = Depends(get_current_user)):
    """
    Main chat endpoint using LangGraph with MemorySaver.
    Session state is stored in-memory per user (thread_id).
    """
    from aspira import create_workflow, AgentState
    
    # Create workflow with checkpointer
    workflow = create_workflow()
    app_with_memory = workflow.compile(checkpointer=memory)
    
    # Include resume context if available
    history = []
    if user_id in user_resumes:
        resume_context = f"[RESUME CONTEXT]: {user_resumes[user_id]}"
        history.append(resume_context)
    
    # Add user message to history
    history.append(f"User: {request.message}")
    
    # Build initial state
    state: AgentState = {
        # Persistent (managed by checkpointer)
        "keywords": {},
        "history": history,
        "user_id": user_id,
        # Ephemeral (per-request)
        "question": "",
        "search_queries": [],
        "scraped_content": {},
        "question_scores": {}
    }
    
    # Config with thread_id for multi-user isolation
    config = {"configurable": {"thread_id": user_id}}
    
    try:
        # Run workflow (checkpointer handles state persistence)
        result = app_with_memory.invoke(state, config)
        
        response_question = result.get("question", "Could you tell me more?")
        return {"response": response_question}
        
    except Exception as e:
        logger.error(f"Error in chat processing: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


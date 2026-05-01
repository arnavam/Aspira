
from logger_config import get_logger
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

# Initialize Database (only for auth now)
db = Database()


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
    conversation_id: str = "default"


class ResumeRequest(BaseModel):
    content: str


# Store resume content per user (in-memory)
user_resumes: Dict[str, str] = {}


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
        raise HTTPException(
            status_code=500, detail="Database error during registration")

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


@app.get("/conversations")
async def get_conversations(user_id: str = Depends(get_current_user)):
    """Get a list of all conversation IDs for the user."""
    conversations = db.get_conversations(user_id)
    valid_conversations = [c for c in conversations if c]
    if not valid_conversations:
        return {"conversations": ["default"]}
    return {"conversations": valid_conversations}


@app.get("/conversations/{conversation_id}/history")
async def get_history(conversation_id: str, user_id: str = Depends(get_current_user)):
    """Get the full history of a specific conversation."""
    history = db.get_conversation_history(user_id, conversation_id)
    # Parse history into roles for frontend
    parsed_history = []
    for msg in history:
        if msg.startswith("[RESUME CONTEXT]"):
            continue
        if msg.startswith("User: "):
            parsed_history.append({"role": "user", "content": msg[6:]})
        elif msg.startswith("Interviewer: "):
            parsed_history.append({"role": "assistant", "content": msg[13:]})
        else:
            parsed_history.append({"role": "assistant", "content": msg})
    return {"history": parsed_history}


@app.get("/dashboard/{conversation_id}")
async def get_dashboard_data(conversation_id: str, user_id: str = Depends(get_current_user)):
    """Fetch analytics and keyword scores for a specific conversation dashboard."""
    keywords = db.get_keywords(user_id, conversation_id)
    # keywords is a dict {keyword: [score, similarity]}

    # Format for easy frontend consumption
    formatted_keywords = [{"keyword": k, "score": v[0], "similarity": v[1]}
                          for k, v in keywords.items() if isinstance(v, list) and len(v) == 2]
    formatted_keywords.sort(
        key=lambda x: x["score"] * x["similarity"], reverse=True)

    # Grab history to count messages
    history = db.get_conversation_history(user_id, conversation_id)
    user_messages = [msg for msg in history if msg.startswith("User: ")]

    return {
        "metrics": {
            "total_questions": len([msg for msg in history if msg.startswith("Interviewer: ")]),
            "total_responses": len(user_messages),
        },
        "keywords": formatted_keywords
    }


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

        # Store for this user in DB
        db.save_resume(user_id, text)

        logger.info(f"""Resume stored for user {user_id}: {
                    len(text)} chars from {file.filename}""")
        return {"message": "Resume processed successfully", "chars": len(text), "filename": file.filename}

    except Exception as e:
        logger.error(f"Error processing resume: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat")
def chat(request: ChatRequest, user_id: str = Depends(get_current_user)):
    """
    Main chat endpoint. Session state is stored in MongoDB.
    """
    from aspira import create_workflow, AgentState

    conversation_id = request.conversation_id

    # Load history from DB
    history = db.get_conversation_history(user_id, conversation_id)

    # Load resume from DB
    resume = db.get_resume(user_id)
    if resume and not any("[RESUME CONTEXT]" in msg for msg in history):
        history.insert(0, f"[RESUME CONTEXT]: {resume}")

    # Save and append the new user message
    db.add_conversation_message(
        user_id, f"User: {request.message}", conversation_id)
    history.append(f"User: {request.message}")

    # Load keywords from DB
    keywords = db.get_keywords(user_id, conversation_id)

    # Create workflow
    workflow = create_workflow()
    app_without_memory = workflow.compile()

    # Build initial state
    state: AgentState = {
        "keywords": keywords,
        "history": history,
        "user_id": user_id,
        "question": "",
        "search_queries": [],
        "scraped_content": {},
        "relevant_chunks": [],
        "question_scores": {},
            "no_keywords": 1,
    "no_links": 1,
    "no_chunks": 1

    }

    try:
        # Run workflow
        result = app_without_memory.invoke(state)

        # Get response question
        response_question = result.get("question")

        # Save interviewer response to DB
        db.add_conversation_message(user_id, f'''Interviewer: {
                                    response_question}''', conversation_id)

        # Save updated keywords
        new_keywords = result.get("keywords", {})
        if new_keywords:
            db.update_keywords(user_id, new_keywords, conversation_id)

        return {"response": response_question}

    except Exception as e:
        logger.error(f"Error in chat processing: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

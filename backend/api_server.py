from logger_config import get_logger
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
import tempfile
import os
import json
import asyncio
from fastapi.responses import FileResponse
from groq import Groq
import edge_tts
from typing import Dict
from database import Database
from auth import (verify_password, get_password_hash, create_access_token,
                  ALGORITHM, SECRET_KEY, jwt, JWTError)

# Initialize Database
db = Database()

# Initialize API
app = FastAPI(title="Aspira Backend API")


@app.on_event("startup")
async def startup_db_client():
    await db.initialize()

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
    force_end: bool = False


class SetupRequest(BaseModel):
    conversation_id: str = "default"
    company: str = ""
    role: str = ""
    requirements: str = ""


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

    user = await db.get_user(username)
    if user is None:
        raise credentials_exception

    return str(user["_id"])

# --- Auth Routes ---


@app.get("/")
async def check_health():
    return {"status": "ok"}


@app.post("/register", response_model=Token)
async def register(user: UserCreate):
    existing_user = await db.get_user(user.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    hashed_password = get_password_hash(user.password)
    user_id = await db.create_user(user.username, hashed_password)

    if not user_id:
        raise HTTPException(
            status_code=500, detail="Database error during registration")

    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await db.get_user(form_data.username)
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
    conversations = await db.get_conversations(user_id)
    valid_conversations = [c for c in conversations if c]
    if not valid_conversations:
        return {"conversations": ["default"]}
    return {"conversations": valid_conversations}


@app.get("/conversations/{conversation_id}/history")
async def get_history(conversation_id: str, user_id: str = Depends(get_current_user)):
    """Get the full history of a specific conversation."""
    history = await db.get_conversation_history(user_id, conversation_id)
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
    evaluation = await db.get_evaluation(user_id, conversation_id)
    metadata = await db.get_interview_metadata(user_id, conversation_id)
    
    # Strictly consider it ended ONLY if there's a final overall_score or grades.
    is_ended = bool(evaluation and "overall_score" in evaluation)
    
    return {
        "history": parsed_history, 
        "is_ended": is_ended,
        "metadata": metadata
    }


@app.post("/setup_interview")
async def setup_interview(request: SetupRequest, user_id: str = Depends(get_current_user)):
    """Save metadata for a new interview session."""
    metadata = {
        "company": request.company,
        "role": request.role,
        "requirements": request.requirements
    }
    await db.save_interview_metadata(user_id, request.conversation_id, metadata)
    return {"message": "Interview metadata saved successfully."}


@app.get("/dashboard/{conversation_id}")
async def get_dashboard_data(conversation_id: str, user_id: str = Depends(get_current_user)):
    """Fetch analytics, keyword scores, and evaluation for a specific conversation dashboard."""
    # Fetch keywords
    keywords = await db.get_keywords(user_id, conversation_id)
    
    # Calculate a normalized final score [0, 1] for each keyword
    formatted_keywords = []
    if keywords:
        # Find max frequency score for normalization
        max_freq = max([v[0] for v in keywords.values() if isinstance(v, list) and len(v) == 2] or [1.0])
        
        for k, v in keywords.items():
            if isinstance(v, list) and len(v) == 2:
                freq_score = v[0]
                sim_score = v[1]
                
                # Normalize frequency relative to max in session (0.0 to 1.0)
                norm_freq = freq_score / max_freq if max_freq > 0 else 0
                
                # Combine: 40% frequency weight, 60% similarity weight
                # This ensures the score is always <= 1.0
                final_score = (norm_freq * 0.4) + (sim_score * 0.6)
                
                formatted_keywords.append({
                    "keyword": k, 
                    "score": round(final_score, 2),
                    "original_freq": round(freq_score, 2),
                    "similarity": round(sim_score, 2)
                })

    formatted_keywords.sort(key=lambda x: x["score"], reverse=True)

    # Grab history to count messages
    history = await db.get_conversation_history(user_id, conversation_id)
    user_messages = [msg for msg in history if msg.startswith("User: ")]

    # Grab evaluation
    evaluation = await db.get_evaluation(user_id, conversation_id)
    if not evaluation and history:
        try:
            from I_evaluation import evaluate_interview
            metadata = await db.get_interview_metadata(user_id, conversation_id)
            evaluation = await evaluate_interview(history, {}, metadata)
            await db.save_evaluation(user_id, conversation_id, evaluation)
        except Exception as e:
            logger.error(f"Failed to generate evaluation on the fly: {e}", exc_info=True)

    return {
        "metrics": {
            "total_questions": len([msg for msg in history if msg.startswith("Interviewer: ")]),
            "total_responses": len(user_messages),
        },
        "keywords": formatted_keywords,
        "evaluation": evaluation,
        "history": history
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
            def load_docs():
                reader = SimpleDirectoryReader(input_files=[file_path])
                return reader.load_data()

            documents = await asyncio.to_thread(load_docs)

            # Combine all document text
            text = "\n".join([doc.text for doc in documents if doc.text])

        # Truncate if too long
        max_length = 10000  # ~2500 tokens
        text = text[:max_length] if len(text) > max_length else text

        # Store for this user in DB
        await db.save_resume(user_id, text)

        logger.info(f"Resume stored for user {user_id}: {
                    len(text)} chars from {file.filename}")
        return {"message": "Resume processed successfully", "chars": len(text), "filename": file.filename}

    except Exception as e:
        logger.error(f"Error processing resume: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...), user_id: str = Depends(get_current_user)):
    """Transcribe audio using Groq's Whisper API."""
    try:
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        audio_bytes = await file.read()

        # Groq API expects a tuple (filename, bytes)
        transcription = await asyncio.to_thread(
            client.audio.transcriptions.create,
            file=(file.filename, audio_bytes),
            model="whisper-large-v3",
            language="en"
        )
        return {"text": transcription.text}
    except Exception as e:
        logger.error(f"Transcription error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tts")
async def generate_tts(text: str):
    """Generate Text-to-Speech using edge-tts."""
    try:
        communicate = edge_tts.Communicate(text, "en-US-AriaNeural")

        # We need a temp file that persists just long enough to be sent
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tmp_file.close()

        await communicate.save(tmp_file.name)

        return FileResponse(
            tmp_file.name,
            media_type="audio/mpeg",
            filename="response.mp3",
            # FastAPI's FileResponse doesn't auto-delete the file after sending by default.
            # We'll use a BackgroundTask to delete it, but for simplicity here we just return it.
            # Using background parameter requires Starlette BackgroundTask.
        )
    except Exception as e:
        logger.error(f"TTS error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat")
async def chat(request: ChatRequest, user_id: str = Depends(get_current_user)):
    """
    Main chat endpoint. Session state is stored in MongoDB.
    Returns Server-Sent Events (SSE) representing LangGraph node updates and final output.
    """
    from aspira import create_workflow, AgentState

    conversation_id = request.conversation_id

    # Load history from DB
    history = await db.get_conversation_history(user_id, conversation_id)

    # Load resume from DB
    resume = await db.get_resume(user_id)
    if resume and not any("[RESUME CONTEXT]" in msg for msg in history):
        history.insert(0, f"[RESUME CONTEXT]: {resume}")

    # Save and append the new user message
    if request.message.strip():
        await db.add_conversation_message(
            user_id, f"User: {request.message}", conversation_id)
        history.append(f"User: {request.message}")

    # Load keywords and metadata from DB
    keywords = await db.get_keywords(user_id, conversation_id)
    metadata = await db.get_interview_metadata(user_id, conversation_id)

    async def event_generator():
        try:
            if request.force_end:
                from I_evaluation import evaluate_interview
                eval_data = await evaluate_interview(history, {}, metadata)
                await db.save_evaluation(user_id, conversation_id, eval_data)
                yield {"event": "evaluation", "data": json.dumps(eval_data)}
                yield {"event": "end", "data": "Stream finished"}
                return

            # Handle first question request (empty message, no user history)
            is_first_message = not request.message.strip() and not any(msg.startswith("User: ") for msg in history)
            if is_first_message:
                company = metadata.get("company", "").strip()
                role = metadata.get("role", "").strip()
                
                greeting = "Hello! Welcome to your interview session. I'm Aspira, your AI interviewer."
                if role:
                    greeting += f" I'll be evaluating you for the {role} position"
                    if company:
                        greeting += f" at {company}."
                    else:
                        greeting += "."
                else:
                    greeting += " I'll be asking you some questions to understand your background and skills better."
                
                greeting += " Let's start - could you tell me a bit about yourself and your relevant experience?"
                
                await db.add_conversation_message(user_id, f"Interviewer: {greeting}", conversation_id)
                yield {"event": "question", "data": json.dumps({"response": greeting})}
                yield {"event": "end", "data": "Stream finished"}
                return

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
                "no_chunks": 1,
                "answer_stats": {},
                "is_interview_complete": False,
                "interview_metadata": metadata
            }

            # Stream events as nodes complete
            async for event in app_without_memory.astream(state, stream_mode="updates"):
                for node_name, state_update in event.items():
                    # Send an update event
                    yield {"event": "update", "data": json.dumps({"node": node_name, "status": "completed"})}

                    if node_name == "respond":
                        response_question = state_update.get("question")

                        # Save interviewer response to DB
                        await db.add_conversation_message(
                            user_id, f"Interviewer: {response_question}", conversation_id)

                        # Save updated keywords
                        new_keywords = state_update.get("keywords", {})
                        if new_keywords:
                            await db.update_keywords(user_id, new_keywords, conversation_id)

                        # Send final question
                        yield {"event": "question", "data": json.dumps({"response": response_question})}

                    # AI-driven termination handling
                    if node_name == "query_generation" and state_update.get("is_interview_complete"):
                        from I_evaluation import evaluate_interview
                        eval_data = await evaluate_interview(history, state_update.get("answer_stats", {}), metadata)
                        await db.save_evaluation(user_id, conversation_id, eval_data)
                        yield {"event": "evaluation", "data": json.dumps(eval_data)}

            yield {"event": "end", "data": "Stream finished"}
        except Exception as e:
            logger.error(f"Error in chat processing: {e}", exc_info=True)
            yield {"event": "error", "data": str(e)}

    return EventSourceResponse(event_generator())

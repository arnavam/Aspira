"""
Aspira - AI Interview Assistant
Streamlit Frontend with Native Chat UI and Resume Upload
"""

import streamlit as st
import requests
from typing import Optional


# --- Configuration ---
st.set_page_config(
    page_title="Aspira - AI Interview Assistant",
    page_icon="✨",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for Modern Design ---
st.markdown("""
<style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    .stApp {
        font-family: 'Inter', sans-serif;
    }
    
    /* Header Styling */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem 2rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
    }
    
    .main-header h1 {
        color: white;
        font-weight: 700;
        margin: 0;
        font-size: 2rem;
    }
    
    .main-header p {
        color: rgba(255, 255, 255, 0.9);
        margin: 0.25rem 0 0 0;
        font-size: 1rem;
    }
    
    /* Resume Card */
    .resume-card {
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        border: 2px dashed #0ea5e9;
        border-radius: 12px;
        padding: 1rem;
        margin: 1rem 0;
        text-align: center;
    }
    
    .resume-success {
        background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
        border: 2px solid #22c55e;
        border-radius: 12px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    /* Auth Card */
    .auth-card {
        background: white;
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        border: 1px solid #e2e8f0;
    }
    
    /* Button Styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    
    /* Input Styling */
    .stTextInput > div > div > input {
        border-radius: 12px;
        border: 2px solid #e2e8f0;
        padding: 0.75rem 1rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Chat input styling */
    .stChatInput > div {
        border-radius: 24px !important;
        border: 2px solid #e2e8f0 !important;
    }
    
    .stChatInput > div:focus-within {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e1e2e 0%, #2d2d44 100%);
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: #e2e8f0;
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Chat message avatars */
    .stChatMessage [data-testid="chatAvatarIcon-user"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .stChatMessage [data-testid="chatAvatarIcon-assistant"] {
        background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
    }
</style>
""", unsafe_allow_html=True)


# --- Session State Initialization ---
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "username" not in st.session_state:
    st.session_state.username = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "resume_content" not in st.session_state:
    st.session_state.resume_content = None
if "resume_uploaded" not in st.session_state:
    st.session_state.resume_uploaded = False
if "interview_started" not in st.session_state:
    st.session_state.interview_started = False
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = "default"
if "current_view" not in st.session_state:
    st.session_state.current_view = "Interview"
if "conversations_list" not in st.session_state:
    st.session_state.conversations_list = ["default"]


# --- API Configuration ---
API_BASE_URL = st.sidebar.text_input(
    "API URL", 
    value="http://localhost:8000",
    help="Base URL of the Aspira API server"
)


# --- API Helper Functions ---
def check_api_health() -> bool:
    """Check if the API server is running."""
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False


def register_user(username: str, password: str) -> tuple[bool, str]:
    """Register a new user."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/register",
            json={"username": username, "password": password},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            return True, data.get("access_token", "")
        else:
            error = response.json().get("detail", "Registration failed")
            return False, error
    except requests.RequestException as e:
        return False, str(e)


def login_user(username: str, password: str) -> tuple[bool, str]:
    """Login an existing user."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/token",
            data={"username": username, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            return True, data.get("access_token", "")
        else:
            error = response.json().get("detail", "Login failed")
            return False, error
    except requests.RequestException as e:
        return False, str(e)


def send_resume_to_backend(uploaded_file, token: str) -> tuple[bool, str]:
    """Send resume file directly to the backend for parsing."""
    try:
        # Reset file pointer to beginning
        uploaded_file.seek(0)
        
        # Send file as multipart form data
        files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
        response = requests.post(
            f"{API_BASE_URL}/resume",
            files=files,
            headers={"Authorization": f"Bearer {token}"},
            timeout=60  # Longer timeout for file processing
        )
        if response.status_code == 200:
            data = response.json()
            return True, data.get("message", "Resume processed successfully")
        else:
            error = response.json().get("detail", "Resume processing failed")
            return False, error
    except requests.RequestException as e:
        return False, str(e)


def send_chat_message(message: str, token: str, conversation_id: str) -> tuple[bool, str]:
    """Send a chat message to the API."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/chat",
            json={"message": message, "conversation_id": conversation_id},
            headers={"Authorization": f"Bearer {token}"},
            timeout=60  # Longer timeout for AI processing
        )
        if response.status_code == 200:
            data = response.json()
            return True, data.get("response", "No response received")
        else:
            error = response.json().get("detail", "Chat request failed")
            return False, error
    except requests.RequestException as e:
        return False, str(e)

def fetch_conversations(token: str) -> list:
    """Fetch user's conversation IDs."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/conversations",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        if response.status_code == 200:
            return response.json().get("conversations", ["default"])
    except:
        pass
    return ["default"]

def load_conversation_history(conversation_id: str, token: str) -> list:
    """Fetch full history for a conversation."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/conversations/{conversation_id}/history",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        if response.status_code == 200:
            return response.json().get("history", [])
    except:
        pass
    return []

def fetch_dashboard_data(conversation_id: str, token: str) -> dict:
    """Fetch metrics and keyword scores for a conversation."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/dashboard/{conversation_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return {"metrics": {}, "keywords": []}


# --- UI Components ---
def render_header():
    """Render the main header."""
    st.markdown("""
    <div class="main-header">
        <h1>✨ Aspira</h1>
        <p>Your AI-Powered Interview Assistant</p>
    </div>
    """, unsafe_allow_html=True)


def render_api_status():
    """Render API connection status in sidebar."""
    is_connected = check_api_health()
    if is_connected:
        st.sidebar.success("🟢 API Connected")
    else:
        st.sidebar.error("🔴 API Disconnected")
    return is_connected


def render_auth_section():
    """Render the authentication section."""
    st.markdown("### 🔐 Authentication")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        with st.form("login_form"):
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Login", use_container_width=True)
            
            if submitted:
                if username and password:
                    with st.spinner("Authenticating..."):
                        success, result = login_user(username, password)
                    if success:
                        st.session_state.access_token = result
                        st.session_state.username = username
                        st.success("✅ Login successful!")
                        st.rerun()
                    else:
                        st.error(f"❌ {result}")
                else:
                    st.warning("Please enter both username and password")
    
    with tab2:
        with st.form("register_form"):
            username = st.text_input("Username", key="register_username")
            password = st.text_input("Password", type="password", key="register_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
            submitted = st.form_submit_button("Register", use_container_width=True)
            
            if submitted:
                if username and password and confirm_password:
                    if password != confirm_password:
                        st.error("Passwords do not match!")
                    elif len(password) < 6:
                        st.warning("Password should be at least 6 characters")
                    else:
                        with st.spinner("Creating account..."):
                            success, result = register_user(username, password)
                        if success:
                            st.session_state.access_token = result
                            st.session_state.username = username
                            st.success("✅ Registration successful!")
                            st.rerun()
                        else:
                            st.error(f"❌ {result}")
                else:
                    st.warning("Please fill in all fields")


def render_resume_upload():
    """Render the resume upload section."""
    st.markdown("### 📄 Upload Your Resume")
    st.markdown("*Upload your resume to personalize the interview experience*")
    
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=["docx", "pdf", "txt", "doc", "md", "html", "rtf"],
        help="Supported formats: .docx, .pdf, .txt, .doc, .md, .html, .rtf",
        key="resume_uploader"
    )
    
    if uploaded_file is not None:
        st.success(f"📎 File selected: **{uploaded_file.name}**")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Submit Resume", use_container_width=True, type="primary"):
                with st.spinner("Uploading and processing resume..."):
                    success, message = send_resume_to_backend(
                        uploaded_file, 
                        st.session_state.access_token
                    )
                
                if success:
                    st.session_state.resume_content = True  # Just mark as uploaded
                    st.session_state.resume_uploaded = True
                    st.success(f"✅ {message}")
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
        
        with col2:
            if st.button("⏭️ Skip Resume", use_container_width=True):
                st.session_state.resume_uploaded = True
                st.rerun()
    else:
        st.info("👆 Upload your resume to get personalized interview questions")
        if st.button("⏭️ Skip and Start Interview", use_container_width=True):
            st.session_state.resume_uploaded = True
            st.rerun()


def render_chat_interface():
    """Render the native Streamlit chat interface."""
    # Header with user info
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.markdown(f"### 💬 Interview Session")
        st.caption(f"Logged in as **{st.session_state.username}**")
    with col2:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.messages = []
            st.session_state.interview_started = False
            st.rerun()
    with col3:
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.access_token = None
            st.session_state.username = None
            st.session_state.messages = []
            st.session_state.resume_content = None
            st.session_state.resume_uploaded = False
            st.session_state.interview_started = False
            st.rerun()
    
    st.divider()
    
    # Resume status indicator
    if not st.session_state.resume_content:
        st.markdown("""
        <div class="resume-success">
            ❌<strong>Resume NOT loaded</strong> - Your resume has been analyzed for personalized questions
        </div>
        """, unsafe_allow_html=True)
    
    # Start interview if not started
    if not st.session_state.interview_started and not st.session_state.messages:
        st.info("👋 Ready to begin your interview? The AI interviewer will ask you questions based on your profile.")
        if st.button("🎯 Start Interview", use_container_width=True, type="primary"):
            st.session_state.interview_started = True
            # Add initial greeting from assistant
            st.session_state.messages.append({
                "role": "assistant",
                "content": "Hello! Welcome to your interview session. I'm Aspira, your AI interviewer. I'll be asking you some questions to understand your background and skills better. Let's start - could you tell me a bit about yourself and what kind of role you're looking for?"
            })
            st.rerun()
    
    # Display chat messages using native st.chat_message
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar="🧑‍💼" if message["role"] == "user" else "✨"):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Type your response here...", key="chat_input"):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message immediately
        with st.chat_message("user", avatar="🧑‍💼"):
            st.markdown(prompt)
        
        # Get AI response
        with st.chat_message("assistant", avatar="✨"):
            with st.spinner("Thinking..."):
                success, response = send_chat_message(
                    prompt, 
                    st.session_state.access_token,
                    st.session_state.conversation_id
                )
            
            if success:
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            else:
                error_msg = f"❌ Error: {response}"
                st.error(error_msg)
                # Check if token expired
                if "credentials" in str(response).lower() or "401" in str(response):
                    st.warning("Session expired. Please login again.")
                    st.session_state.access_token = None


def render_sidebar():
    """Render the sidebar - minimal, clean design."""
    # API Status
    st.sidebar.markdown("### 📡 API Status")
    api_connected = render_api_status()
    
    if st.session_state.access_token:
        st.sidebar.markdown("---")
        
        # Navigation
        st.sidebar.markdown("### 🧭 Navigation")
        view_selection = st.sidebar.radio("View", ["Interview", "Dashboard"])
        if view_selection != st.session_state.current_view:
            st.session_state.current_view = view_selection
            st.rerun()

        st.sidebar.markdown("---")
        st.sidebar.markdown("### 💬 Conversations")
        
        # Fetch conversations
        st.session_state.conversations_list = fetch_conversations(st.session_state.access_token)
        
        # Ensure current active conversation is in the list even if it has no messages yet
        if st.session_state.conversation_id not in st.session_state.conversations_list:
            st.session_state.conversations_list.append(st.session_state.conversation_id)
        
        # Create New Conversation
        new_conv = st.sidebar.text_input("New Conversation Name", placeholder="e.g. Google Interview")
        if st.sidebar.button("➕ Create New"):
            if new_conv and new_conv not in st.session_state.conversations_list:
                st.session_state.conversation_id = new_conv
                st.session_state.messages = []
                st.session_state.interview_started = False
                st.rerun()
                
        # Select Existing Conversation
        selected_conv = st.sidebar.selectbox(
            "Select Conversation", 
            options=st.session_state.conversations_list,
            index=st.session_state.conversations_list.index(st.session_state.conversation_id) if st.session_state.conversation_id in st.session_state.conversations_list else 0
        )
        
        if selected_conv != st.session_state.conversation_id:
            st.session_state.conversation_id = selected_conv
            st.session_state.messages = load_conversation_history(selected_conv, st.session_state.access_token)
            st.session_state.interview_started = len(st.session_state.messages) > 0
            st.rerun()
            
    # Interview stats (only show if in session)
    if st.session_state.access_token and st.session_state.messages and st.session_state.current_view == "Interview":
        st.sidebar.markdown("---")
        user_msgs = len([m for m in st.session_state.messages if m["role"] == "user"])
        st.sidebar.markdown("### 📊 Session Stats")
        st.sidebar.metric("Responses", user_msgs)
        
        if st.session_state.resume_content:
            st.sidebar.success("📄 Resume loaded")
    
    return api_connected


def render_dashboard():
    """Render the Dashboard for visualizing interview scores."""
    st.markdown(f"### 📈 Dashboard: {st.session_state.conversation_id}")
    st.caption("Review your performance and accumulated keyword scores from the interview.")
    
    with st.spinner("Loading dashboard..."):
        data = fetch_dashboard_data(st.session_state.conversation_id, st.session_state.access_token)
        
    if not data:
        st.warning("No data found for this conversation.")
        return
        
    metrics = data.get("metrics", {})
    keywords = data.get("keywords", [])
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Questions Asked", metrics.get("total_questions", 0))
    with col2:
        st.metric("Total User Responses", metrics.get("total_responses", 0))
        
    st.markdown("---")
    st.markdown("#### 🏆 Keyword Performance Scores")
    
    if not keywords:
        st.info("No keywords extracted yet. Start an interview to see your scores here!")
    else:
        import pandas as pd
        
        # Prepare DataFrame for chart
        df = pd.DataFrame(keywords)
        # Compute combined score for visualization
        df["Combined Score"] = df["score"] * df["similarity"]
        df_sorted = df.sort_values(by="Combined Score", ascending=False).head(10)
        
        st.bar_chart(data=df_sorted, x="keyword", y="score")

# --- Main App ---
def main():
    # Render sidebar and get API status
    api_connected = render_sidebar()
    
    # Render header
    render_header()
    
    # Check API connection
    if not api_connected:
        st.error("""
        ⚠️ **Cannot connect to API server**
        
        Please ensure the API server is running at the configured URL.
        You can update the API URL in the sidebar.
        """)
        st.code(f"API URL: {API_BASE_URL}")
        return
    
    # Main content based on state
    if not st.session_state.access_token:
        # Not logged in - show auth
        render_auth_section()
    elif not st.session_state.resume_uploaded:
        # Logged in but no resume - show upload
        render_resume_upload()
    else:
        # View Routing
        if st.session_state.current_view == "Dashboard":
            render_dashboard()
        else:
            # Ready for interview - show chat
            render_chat_interface()


if __name__ == "__main__":
    main()

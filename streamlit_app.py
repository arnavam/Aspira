"""
Aspira - AI Interview Assistant
Streamlit Frontend for the Aspira API
"""

import streamlit as st
import requests
from typing import Optional

# --- Configuration ---
API_BASE_URL = st.sidebar.text_input(
    "API URL", 
    value="http://localhost:8000",
    help="Base URL of the Aspira API server"
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
        padding: 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
    }
    
    .main-header h1 {
        color: white;
        font-weight: 700;
        margin: 0;
        font-size: 2.5rem;
    }
    
    .main-header p {
        color: rgba(255, 255, 255, 0.9);
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
    }
    
    /* Chat Container */
    .chat-container {
        background: #f8fafc;
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid #e2e8f0;
    }
    
    /* Message Bubbles */
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem 1.25rem;
        border-radius: 18px 18px 4px 18px;
        margin: 0.75rem 0;
        max-width: 80%;
        margin-left: auto;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.2);
    }
    
    .assistant-message {
        background: white;
        color: #1e293b;
        padding: 1rem 1.25rem;
        border-radius: 18px 18px 18px 4px;
        margin: 0.75rem 0;
        max-width: 80%;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
    }
    
    /* Auth Card */
    .auth-card {
        background: white;
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        border: 1px solid #e2e8f0;
    }
    
    /* Status Indicators */
    .status-badge {
        display: inline-flex;
        align-items: center;
        padding: 0.375rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.875rem;
        font-weight: 500;
    }
    
    .status-connected {
        background: #d1fae5;
        color: #065f46;
    }
    
    .status-disconnected {
        background: #fee2e2;
        color: #991b1b;
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
</style>
""", unsafe_allow_html=True)


# --- Session State Initialization ---
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "username" not in st.session_state:
    st.session_state.username = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# --- API Helper Functions ---
def check_api_health() -> bool:
    """Check if the API server is running."""
    try:
        response = requests.post(f"{API_BASE_URL}/", timeout=5)
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


def send_chat_message(message: str, token: str) -> tuple[bool, str]:
    """Send a chat message to the API."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/chat",
            json={"message": message},
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


def render_chat_interface():
    """Render the chat interface."""
    st.markdown(f"### 💬 Chat with Aspira")
    st.markdown(f"*Logged in as: **{st.session_state.username}***")
    
    # Logout button
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.access_token = None
            st.session_state.username = None
            st.session_state.chat_history = []
            st.rerun()
    
    st.divider()
    
    # Chat history display
    chat_container = st.container()
    with chat_container:
        if not st.session_state.chat_history:
            st.info("👋 Start a conversation by sending a message below!")
        else:
            for msg in st.session_state.chat_history:
                if msg["role"] == "user":
                    st.markdown(f"""
                    <div class="user-message">
                        <strong>You:</strong> {msg["content"]}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="assistant-message">
                        <strong>Aspira:</strong> {msg["content"]}
                    </div>
                    """, unsafe_allow_html=True)
    
    # Message input
    st.divider()
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input(
            "Message",
            placeholder="Type your message here...",
            label_visibility="collapsed"
        )
        col1, col2 = st.columns([4, 1])
        with col2:
            send_button = st.form_submit_button("Send ➤", use_container_width=True)
    
    if send_button and user_input:
        # Add user message to history
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input
        })
        
        # Send to API
        with st.spinner("Aspira is thinking..."):
            success, response = send_chat_message(
                user_input, 
                st.session_state.access_token
            )
        
        if success:
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": response
            })
        else:
            st.error(f"❌ Error: {response}")
            # Check if token expired
            if "credentials" in response.lower() or "401" in response:
                st.warning("Session expired. Please login again.")
                st.session_state.access_token = None
        
        st.rerun()


def render_sidebar():
    """Render the sidebar."""
    st.sidebar.markdown("## ⚡ Aspira")
    st.sidebar.markdown("---")
    
    # API Status
    st.sidebar.markdown("### 📡 API Status")
    api_connected = render_api_status()
    
    st.sidebar.markdown("---")
    
    # User info if logged in
    if st.session_state.access_token:
        st.sidebar.markdown("### 👤 Account")
        st.sidebar.markdown(f"**User:** {st.session_state.username}")
        
        st.sidebar.markdown("---")
        
        # Clear chat button
        if st.sidebar.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    <div style="text-align: center; color: #888; font-size: 0.8rem;">
        Built with ❤️ using Streamlit<br>
        Powered by Aspira AI
    </div>
    """, unsafe_allow_html=True)
    
    return api_connected


# --- Main App ---
def main():
    st.set_page_config(
        page_title="Aspira - AI Interview Assistant",
        page_icon="✨",
        layout="centered",
        initial_sidebar_state="expanded"
    )
    
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
    
    # Main content based on auth state
    if st.session_state.access_token:
        render_chat_interface()
    else:
        render_auth_section()


if __name__ == "__main__":
    main()

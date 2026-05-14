# Aspira — High-Stakes AI Interviewer Protocol

Aspira is a premium, end-to-end AI-powered interviewer platform designed to simulate high-stakes professional interviews. It leverages state-of-the-art LLM orchestration to provide dynamic questioning, real-time knowledge mapping, and automated performance analytics.

## 🏗️ Project Architecture

The project is split into two main components:

- **[Frontend](./frontend)**: A modern, glassmorphic React dashboard built with Vite and TypeScript.
- **[Backend](./backend)**: A high-performance FastAPI server utilizing LangGraph for complex interview workflows and LLM orchestration.

---

## 🛠️ Tech Stack

### Frontend
- **Framework**: [React 19](https://react.dev/)
- **Build Tool**: [Vite](https://vitejs.dev/)
- **Language**: [TypeScript](https://www.typescriptlang.org/)
- **Icons**: [Lucide React](https://lucide.dev/)
- **Styling**: Modern CSS with Glassmorphism and dark-mode aesthetics.

### Backend
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **Orchestration**: [LangGraph](https://python.langchain.com/docs/langgraph/) (Stateful AI workflows)
- **Database**: [MongoDB](https://www.mongodb.com/) (Motor driver)
- **AI Models**: [Groq](https://groq.com/) (LLMs & Whisper STT)
- **Speech**: [edge-tts](https://github.com/rany2/edge-tts) (Neural TTS)
- **RAG & Graph**: [LlamaIndex](https://www.llamaindex.ai/) & NetworkX

---

## 🚀 Quick Start

### 1. Prerequisites
- [Node.js](https://nodejs.org/) (v18+)
- [Python 3.13+](https://www.python.org/)
- [uv](https://github.com/astral-sh/uv) (Python package manager)
- [MongoDB](https://www.mongodb.com/) (Local or Atlas)

### 2. Backend Setup
```bash
cd backend
cp .env.example .env  # Fill in your GROQ_API_KEY and MONGODB_URI
uv sync
uv run uvicorn api_server:app --reload
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
The application will be available at `http://localhost:5173`.

---

## ✨ Key Features

- **Dynamic Contextual Interviews**: Questions are generated based on your resume and real-time answers.
- **Live Knowledge Graph**: Visualize your skill map and expertise depth as the interview progresses.
- **Automated Evaluation**: Get a detailed breakdown of your technical accuracy, communication, and role fit.
- **Low-Latency Audio**: High-speed transcription and neural text-to-speech for an immersive experience.
- **Session Persistence**: All interview history and performance metrics are securely stored.

## 🧪 Testing

To run the backend test suite:
```bash
cd backend
uv run pytest tests/ --cov
```

---

## 📄 License
Aspira is open-source software. Feel free to modify and use it according to your needs.

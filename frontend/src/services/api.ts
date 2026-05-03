const API_URL = "http://localhost:8000";

export const getAuthToken = () => localStorage.getItem("token");
export const setAuthToken = (token: string) => localStorage.setItem("token", token);
export const clearAuthToken = () => localStorage.removeItem("token");

const headers = (isFormData = false) => {
  const token = getAuthToken();
  const h: HeadersInit = {};
  if (token) h["Authorization"] = `Bearer ${token}`;
  if (!isFormData) h["Content-Type"] = "application/json";
  return h;
};

const handleResponse = async (res: Response) => {
  if (res.status === 401) {
    clearAuthToken();
    window.location.href = "/?error=session_expired";
    throw new Error("Session expired");
  }
  if (!res.ok) {
    throw new Error(await res.text());
  }
  return res;
};

export const api = {
  // Auth
  register: async (username: string, password: string) => {
    const res = await fetch(`${API_URL}/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    await handleResponse(res);
    return res.json();
  },

  login: async (username: string, password: string) => {
    const formData = new URLSearchParams();
    formData.append("username", username);
    formData.append("password", password);
    const res = await fetch(`${API_URL}/token`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: formData,
    });
    await handleResponse(res);
    return res.json();
  },

  // Setup / Resume
  uploadResume: async (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`${API_URL}/resume`, {
      method: "POST",
      headers: headers(true),
      body: formData,
    });
    await handleResponse(res);
    return res.json();
  },

  setupInterview: async (conversation_id: string, company: string, role: string, requirements: string) => {
    const res = await fetch(`${API_URL}/setup_interview`, {
      method: "POST",
      headers: headers(),
      body: JSON.stringify({ conversation_id, company, role, requirements }),
    });
    await handleResponse(res);
    return res.json();
  },

  // Conversations
  getConversations: async () => {
    const res = await fetch(`${API_URL}/conversations`, { headers: headers() });
    await handleResponse(res);
    const data = await res.json();
    return data.conversations || [];
  },

  getHistory: async (id: string) => {
    const res = await fetch(`${API_URL}/conversations/${id}/history`, { headers: headers() });
    await handleResponse(res);
    const data = await res.json();
    return { 
      history: data.history || [], 
      is_ended: data.is_ended || false,
      metadata: data.metadata || {} 
    };
  },

  // Chat
  chat: async (message: string, conversation_id: string, force_end: boolean = false) => {
    const res = await fetch(`${API_URL}/chat`, {
      method: "POST",
      headers: headers(),
      body: JSON.stringify({ message, conversation_id, force_end }),
    });
    await handleResponse(res);

    if (!res.body) throw new Error("No response body");

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let finalResponse = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value, { stream: true });
      
      const lines = chunk.split('\n');
      let currentEvent = '';
      for (const line of lines) {
        if (line.startsWith('event: ')) {
          currentEvent = line.substring(7).trim();
        } else if (line.startsWith('data: ')) {
          const dataStr = line.substring(6).trim();
          if (dataStr && dataStr !== 'Stream finished') {
            try {
              const data = JSON.parse(dataStr);
              if (currentEvent === 'question' && data.response) {
                finalResponse = data.response;
              }
            } catch (e) {
              console.error("Failed to parse SSE data", e);
            }
          }
        }
      }
    }
    return { response: finalResponse };
  },

  // Audio Processing
  transcribe: async (audioBlob: Blob) => {
    const formData = new FormData();
    formData.append("file", audioBlob, "audio.wav");
    const res = await fetch(`${API_URL}/transcribe`, {
      method: "POST",
      headers: headers(true),
      body: formData,
    });
    await handleResponse(res);
    return res.json();
  },

  // Dashboard
  getDashboard: async (id: string) => {
    const res = await fetch(`${API_URL}/dashboard/${id}`, { headers: headers() });
    await handleResponse(res);
    return res.json();
  },

  getTTSUrl: (text: string) => `${API_URL}/tts?text=${encodeURIComponent(text)}`,
};

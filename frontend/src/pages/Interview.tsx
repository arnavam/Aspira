import { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Mic, Square, Menu, Settings, BarChart3, LogOut, X, Code, Send, Volume2 } from 'lucide-react';
import { api, clearAuthToken } from '../services/api';

type Message = { role: 'user' | 'assistant'; content: string };

export default function Interview() {
  const [conversations, setConversations] = useState<string[]>(['default']);
  const [currentConv, setCurrentConv] = useState('default');
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isSessionEnded, setIsSessionEnded] = useState(false);
  const [metadata, setMetadata] = useState<any>({});
  const [hasStarted, setHasStarted] = useState(false);
  
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [showDebug, setShowDebug] = useState(false);
  
  const [isRecording, setIsRecording] = useState(false);
  const [loading, setLoading] = useState(false);
  const [ttsEngine, setTtsEngine] = useState<'edge' | 'browser'>('edge');
  const [recordingDuration, setRecordingDuration] = useState(0);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<number | null>(null);
  const hasGreetingPlayedRef = useRef(false);
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);
  
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const init = async () => {
      // Check if we came from Setup with a new conversation ID
      if (location.state?.newConversationId) {
        const newId = location.state.newConversationId;
        setConversations(prev => [...prev, newId]);
        setCurrentConv(newId);
        await loadHistory(newId);
        window.history.replaceState({}, document.title);
      } else {
        // Fetch conversations and load the most recent one if available
        const fetchedConvs = await fetchConversations();
        const latestConv = fetchedConvs.length > 0 ? fetchedConvs[fetchedConvs.length - 1] : 'default';
        setCurrentConv(latestConv);
        await loadHistory(latestConv);
      }
    };
    init();
  }, []);

  const fetchConversations = async () => {
    try {
      const data = await api.getConversations();
      if (data && data.length > 0) {
        setConversations(() => {
          const combined = new Set([...data]);
          if (currentConv && !combined.has(currentConv)) combined.add(currentConv);
          return Array.from(combined);
        });
      }
      return data || [];
    } catch (e) {
      console.error(e);
      if (String(e).includes('401')) handleLogout();
      return [];
    }
  };

  const loadHistory = async (convId: string) => {
    try {
      setLoading(true);
      const data = await api.getHistory(convId);
      const history = data.history || [];
      setIsSessionEnded(data.is_ended || false);
      setMessages(history);
      setMetadata(data.metadata || {});
      setCurrentConv(convId);
      setIsSidebarOpen(false); // Auto-collapse
      
      if (history.length > 0) {
        setHasStarted(true);
      } else {
        setHasStarted(false);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    clearAuthToken();
    navigate('/');
  };

  const handleNewInterviewClick = () => {
    setIsSidebarOpen(false);
    navigate('/setup');
  };

  const handleStartInterview = async () => {
    setHasStarted(true);
    setLoading(true);
    
    // Unlock audio context via user interaction
    if (currentAudioRef.current) {
      currentAudioRef.current.play().catch(() => {});
      currentAudioRef.current.pause();
    } else if (ttsEngine === 'browser') {
      const u = new SpeechSynthesisUtterance("");
      window.speechSynthesis.speak(u);
      window.speechSynthesis.cancel();
    }

    try {
      const response = await api.chat("", currentConv);
      const aiText = response.response;
      setMessages(prev => [...prev, { role: 'assistant', content: aiText }]);
      playTTS(aiText);
    } catch (err) {
      console.error(err);
      setMessages(prev => [...prev, { role: 'assistant', content: '❌ Error connecting to server. Please try again.' }]);
    } finally {
      setLoading(false);
    }
  };

  const playTTS = (text: string) => {
    if (!text) return;
    
    // Stop any currently playing audio
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current.currentTime = 0;
    }
    window.speechSynthesis.cancel();

    if (ttsEngine === 'browser') {
      const utterance = new SpeechSynthesisUtterance(text);
      window.speechSynthesis.speak(utterance);
    } else {
      const audio = new Audio(api.getTTSUrl(text));
      currentAudioRef.current = audio;
      audio.play().catch(e => console.error("Audio playback failed", e));
    }
  };

  const handleReplay = () => {
    const aiMsgs = messages.filter(m => m.role === 'assistant');
    if (aiMsgs.length > 0) {
      playTTS(aiMsgs[aiMsgs.length - 1].content);
    }
  };

  const handleSendMessage = async (text: string) => {
    if (!text.trim() || loading) return;
    
    const userMsg: Message = { role: 'user', content: text };
    setMessages(prev => [...prev, userMsg]);
    setInputText('');
    setLoading(true);

    try {
      const response = await api.chat(text, currentConv);
      const aiText = response.response;
      setMessages(prev => [...prev, { role: 'assistant', content: aiText }]);
      playTTS(aiText);
    } catch (err) {
      console.error(err);
      setMessages(prev => [...prev, { role: 'assistant', content: '❌ Error connecting to server. Please try again.' }]);
    } finally {
      setLoading(false);
    }
  };

  const handleEndSession = async () => {
    setLoading(true);
    try {
      await api.chat("User ended the interview.", currentConv, true);
    } catch (err) {
      console.error("Failed to end session gracefully", err);
    } finally {
      setLoading(false);
      navigate(`/dashboard/${currentConv}`);
    }
  };

  // --- Audio Recording Logic ---
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        stream.getTracks().forEach(track => track.stop());
        if (timerRef.current) clearInterval(timerRef.current);
        setRecordingDuration(0);
        
        setLoading(true);
        try {
          const res = await api.transcribe(audioBlob);
          if (res.text) {
            handleSendMessage(res.text);
          }
        } catch (e) {
          console.error(e);
        } finally {
          setLoading(false);
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
      setRecordingDuration(0);
      timerRef.current = window.setInterval(() => {
        setRecordingDuration(prev => prev + 1);
      }, 1000);
    } catch (err) {
      console.error("Error accessing microphone", err);
      alert("Microphone access is required.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60).toString().padStart(2, '0');
    const s = (seconds % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  // Get the latest AI question
  const aiMessages = messages.filter(m => m.role === 'assistant');
  const currentQuestion = aiMessages.length > 0 
    ? aiMessages[aiMessages.length - 1].content 
    : "Initializing...";
  
  const questionCount = Math.floor(messages.length / 2) + 1;

  const getFontSize = (text: string) => {
    const len = text.length;
    if (len < 60) return '2.5rem';
    if (len < 150) return '2rem';
    if (len < 300) return '1.5rem';
    return '1.25rem';
  };

  return (
    <div className="app-container">
      
      {/* Top Header for Hamburger */}
      <div style={{ position: 'absolute', top: 0, left: 0, right: 0, padding: '24px', zIndex: 10, display: 'flex', justifyContent: 'space-between', pointerEvents: 'none' }}>
        <button 
          onClick={() => setIsSidebarOpen(true)}
          style={{ background: 'transparent', border: 'none', color: 'var(--text-primary)', cursor: 'pointer', pointerEvents: 'auto' }}
        >
          <Menu size={28} />
        </button>
      </div>

      {/* Overlay */}
      {isSidebarOpen && (
        <div 
          onClick={() => setIsSidebarOpen(false)}
          style={{ position: 'absolute', inset: 0, background: 'rgba(0,0,0,0.6)', zIndex: 40, backdropFilter: 'blur(4px)' }}
        />
      )}

      {/* Sidebar */}
      <aside style={{ 
        position: 'absolute', top: 0, bottom: 0, left: 0, width: '400px', 
        background: 'var(--bg-primary)', borderRight: '1px solid var(--glass-border)', 
        zIndex: 50, display: 'flex', flexDirection: 'column',
        transform: isSidebarOpen ? 'translateX(0)' : 'translateX(-100%)',
        transition: 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        fontFamily: 'var(--font-ui)'
      }}>
        <div style={{ padding: '32px 24px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ color: 'var(--accent-primary)', fontSize: '1.2rem' }}>✦</span>
            <span style={{ fontSize: '1.2rem', fontWeight: 700, letterSpacing: '0.1em' }}>ASPIRA</span>
          </div>
          <button onClick={() => setIsSidebarOpen(false)} style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>
        
        <div style={{ padding: '0 24px', marginBottom: '32px' }}>
          <button className="btn btn-primary" onClick={handleNewInterviewClick} style={{ width: '100%', padding: '12px', borderRadius: '8px' }}>
            + New Interview
          </button>
        </div>

        <div style={{ flex: 1, overflowY: 'auto' }}>
          <h3 style={{ fontSize: '0.75rem', color: 'var(--accent-primary)', padding: '0 24px', marginBottom: '16px', letterSpacing: '0.1em', fontWeight: 700 }}>SESSION HISTORY</h3>
          <ul style={{ listStyle: 'none' }}>
            {conversations.map(conv => {
              const isActive = currentConv === conv;
              return (
                <li key={conv}>
                  <button 
                    onClick={() => {
                      if (isActive) {
                        setIsSidebarOpen(false);
                      } else {
                        navigate(`/dashboard/${conv}`);
                      }
                    }}
                    style={{ 
                      width: '100%', textAlign: 'left', padding: '12px 24px', 
                      background: isActive ? 'rgba(255,255,255,0.03)' : 'transparent',
                      color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
                      border: 'none', borderLeft: isActive ? '3px solid var(--accent-primary)' : '3px solid transparent',
                      cursor: 'pointer', fontSize: '0.9rem', transition: 'all 0.2s',
                      whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis'
                    }}
                  >
                    {/* In a real app we'd map ID to a Date + Role string. For now, use the ID or truncate it. */}
                    {conv.replace('interview-', 'Session ')}
                  </button>
                </li>
              );
            })}
          </ul>
        </div>

        <div style={{ padding: '24px', borderTop: '1px solid var(--glass-border)', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={{ fontSize: '0.75rem', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Settings size={12} /> Voice Engine
            </label>
            <select 
              value={ttsEngine} 
              onChange={e => setTtsEngine(e.target.value as 'edge' | 'browser')}
              style={{ padding: '8px', fontSize: '0.875rem', background: 'transparent', border: '1px solid var(--glass-border)' }}
            >
              <option value="edge">Edge TTS / OpenAI</option>
              <option value="browser">Browser Native</option>
            </select>
          </div>
          
          <button onClick={() => { setIsSidebarOpen(false); setShowDebug(true); }} style={{ display: 'flex', alignItems: 'center', gap: '12px', background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '0.9rem', padding: '8px 0' }}>
            <Code size={16} /> Debug & Export
          </button>

          <button onClick={handleLogout} style={{ display: 'flex', alignItems: 'center', gap: '12px', background: 'none', border: 'none', color: '#c25e5e', cursor: 'pointer', fontSize: '0.9rem', padding: '8px 0', marginTop: '16px' }}>
            <LogOut size={16} /> Logout
          </button>
        </div>
      </aside>

      {/* Main Split View */}
      <main className="main-split">
        
        {/* Left Column - The Question */}
        <div className="left-column">
          <div style={{ marginBottom: '64px', display: 'flex', flexDirection: 'column', alignItems: 'center', alignSelf: 'center' }}>
            <div style={{ 
              width: '96px', height: '96px', borderRadius: '50%', background: 'var(--bg-secondary)', 
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              border: '2px solid rgba(112, 92, 255, 0.4)',
              boxShadow: '0 0 40px rgba(112, 92, 255, 0.15)',
              marginBottom: '20px',
              position: 'relative'
            }}>
              <div style={{ position: 'absolute', inset: '6px', borderRadius: '50%', border: '1px solid rgba(255, 255, 255, 0.05)' }} />
              <div style={{ width: '56px', height: '56px', background: '#32365A', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: 'inset 0 0 10px rgba(0,0,0,0.5)' }}>
                <span style={{ display: 'flex', gap: '4px', alignItems: 'center', color: 'var(--accent-secondary)' }}>
                  <div style={{ width: '4px', height: '14px', background: 'currentColor', borderRadius: '2px' }} />
                  <div style={{ width: '4px', height: '22px', background: 'currentColor', borderRadius: '2px' }} />
                  <div style={{ width: '4px', height: '14px', background: 'currentColor', borderRadius: '2px' }} />
                </span>
              </div>
            </div>
            <h3 style={{ color: 'var(--accent-secondary)', fontSize: '1.4rem', fontFamily: 'var(--font-heading)', fontStyle: 'italic', marginBottom: '6px', fontWeight: 600 }}>Aspira</h3>
            <p style={{ fontSize: '0.65rem', color: 'var(--text-secondary)', letterSpacing: '0.12em', textTransform: 'uppercase', textAlign: 'center' }}>
              {metadata.company ? `${metadata.company} Interview` : 'Technical Interview'}
            </p>
          </div>

          <h1 style={{ fontSize: getFontSize(currentQuestion), transition: 'font-size 0.3s ease-in-out', lineHeight: 1.3 }}>
            {currentQuestion}
          </h1>

          <div style={{ marginTop: 'auto', width: '100%', paddingTop: '40px', borderTop: '1px solid rgba(255, 255, 255, 0.05)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', fontWeight: 600, letterSpacing: '0.05em', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
              <span style={{ color: 'var(--text-primary)' }}>Question {questionCount}</span>
              <span style={{ color: 'var(--text-primary)' }}>{metadata.role || 'General Assessment'}</span>
            </div>
          </div>
        </div>

        {/* Right Column - User Interface */}
        <div className="right-column">
          
          <button 
            onClick={handleEndSession}
            style={{ position: 'absolute', top: '24px', right: '24px', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--glass-border)', color: 'var(--text-secondary)', padding: '8px 16px', borderRadius: '20px', cursor: 'pointer', fontFamily: 'var(--font-ui)', fontSize: '0.875rem', transition: 'all 0.2s', zIndex: 10, display: showDebug ? 'none' : 'block' }}
            onMouseOver={(e) => { e.currentTarget.style.color = 'var(--accent-primary)'; e.currentTarget.style.borderColor = 'var(--accent-primary)'; }}
            onMouseOut={(e) => { e.currentTarget.style.color = 'var(--text-secondary)'; e.currentTarget.style.borderColor = 'var(--glass-border)'; }}
          >
            End Session & View Analytics →
          </button>

          <div className="glass-panel interview-card" style={{ boxShadow: '0 0 80px 20px rgba(0, 0, 0, 0.5), 0 0 120px 40px rgba(0, 0, 0, 0.3)' }}>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Mic size={16} color="var(--text-secondary)" />
                {isRecording && (
                  <div style={{ display: 'flex', gap: '4px', color: 'var(--success)' }}>
                    <div style={{ width: '3px', height: '12px', background: 'currentColor', borderRadius: '2px', animation: 'pulse-height 1s infinite ease-in-out' }} />
                    <div style={{ width: '3px', height: '18px', background: 'currentColor', borderRadius: '2px', animation: 'pulse-height 1s infinite ease-in-out 0.2s' }} />
                    <div style={{ width: '3px', height: '12px', background: 'currentColor', borderRadius: '2px', animation: 'pulse-height 1s infinite ease-in-out 0.4s' }} />
                  </div>
                )}
              </div>
              <span style={{ fontFamily: 'monospace', fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)', letterSpacing: '0.05em' }}>
                {formatTime(recordingDuration)}
              </span>
            </div>

            <div style={{ height: '320px', background: 'var(--bg-secondary)', borderRadius: '6px', border: '1px solid rgba(221, 161, 94, 0.3)', display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden' }}>
              <img src="/interviewer.png" alt="AI Interviewer" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            </div>

            <div style={{ textAlign: 'center', display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {loading ? (
                <p style={{ color: 'var(--accent-primary)', fontSize: '0.9rem' }}>Aspira is analyzing...</p>
              ) : isRecording ? (
                <p style={{ color: 'var(--success)', fontSize: '0.9rem' }}>Listening...</p>
              ) : (
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Awaiting your response...</p>
              )}
              <p style={{ fontSize: '0.65rem', color: 'var(--text-muted)', letterSpacing: '0.1em', marginTop: '12px' }}>TAKE YOUR TIME. SPEAK CLEARLY.</p>
            </div>

            <div style={{ display: 'flex', gap: '8px', background: 'rgba(255,255,255,0.03)', borderRadius: '100px', padding: '8px', border: '1px solid var(--glass-border)', alignItems: 'center' }}>
              <button 
                onClick={handleReplay}
                style={{ width: '36px', height: '36px', borderRadius: '50%', background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                title="Replay last question"
              >
                <Volume2 size={16} />
              </button>

              <button 
                className={`btn-icon ${isRecording ? 'recording-pulse' : ''}`}
                onClick={isRecording ? stopRecording : startRecording}
                disabled={loading}
                style={{ width: '40px', height: '40px', borderRadius: '50%', background: isRecording ? 'var(--danger)' : 'rgba(255,255,255,0.1)', border: 'none', color: isRecording ? 'white' : 'var(--text-primary)', cursor: loading ? 'not-allowed' : 'pointer' }}
              >
                {isRecording ? <Square size={16} fill="currentColor" /> : <Mic size={16} />}
              </button>
              
              <input 
                type="text" 
                value={inputText}
                onChange={e => setInputText(e.target.value)}
                onKeyDown={e => {
                  if (e.key === 'Enter') handleSendMessage(inputText);
                }}
                placeholder={isSessionEnded ? "Interview concluded." : "Type your response or speak..."}
                disabled={loading || isRecording || isSessionEnded}
                style={{ background: 'transparent', border: 'none', padding: '0 8px', boxShadow: 'none', flex: 1, color: 'var(--text-secondary)' }}
              />
              
              <button 
                onClick={() => handleSendMessage(inputText)}
                disabled={!inputText.trim() || loading || isRecording || isSessionEnded}
                style={{ width: '40px', height: '40px', borderRadius: '50%', background: 'var(--accent-primary)', border: 'none', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: (!inputText.trim() || loading || isRecording || isSessionEnded) ? 'not-allowed' : 'pointer', opacity: (!inputText.trim() || loading || isRecording || isSessionEnded) ? 0.5 : 1 }}
              >
                <Send size={16} />
              </button>
            </div>

          </div>
        </div>
      </main>

      {isSessionEnded && (
        <div style={{ position: 'absolute', top: '80px', left: '50%', transform: 'translateX(-50%)', background: 'rgba(239, 68, 68, 0.2)', color: 'var(--danger)', padding: '8px 24px', borderRadius: '20px', border: '1px solid var(--danger)', fontSize: '0.875rem', fontWeight: 'bold', zIndex: 100, backdropFilter: 'blur(10px)' }}>
          Session Concluded — Read Only Mode
        </div>
      )}

      {/* Start Overlay */}
      {!hasStarted && !loading && (
        <div style={{ position: 'absolute', inset: 0, background: 'rgba(0,0,0,0.8)', zIndex: 60, display: 'flex', alignItems: 'center', justifyContent: 'center', backdropFilter: 'blur(10px)' }}>
          <div className="glass-panel" style={{ padding: '40px', textAlign: 'center', maxWidth: '400px' }}>
            <h2 style={{ marginBottom: '16px', color: 'var(--text-primary)' }}>Ready to begin?</h2>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '32px', fontSize: '0.9rem' }}>
              Ensure your microphone is connected. Audio will play automatically after you start.
            </p>
            <button className="btn btn-primary" onClick={handleStartInterview} style={{ width: '100%', padding: '16px', fontSize: '1.1rem' }}>
              Start Interview
            </button>
          </div>
        </div>
      )}

      {/* Debug & Export Drawer */}
      {showDebug && (
        <div className="glass-modal animate-fade-in" style={{ position: 'absolute', top: '40px', bottom: '40px', right: '40px', width: '400px', zIndex: 100, display: 'flex', flexDirection: 'column' }}>
          <div style={{ padding: '24px', borderBottom: '1px solid var(--glass-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ fontFamily: 'var(--font-ui)', fontSize: '1.2rem' }}>Session Log</h3>
            <button onClick={() => setShowDebug(false)} style={{ background: 'none', border: 'none', color: 'var(--text-primary)', cursor: 'pointer' }}>
              <X size={20} />
            </button>
          </div>
          <div style={{ flex: 1, overflowY: 'auto', padding: '24px' }}>
            {messages.map((msg, i) => (
              <div key={i} style={{ marginBottom: '16px', background: 'rgba(0,0,0,0.2)', padding: '12px', borderRadius: '8px' }}>
                <span style={{ fontSize: '0.75rem', color: msg.role === 'assistant' ? 'var(--accent-primary)' : 'var(--success)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{msg.role}</span>
                <p style={{ fontSize: '0.9rem', marginTop: '4px' }}>{msg.content}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      <style>{`
        @keyframes pulse-height {
          0%, 100% { transform: scaleY(1); }
          50% { transform: scaleY(2); }
        }
      `}</style>
    </div>
  );
}

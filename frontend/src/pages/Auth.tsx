import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, User, Lock, ArrowRight } from 'lucide-react';
import { api, setAuthToken } from '../services/api';

export default function Auth() {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [groqKey, setGroqKey] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('error') === 'session_expired') {
      setError('Your session has expired. Please sign in again.');
      // Remove it from the URL so it doesn't stick around on refresh
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (isLogin) {
        const data = await api.login(username, password);
        setAuthToken(data.access_token);
        navigate('/setup');
      } else {
        if (!groqKey.trim().startsWith('gsk_')) {
          throw new Error("Invalid Groq API Key format. It should start with 'gsk_'");
        }
        const data = await api.register(username, password, groqKey.trim());
        setAuthToken(data.access_token);
        navigate('/setup');
      }
    } catch (err: any) {
      setError(err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container" style={{ alignItems: 'center', justifyContent: 'center' }}>
      <div className="glass animate-fade-in" style={{ width: '100%', maxWidth: '400px', padding: '2.5rem', borderRadius: '16px' }}>
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div style={{ display: 'inline-flex', padding: '12px', background: 'var(--accent-primary)', borderRadius: '50%', marginBottom: '1rem', boxShadow: '0 4px 12px rgba(99, 102, 241, 0.4)' }}>
            <Sparkles size={28} color="white" />
          </div>
          <h2 style={{ marginBottom: '0.5rem' }}>Welcome to Aspira</h2>
          <p style={{ color: 'var(--text-secondary)' }}>
            {isLogin ? 'Sign in to continue your interviews' : 'Create an account to get started'}
          </p>
        </div>

        {error && (
          <div style={{ background: 'rgba(239, 68, 68, 0.1)', borderLeft: '4px solid var(--danger)', padding: '0.75rem 1rem', borderRadius: '4px', marginBottom: '1.5rem', color: 'var(--danger)', fontSize: '0.875rem' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '1.25rem' }}>
            <label>Username</label>
            <div style={{ position: 'relative' }}>
              <User size={18} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              <input 
                type="text" 
                placeholder="Enter your username" 
                value={username} 
                onChange={(e) => setUsername(e.target.value)} 
                required 
                style={{ paddingLeft: '2.5rem' }}
              />
            </div>
          </div>

          <div style={{ marginBottom: '2rem' }}>
            <label>Password</label>
            <div style={{ position: 'relative' }}>
              <Lock size={18} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              <input 
                type="password" 
                placeholder="••••••••" 
                value={password} 
                onChange={(e) => setPassword(e.target.value)} 
                required 
                style={{ paddingLeft: '2.5rem' }}
              />
            </div>
          </div>

          {!isLogin && (
            <div style={{ marginBottom: '2rem' }}>
              <label>Groq API Key</label>
              <div style={{ position: 'relative' }}>
                <Lock size={18} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                <input 
                  type="password" 
                  placeholder="gsk_..." 
                  value={groqKey} 
                  onChange={(e) => setGroqKey(e.target.value)} 
                  required 
                  style={{ paddingLeft: '2.5rem' }}
                />
              </div>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '6px' }}>
                Required for the AI to function. It will be securely stored.
              </p>
            </div>
          )}

          <button type="submit" className="btn btn-primary" style={{ width: '100%' }} disabled={loading}>
            {loading ? 'Processing...' : (isLogin ? 'Sign In' : 'Create Account')}
            {!loading && <ArrowRight size={18} />}
          </button>
        </form>

        <div style={{ textAlign: 'center', marginTop: '1.5rem' }}>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
            {isLogin ? "Don't have an account?" : "Already have an account?"}
            <button 
              onClick={() => setIsLogin(!isLogin)} 
              style={{ background: 'none', border: 'none', color: 'var(--accent-primary)', marginLeft: '0.5rem', cursor: 'pointer', fontWeight: '500' }}
            >
              {isLogin ? 'Sign Up' : 'Sign In'}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}

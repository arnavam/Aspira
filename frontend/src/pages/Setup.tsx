import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { UploadCloud, FileText, ArrowRight, Briefcase, Building2, ListChecks } from 'lucide-react';
import { api } from '../services/api';

export default function Setup() {
  const [file, setFile] = useState<File | null>(null);
  const [sessionName, setSessionName] = useState('');
  const [company, setCompany] = useState('');
  const [role, setRole] = useState('');
  const [requirements, setRequirements] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0];
      if (selected.type === 'application/pdf') {
        setFile(selected);
        setError('');
      } else {
        setError('Please upload a valid PDF file.');
      }
    }
  };

  const isNewInterview = sessionName.trim() !== '' || company.trim() !== '' || role.trim() !== '' || requirements.trim() !== '' || file !== null;

  const handleStartInterview = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    if (!isNewInterview) {
      // Just resume the latest interview
      navigate('/interview');
      return;
    }

    // Generate or use provided conversation ID for this session
    const formattedName = sessionName.trim().toLowerCase().replace(/[^a-z0-9]+/g, '-');
    const conversationId = formattedName ? `${formattedName}-${Date.now()}` : `interview-${Date.now()}`;

    try {
      // 1. Upload new resume if provided
      if (file) {
        await api.uploadResume(file);
      }
      
      // 2. Save metadata for this interview
      if (company || role || requirements) {
        await api.setupInterview(conversationId, company, role, requirements);
      }
      
      // 3. Navigate to interview and pass the conversationId
      navigate('/interview', { state: { newConversationId: conversationId } });
    } catch (err: any) {
      setError(err.message || 'Failed to setup interview');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container" style={{ alignItems: 'center', justifyContent: 'center', overflowY: 'auto' }}>
      <div className="glass-panel animate-fade-in" style={{ width: '100%', maxWidth: '600px', padding: '3rem', margin: '2rem 0' }}>
        <h2 style={{ marginBottom: '0.5rem', color: 'var(--text-primary)' }}>Configure Interview</h2>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem', fontFamily: 'var(--font-ui)' }}>
          Provide the details of the role you are targeting. Aspira will adapt its questions.
        </p>

        {error && (
          <div style={{ background: 'rgba(239, 68, 68, 0.1)', borderLeft: '4px solid var(--danger)', padding: '12px 16px', borderRadius: '4px', marginBottom: '1.5rem', color: 'var(--danger)', fontSize: '0.875rem' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleStartInterview}>
          <div style={{ marginBottom: '1.5rem' }}>
            <label>Session Name (Optional)</label>
            <input 
              type="text" 
              placeholder="e.g. Google Frontend Interview" 
              value={sessionName}
              onChange={e => setSessionName(e.target.value)}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
            <div>
              <label><Building2 size={14} style={{ display: 'inline', verticalAlign: '-2px', marginRight: '4px' }}/> Company</label>
              <input 
                type="text" 
                placeholder="e.g. Acme Corp" 
                value={company}
                onChange={e => setCompany(e.target.value)}
              />
            </div>
            <div>
              <label><Briefcase size={14} style={{ display: 'inline', verticalAlign: '-2px', marginRight: '4px' }}/> Target Role</label>
              <input 
                type="text" 
                placeholder="e.g. Senior Frontend Engineer" 
                value={role}
                onChange={e => setRole(e.target.value)}
              />
            </div>
          </div>

          <div style={{ marginBottom: '2rem' }}>
            <label><ListChecks size={14} style={{ display: 'inline', verticalAlign: '-2px', marginRight: '4px' }}/> Job Requirements / Description</label>
            <textarea 
              placeholder="Paste the job description or key requirements here..." 
              value={requirements}
              onChange={e => setRequirements(e.target.value)}
              style={{ minHeight: '120px', resize: 'vertical' }}
            />
          </div>

          <h3 style={{ fontSize: '1.1rem', marginBottom: '1rem', fontFamily: 'var(--font-ui)' }}>Resume (Context)</h3>
          
          <div 
            onClick={() => fileInputRef.current?.click()}
            style={{ 
              border: `1px dashed ${file ? 'var(--success)' : 'var(--glass-border)'}`, 
              borderRadius: '12px', 
              padding: '2rem', 
              cursor: 'pointer',
              transition: 'all 0.2s',
              background: 'rgba(0,0,0,0.2)',
              marginBottom: '2rem',
              textAlign: 'center'
            }}
          >
            <input 
              type="file" 
              ref={fileInputRef} 
              onChange={handleFileChange} 
              accept="application/pdf" 
              style={{ display: 'none' }} 
            />
            
            {file ? (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.75rem' }}>
                <div style={{ color: 'var(--success)' }}>
                  <FileText size={32} />
                </div>
                <div>
                  <p style={{ fontWeight: '500', fontFamily: 'var(--font-ui)' }}>{file.name}</p>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                </div>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.75rem' }}>
                <UploadCloud size={32} color="var(--text-secondary)" />
                <p style={{ color: 'var(--text-primary)', fontFamily: 'var(--font-ui)', fontWeight: 500 }}>Upload New Resume</p>
                <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>Or leave blank to use your previously saved resume.</p>
              </div>
            )}
          </div>

          <button type="submit" className="btn btn-primary" disabled={loading} style={{ width: '100%' }}>
            {loading ? 'Initializing Protocol...' : (isNewInterview ? 'Start New Interview' : 'Resume Interview')} {!loading && <ArrowRight size={18} />}
          </button>
        </form>
      </div>
    </div>
  );
}

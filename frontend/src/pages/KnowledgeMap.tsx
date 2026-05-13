import { useState, useEffect, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api } from '../services/api';
import { ArrowLeft, RefreshCw, Zap } from 'lucide-react';

type KeywordEntry = {
  keyword: string;
  score: number;
};

export default function KnowledgeMap() {
  const [htmlContent, setHtmlContent] = useState<string | null>(null);
  const [keywords, setKeywords] = useState<KeywordEntry[]>([]);
  const [metadata, setMetadata] = useState<any>({});
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const conversationId = id || 'default';

  const fetchGraph = useCallback(async () => {
    try {
      // Fetch both metadata/keywords and the HTML representation
      const [data, htmlData] = await Promise.all([
        api.getKnowledgeGraph(conversationId),
        api.getKnowledgeGraphHtml(conversationId)
      ]);
      
      setKeywords(data.keywords || []);
      setMetadata(data.metadata || {});
      setHtmlContent(htmlData.html_content || null);
    } catch (err) {
      console.error('Failed to fetch knowledge graph', err);
    } finally {
      setLoading(false);
    }
  }, [conversationId]);

  // Initial fetch
  useEffect(() => {
    fetchGraph();
  }, [fetchGraph]);

  // Auto-refresh every 8 seconds
  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(fetchGraph, 8000);
    return () => clearInterval(interval);
  }, [autoRefresh, fetchGraph]);

  return (
    <div className="app-container" style={{ background: 'var(--bg-primary)', overflow: 'hidden', display: 'flex', flexDirection: 'column', height: '100vh' }}>
      
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '1.5rem 2rem', borderBottom: '1px solid var(--glass-border)', flexShrink: 0 }}>
        <button className="btn btn-secondary btn-icon" onClick={() => navigate('/interview')} style={{ borderRadius: '50%', width: '40px', height: '40px', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--glass-border)', color: 'var(--text-secondary)', cursor: 'pointer' }}>
          <ArrowLeft size={18} />
        </button>
        <div style={{ flex: 1 }}>
          <h1 style={{ fontSize: '1.3rem', fontFamily: 'var(--font-heading)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Zap size={18} color="var(--accent-secondary)" />
            Knowledge Map
          </h1>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
            {metadata.company ? `${metadata.company}` : 'Interview'} {metadata.role ? `· ${metadata.role}` : ''}
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            style={{
              display: 'flex', alignItems: 'center', gap: '6px',
              padding: '6px 14px', borderRadius: '20px', fontSize: '0.8rem', fontWeight: 500,
              background: autoRefresh ? 'rgba(16, 185, 129, 0.15)' : 'rgba(255,255,255,0.05)',
              color: autoRefresh ? 'var(--success)' : 'var(--text-secondary)',
              border: `1px solid ${autoRefresh ? 'rgba(16, 185, 129, 0.3)' : 'var(--glass-border)'}`,
              cursor: 'pointer', transition: 'all 0.2s',
            }}
          >
            <RefreshCw size={12} className={autoRefresh ? 'spin-slow' : ''} />
            {autoRefresh ? 'Live' : 'Paused'}
          </button>
          <button
            onClick={fetchGraph}
            style={{
              padding: '6px 14px', borderRadius: '20px', fontSize: '0.8rem',
              background: 'rgba(255,255,255,0.05)', color: 'var(--text-secondary)',
              border: '1px solid var(--glass-border)', cursor: 'pointer',
            }}
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>

        {/* Graph HTML Container */}
        <div style={{ flex: 1, position: 'relative' }}>
          {loading && !htmlContent ? (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-muted)' }}>
              Loading graph...
            </div>
          ) : !htmlContent ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: '16px' }}>
              <Zap size={48} color="var(--text-muted)" />
              <h3 style={{ color: 'var(--text-secondary)' }}>No graph data yet</h3>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', maxWidth: '400px', textAlign: 'center' }}>
                Start answering questions in your interview. The knowledge map will grow as Aspira analyzes your responses.
              </p>
            </div>
          ) : (
            <iframe
              title="Knowledge Graph"
              srcDoc={htmlContent}
              style={{ width: '100%', height: '100%', border: 'none', display: 'block' }}
            />
          )}
        </div>

        {/* Sidebar Panel */}
        <div style={{
          width: '280px', borderLeft: '1px solid var(--glass-border)',
          padding: '1.5rem', overflowY: 'auto', flexShrink: 0,
          display: 'flex', flexDirection: 'column', gap: '2rem',
        }}>
          {/* Live Keywords */}
          {keywords.length > 0 ? (
            <div>
              <h4 style={{ fontSize: '0.7rem', color: 'var(--accent-primary)', letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: '12px', fontWeight: 700 }}>
                Top Keywords
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {keywords.slice(0, 15).map((kw) => (
                  <div key={kw.keyword}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px', fontSize: '0.8rem' }}>
                      <span style={{ color: 'var(--text-secondary)' }}>{kw.keyword}</span>
                      <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>{(kw.score * 100).toFixed(0)}%</span>
                    </div>
                    <div style={{ width: '100%', height: '4px', background: 'rgba(255,255,255,0.06)', borderRadius: '2px', overflow: 'hidden' }}>
                      <div style={{
                        height: '100%', borderRadius: '2px',
                        background: `linear-gradient(90deg, var(--accent-primary), var(--accent-secondary))`,
                        width: `${Math.min(kw.score * 100, 100)}%`,
                        transition: 'width 0.5s ease',
                      }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div>
              <h4 style={{ fontSize: '0.7rem', color: 'var(--accent-primary)', letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: '12px', fontWeight: 700 }}>
                Top Keywords
              </h4>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No keywords identified yet.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

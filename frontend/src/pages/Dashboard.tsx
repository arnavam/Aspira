import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api } from '../services/api';
import { ArrowLeft, BarChart3, MessageSquare, Award } from 'lucide-react';

export default function Dashboard() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const conversationId = id || "default";
        const dashboardData = await api.getDashboard(conversationId);
        setData(dashboardData);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchDashboard();
  }, [id]);

  return (
    <div className="app-container" style={{ background: 'var(--bg-primary)', overflowY: 'auto' }}>
      <div style={{ maxWidth: '1000px', margin: '0 auto', padding: '3rem 2rem', width: '100%' }}>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '3rem' }}>
          <button className="btn btn-secondary btn-icon" onClick={() => navigate('/interview')} style={{ borderRadius: '50%' }}>
            <ArrowLeft size={20} />
          </button>
          <h1 style={{ fontSize: '2rem' }}>Interview Performance</h1>
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '4rem', color: 'var(--text-muted)' }}>Loading analytics...</div>
        ) : !data ? (
          <div style={{ textAlign: 'center', padding: '4rem', background: 'var(--bg-secondary)', borderRadius: '16px' }}>
            <BarChart3 size={48} color="var(--text-muted)" style={{ marginBottom: '1rem' }} />
            <h3>No data available</h3>
            <p style={{ color: 'var(--text-secondary)' }}>Complete an interview to see your performance metrics.</p>
          </div>
        ) : (
          <div className="animate-fade-in">
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1.5rem', marginBottom: '3rem' }}>
              <div className="glass" style={{ padding: '1.5rem', borderRadius: '16px', display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <div style={{ padding: '1rem', background: 'rgba(99, 102, 241, 0.1)', borderRadius: '12px', color: 'var(--accent-primary)' }}>
                  <MessageSquare size={24} />
                </div>
                <div>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>Total Questions</p>
                  <h3 style={{ fontSize: '1.5rem' }}>{data.metrics?.total_questions || 0}</h3>
                </div>
              </div>
              <div className="glass" style={{ padding: '1.5rem', borderRadius: '16px', display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <div style={{ padding: '1rem', background: 'rgba(16, 185, 129, 0.1)', borderRadius: '12px', color: 'var(--success)' }}>
                  <Award size={24} />
                </div>
                <div>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>Average Score</p>
                  <h3 style={{ fontSize: '1.5rem' }}>{data.evaluation?.overall_score ? (data.evaluation.overall_score / 2).toFixed(1) : 0} / 5</h3>
                </div>
              </div>
            </div>

            <div className="glass" style={{ padding: '2rem', borderRadius: '16px' }}>
              <h3 style={{ marginBottom: '1.5rem' }}>Keyword Performance</h3>
              {data.keywords && data.keywords.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  {data.keywords.map((kwObj: any) => (
                    <div key={kwObj.keyword}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', fontSize: '0.875rem' }}>
                        <span style={{ fontWeight: '500' }}>{kwObj.keyword}</span>
                        <span>{(kwObj.score * 100).toFixed(0)}%</span>
                      </div>
                      <div style={{ width: '100%', height: '8px', background: 'rgba(255,255,255,0.1)', borderRadius: '4px', overflow: 'hidden' }}>
                        <div style={{ height: '100%', background: 'linear-gradient(90deg, var(--accent-primary), var(--accent-secondary))', width: `${kwObj.score * 100}%`, borderRadius: '4px' }} />
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p style={{ color: 'var(--text-secondary)' }}>No keywords analyzed yet.</p>
              )}
            </div>

            {data.history && data.history.length > 0 && (
              <div className="glass" style={{ padding: '2rem', borderRadius: '16px', marginTop: '1.5rem' }}>
                <h3 style={{ marginBottom: '1.5rem' }}>Session Transcript</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', maxHeight: '400px', overflowY: 'auto', paddingRight: '1rem' }}>
                  {data.history.map((msg: string, i: number) => {
                    const isUser = msg.startsWith("User:");
                    const isSystem = msg.startsWith("[");
                    if (isSystem) return null;
                    return (
                      <div key={i} style={{ padding: '1rem', background: isUser ? 'rgba(99, 102, 241, 0.1)' : 'rgba(255,255,255,0.03)', borderRadius: '8px', borderLeft: isUser ? '3px solid var(--accent-primary)' : '3px solid var(--text-secondary)' }}>
                        <span style={{ fontSize: '0.75rem', color: isUser ? 'var(--accent-primary)' : 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '4px', display: 'block' }}>
                          {isUser ? 'You' : 'Interviewer'}
                        </span>
                        <p style={{ fontSize: '0.9rem', color: 'var(--text-primary)', lineHeight: 1.5 }}>
                          {msg.replace(/^(User:|Interviewer:)/, '').trim()}
                        </p>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

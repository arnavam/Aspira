import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api } from '../services/api';
import { ArrowLeft, RefreshCw, Zap } from 'lucide-react';

type GraphNode = {
  id: string;
  type: string;
  content: string;
  metadata?: Record<string, any>;
};

type GraphEdge = {
  source: string;
  target: string;
  relation: string;
};

type KeywordEntry = {
  keyword: string;
  score: number;
};

const NODE_COLORS: Record<string, string> = {
  answer: '#705CFF',
  topic: '#DDA15E',
  document: '#10B981',
  question: '#38BDF8',
  source: '#F472B6',
};

const NODE_RADII: Record<string, number> = {
  answer: 18,
  topic: 14,
  document: 10,
  question: 12,
  source: 10,
};

export default function KnowledgeMap() {
  const [graphData, setGraphData] = useState<{ nodes: GraphNode[]; edges: GraphEdge[] } | null>(null);
  const [keywords, setKeywords] = useState<KeywordEntry[]>([]);
  const [metadata, setMetadata] = useState<any>({});
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const nodePositions = useRef<Map<string, { x: number; y: number }>>(new Map());
  const animationRef = useRef<number>(0);

  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const conversationId = id || 'default';

  const fetchGraph = useCallback(async () => {
    try {
      const data = await api.getKnowledgeGraph(conversationId);
      const graph = data.graph || {};
      setGraphData({
        nodes: graph.nodes || [],
        edges: graph.edges || [],
      });
      setKeywords(data.keywords || []);
      setMetadata(data.metadata || {});
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

  // Layout nodes in a force-directed-like pattern using a simple radial layout
  useEffect(() => {
    if (!graphData || graphData.nodes.length === 0) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size
    const container = canvas.parentElement;
    if (container) {
      canvas.width = container.clientWidth;
      canvas.height = container.clientHeight;
    }

    const cx = canvas.width / 2;
    const cy = canvas.height / 2;
    const nodes = graphData.nodes;
    const edges = graphData.edges;

    // Group nodes by type for radial placement
    const typeGroups: Record<string, GraphNode[]> = {};
    for (const node of nodes) {
      const type = node.type || 'topic';
      if (!typeGroups[type]) typeGroups[type] = [];
      typeGroups[type].push(node);
    }

    const typeOrder = ['answer', 'topic', 'document', 'question', 'source'];
    let ringIndex = 0;
    const positions = new Map<string, { x: number; y: number }>();

    for (const type of typeOrder) {
      const group = typeGroups[type];
      if (!group || group.length === 0) continue;

      const radius = 60 + ringIndex * 100;
      const angleStep = (2 * Math.PI) / group.length;
      const offset = ringIndex * 0.5;

      group.forEach((node, i) => {
        const angle = angleStep * i + offset;
        positions.set(node.id, {
          x: cx + radius * Math.cos(angle),
          y: cy + radius * Math.sin(angle),
        });
      });
      ringIndex++;
    }

    // Handle any types not in the predefined order
    for (const [type, group] of Object.entries(typeGroups)) {
      if (typeOrder.includes(type)) continue;
      const radius = 60 + ringIndex * 100;
      const angleStep = (2 * Math.PI) / group.length;
      group.forEach((node, i) => {
        const angle = angleStep * i;
        positions.set(node.id, {
          x: cx + radius * Math.cos(angle),
          y: cy + radius * Math.sin(angle),
        });
      });
      ringIndex++;
    }

    nodePositions.current = positions;

    // Draw function
    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Draw edges
      for (const edge of edges) {
        const from = positions.get(edge.source);
        const to = positions.get(edge.target);
        if (!from || !to) continue;

        ctx.beginPath();
        ctx.moveTo(from.x, from.y);
        ctx.lineTo(to.x, to.y);
        ctx.strokeStyle = 'rgba(112, 92, 255, 0.15)';
        ctx.lineWidth = 1;
        ctx.stroke();
      }

      // Draw nodes
      for (const node of nodes) {
        const pos = positions.get(node.id);
        if (!pos) continue;

        const color = NODE_COLORS[node.type] || '#705CFF';
        const radius = NODE_RADII[node.type] || 10;

        // Glow
        ctx.beginPath();
        ctx.arc(pos.x, pos.y, radius + 6, 0, Math.PI * 2);
        const glow = ctx.createRadialGradient(pos.x, pos.y, radius, pos.x, pos.y, radius + 6);
        glow.addColorStop(0, color + '40');
        glow.addColorStop(1, 'transparent');
        ctx.fillStyle = glow;
        ctx.fill();

        // Node circle
        ctx.beginPath();
        ctx.arc(pos.x, pos.y, radius, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();

        // Label (truncated)
        const label = (node.content || node.id).substring(0, 18);
        ctx.font = '10px "DM Sans", sans-serif';
        ctx.fillStyle = '#F8F9FA';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'top';
        ctx.fillText(label, pos.x, pos.y + radius + 6);
      }
    };

    draw();

    // Cleanup
    return () => {
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
    };
  }, [graphData]);

  // Canvas mouse hover for tooltip
  const handleCanvasMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas || !graphData) return;

    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;

    let found: GraphNode | null = null;
    for (const node of graphData.nodes) {
      const pos = nodePositions.current.get(node.id);
      if (!pos) continue;
      const r = NODE_RADII[node.type] || 10;
      const dist = Math.sqrt((mx - pos.x) ** 2 + (my - pos.y) ** 2);
      if (dist <= r + 4) {
        found = node;
        break;
      }
    }

    setHoveredNode(found);
    if (found) {
      setTooltipPos({ x: e.clientX, y: e.clientY });
    }
  };

  const nodeCount = graphData?.nodes.length || 0;
  const edgeCount = graphData?.edges.length || 0;

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

        {/* Graph Canvas */}
        <div style={{ flex: 1, position: 'relative' }}>
          {loading ? (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-muted)' }}>
              Loading graph...
            </div>
          ) : nodeCount === 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: '16px' }}>
              <Zap size={48} color="var(--text-muted)" />
              <h3 style={{ color: 'var(--text-secondary)' }}>No graph data yet</h3>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', maxWidth: '400px', textAlign: 'center' }}>
                Start answering questions in your interview. The knowledge map will grow as Aspira analyzes your responses.
              </p>
            </div>
          ) : (
            <canvas
              ref={canvasRef}
              onMouseMove={handleCanvasMouseMove}
              onMouseLeave={() => setHoveredNode(null)}
              style={{ width: '100%', height: '100%', display: 'block', cursor: hoveredNode ? 'pointer' : 'default' }}
            />
          )}

          {/* Tooltip */}
          {hoveredNode && (
            <div style={{
              position: 'fixed', left: tooltipPos.x + 12, top: tooltipPos.y - 12,
              background: 'var(--glass-bg-solid)', border: '1px solid var(--glass-border)',
              borderRadius: '8px', padding: '10px 14px', maxWidth: '280px',
              pointerEvents: 'none', zIndex: 100,
              boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                <span style={{
                  width: '8px', height: '8px', borderRadius: '50%',
                  background: NODE_COLORS[hoveredNode.type] || '#705CFF',
                  display: 'inline-block',
                }} />
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                  {hoveredNode.type}
                </span>
              </div>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-primary)', lineHeight: 1.4 }}>
                {hoveredNode.content}
              </p>
            </div>
          )}
        </div>

        {/* Sidebar Panel */}
        <div style={{
          width: '280px', borderLeft: '1px solid var(--glass-border)',
          padding: '1.5rem', overflowY: 'auto', flexShrink: 0,
          display: 'flex', flexDirection: 'column', gap: '2rem',
        }}>
          {/* Stats */}
          <div>
            <h4 style={{ fontSize: '0.7rem', color: 'var(--accent-primary)', letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: '12px', fontWeight: 700 }}>
              Graph Stats
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Nodes</span>
                <span style={{ fontWeight: 600 }}>{nodeCount}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Connections</span>
                <span style={{ fontWeight: 600 }}>{edgeCount}</span>
              </div>
            </div>
          </div>

          {/* Legend */}
          <div>
            <h4 style={{ fontSize: '0.7rem', color: 'var(--accent-primary)', letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: '12px', fontWeight: 700 }}>
              Node Types
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {Object.entries(NODE_COLORS).map(([type, color]) => (
                <div key={type} style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.8rem' }}>
                  <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: color, display: 'inline-block', boxShadow: `0 0 8px ${color}60` }} />
                  <span style={{ color: 'var(--text-secondary)', textTransform: 'capitalize' }}>{type}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Live Keywords */}
          {keywords.length > 0 && (
            <div>
              <h4 style={{ fontSize: '0.7rem', color: 'var(--accent-primary)', letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: '12px', fontWeight: 700 }}>
                Top Keywords
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {keywords.slice(0, 10).map((kw) => (
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
          )}
        </div>
      </div>
    </div>
  );
}

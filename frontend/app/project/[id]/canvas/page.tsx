'use client';

import React, { useCallback, useEffect } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import {
  ReactFlow,
  Background,
  Controls,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  Edge,
  Node,
  BackgroundVariant
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { ArrowLeft, Save, Sparkles, Loader2 } from 'lucide-react';
import { fetchWithAuth } from '@/lib/api';

const initialNodes: Node[] = [
  {
    id: 'client',
    type: 'input',
    data: { label: 'Web/Mobile Client (Next.js)' },
    position: { x: 50, y: 150 },
    style: { background: '#0f172a', border: '1px solid #3b82f6', color: '#fff', borderRadius: '8px', padding: '10px' }
  },
  {
    id: 'api-gateway',
    data: { label: 'API Gateway (FastAPI)' },
    position: { x: 250, y: 150 },
    style: { background: '#0f172a', border: '1px solid #8b5cf6', color: '#fff', borderRadius: '8px', padding: '10px' }
  },
  {
    id: 'auth-service',
    data: { label: 'Auth Middleware (Supabase)' },
    position: { x: 250, y: 20 },
    style: { background: '#0f172a', border: '1px solid #ec4899', color: '#fff', borderRadius: '8px', padding: '10px' }
  },
  {
    id: 'db',
    type: 'output',
    data: { label: 'Relational Database (PostgreSQL)' },
    position: { x: 500, y: 100 },
    style: { background: '#0f172a', border: '1px solid #10b981', color: '#fff', borderRadius: '8px', padding: '10px' }
  },
  {
    id: 'redis',
    data: { label: 'Message Queue & Cache (Redis)' },
    position: { x: 500, y: 220 },
    style: { background: '#0f172a', border: '1px solid #ef4444', color: '#fff', borderRadius: '8px', padding: '10px' }
  },
  {
    id: 'celery-worker',
    type: 'output',
    data: { label: 'Task Worker (Celery)' },
    position: { x: 750, y: 220 },
    style: { background: '#0f172a', border: '1px solid #f59e0b', color: '#fff', borderRadius: '8px', padding: '10px' }
  }
];

const initialEdges: Edge[] = [
  { id: 'e1-2', source: 'client', target: 'api-gateway', animated: true, label: 'JSON HTTP' },
  { id: 'e2-3', source: 'api-gateway', target: 'auth-service', style: { stroke: '#ec4899' } },
  { id: 'e2-4', source: 'api-gateway', target: 'db', label: 'SQL queries' },
  { id: 'e2-5', source: 'api-gateway', target: 'redis', label: 'Push job' },
  { id: 'e5-6', source: 'redis', target: 'celery-worker', animated: true }
];

export default function DesignCanvas() {
  const { id } = useParams();
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [loading, setLoading] = React.useState(true);
  const [isSaving, setIsSaving] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    async function loadCanvas() {
      try {
        setLoading(true);
        setError(null);
        const data = await fetchWithAuth(`/api/projects/${id}/canvas`);
        if (data && data.canvas_json) {
          const payload = data.canvas_json;
          if (Array.isArray(payload.nodes) && payload.nodes.length > 0) {
            setNodes(payload.nodes);
            setEdges(payload.edges || []);
          } else {
            // Load template elements as starting points
            setNodes(initialNodes);
            setEdges(initialEdges);
          }
        }
      } catch (err: any) {
        console.error('Failed to load canvas state:', err);
        setError('Failed to load layout from backend. Using initial template.');
        setNodes(initialNodes);
        setEdges(initialEdges);
      } finally {
        setLoading(false);
      }
    }
    loadCanvas();
  }, [id, setNodes, setEdges]);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const handleSaveCanvas = async () => {
    setIsSaving(true);
    try {
      await fetchWithAuth(`/api/projects/${id}/canvas`, {
        method: 'PUT',
        body: JSON.stringify({
          canvas_json: { nodes, edges, viewport: { x: 0, y: 0, zoom: 1 } }
        })
      });
      alert('Canvas state saved successfully!');
    } catch (err: any) {
      console.error('Failed to save canvas:', err);
      alert(`Save failed: ${err.message || 'Failed to write canvas updates.'}`);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="h-screen flex flex-col bg-slate-950 text-slate-100 font-sans">
      {/* Header bar */}
      <header className="relative z-10 border-b border-slate-900/80 bg-slate-950/80 backdrop-blur-md px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href={`/project/${id}`} className="text-slate-400 hover:text-slate-200 transition-colors">
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <h1 className="font-bold text-base text-slate-100">System Design Canvas</h1>
            <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">React Flow Graph</span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleSaveCanvas}
            disabled={isSaving}
            className="bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg px-4 py-2 text-xs font-semibold flex items-center gap-1.5 cursor-pointer disabled:opacity-50 transition-all shadow-lg shadow-indigo-500/10"
          >
            {isSaving ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Save className="h-3.5 w-3.5" />
            )}
            Save Layout
          </button>
        </div>
      </header>

      {/* Main Canvas Workspace */}
      <div className="flex-1 relative">
        <div className="absolute top-4 left-4 z-10 bg-slate-900/85 backdrop-blur border border-slate-800 rounded-lg px-3 py-2 flex items-center gap-2 text-xs text-indigo-400 pointer-events-none shadow-md">
          <Sparkles className="h-4 w-4" />
          <span>Interactive React Flow diagram. Drag nodes, adjust connectors, and map elements.</span>
        </div>

        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          fitView
          className="bg-slate-950"
        >
          <Background variant={BackgroundVariant.Dots} gap={16} size={1} color="#334155" />
          <Controls className="bg-slate-900 border border-slate-800 text-slate-200 fill-slate-200" />
        </ReactFlow>
      </div>
    </div>
  );
}

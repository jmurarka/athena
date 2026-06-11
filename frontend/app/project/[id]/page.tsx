'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { 
  FileText, 
  Map, 
  Settings, 
  TrendingUp, 
  AlertTriangle, 
  ArrowLeft,
  ArrowRight,
  Sparkles,
  GitBranch,
  Loader2
} from 'lucide-react';
import { fetchWithAuth } from '@/lib/api';

interface PageItem {
  type: string;
  title: string;
  icon: any;
  desc: string;
}

export default function ProjectWorkspace() {
  const { id } = useParams();
  const [project, setProject] = useState<any>(null);
  const [agentRuns, setAgentRuns] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;

    // Load initial project details
    async function loadProject() {
      try {
        setError(null);
        const data = await fetchWithAuth(`/api/projects/${id}`);
        setProject(data);
      } catch (err: any) {
        console.error('Failed to load project details:', err);
        setError('Workspace not found or you do not have permission to access it.');
      }
    }
    loadProject();

    // Subscribe to SSE real-time workspace updates
    const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const eventSource = new EventSource(`${API_URL}/api/projects/${id}/status`);

    eventSource.addEventListener('status_update', (event) => {
      try {
        const data = JSON.parse(event.data);
        setProject((prev: any) => {
          if (!prev) return null;
          return { ...prev, status: data.status };
        });
        if (Array.isArray(data.agent_runs)) {
          setAgentRuns(data.agent_runs);
        }
      } catch (err) {
        console.error('Error parsing status update event:', err);
      }
    });

    eventSource.addEventListener('error', (event) => {
      console.warn('SSE subscription connection closed or failed:', event);
      eventSource.close();
    });

    return () => {
      eventSource.close();
    };
  }, [id]);

  const pageItems: PageItem[] = [
    {
      type: 'product',
      title: 'Product Preparation & Vision',
      icon: Sparkles,
      desc: 'Target user personas, epic features, core vision statement, and NFR metrics.'
    },
    {
      type: 'market',
      title: 'Market Research',
      icon: TrendingUp,
      desc: 'Competitor mapping, market gap discovery, and value differentiation strategy.'
    },
    {
      type: 'feasibility',
      title: 'Feasibility Analysis',
      icon: AlertTriangle,
      desc: 'Technical implementation risks, resource requirements, and risk mitigations.'
    },
    {
      type: 'roadmap',
      title: 'Milestone Execution Roadmap',
      icon: Map,
      desc: 'Detailed phase timelines, deliverables, MVP specs, and V2 boundaries.'
    }
  ];

  if (!project) return null;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans">
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none z-0">
        <div className="absolute top-[-10%] right-[-10%] w-[50%] h-[50%] bg-indigo-900/10 rounded-full blur-[120px]" />
      </div>

      {/* Header bar */}
      <header className="relative z-10 border-b border-slate-900/80 bg-slate-950/80 backdrop-blur-md px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/dashboard" className="text-slate-400 hover:text-slate-200 transition-colors">
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 rounded-lg bg-gradient-to-tr from-violet-600 to-indigo-600 flex items-center justify-center">
              <span className="font-bold text-sm text-white">W</span>
            </div>
            <div>
              <h1 className="font-bold text-base text-slate-100 leading-tight">{project.title}</h1>
              <span className="text-[10px] text-slate-500 font-medium">Workspace ID: {project.id}</span>
            </div>
          </div>
        </div>
      </header>

      {/* Workspace Hub Grid */}
      <main className="relative z-10 max-w-6xl mx-auto px-6 py-12">
        {error && (
          <div className="mb-6 p-4 bg-red-950/40 border border-red-900/60 rounded-2xl text-sm text-red-400">
            {error}
          </div>
        )}

        <div className="bg-slate-900/20 border border-slate-900/80 rounded-2xl p-8 mb-8 backdrop-blur-md">
          <h2 className="text-xs uppercase font-bold text-slate-500 tracking-wider mb-2">Workspace Scope</h2>
          <p className="text-slate-300 text-sm leading-relaxed max-w-3xl">
            {project.problem_statement}
          </p>
        </div>

        {/* Real-time agent status tracker if queued/processing/failed */}
        {project.status !== 'done' && (
          <div className="bg-slate-900/40 border border-slate-900/80 rounded-2xl p-6 mb-8 backdrop-blur-md">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-bold text-sm text-slate-300 uppercase tracking-wider flex items-center gap-2">
                <GitBranch className="h-4 w-4 text-violet-500 animate-pulse" />
                Pipeline Generation Status: <span className="text-violet-400 capitalize">{project.status}</span>
              </h3>
              {project.status === 'processing' && (
                <Loader2 className="h-4 w-4 text-violet-500 animate-spin" />
              )}
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              {['product', 'system_design', 'market', 'feasibility', 'roadmap'].map((agent) => {
                const run = agentRuns.find(r => r.agent_type === agent);
                const status = run ? run.status : 'pending';
                const label = agent.replace('_', ' ');
                
                return (
                  <div key={agent} className={`border rounded-xl p-3 flex flex-col justify-between transition-all duration-300 ${
                    status === 'completed' ? 'bg-emerald-950/20 border-emerald-900/50 text-emerald-400' :
                    status === 'started' ? 'bg-violet-950/20 border-violet-900/50 text-violet-400 shadow-[0_0_15px_rgba(139,92,246,0.1)]' :
                    status === 'failed' ? 'bg-red-950/20 border-red-900/50 text-red-400' :
                    'bg-slate-950/40 border-slate-900/60 text-slate-500'
                  }`}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-[10px] uppercase font-bold tracking-wider">{label}</span>
                      {status === 'started' && <Loader2 className="h-3 w-3 animate-spin" />}
                    </div>
                    <span className="text-xs font-semibold capitalize">{status}</span>
                    {run && run.latency_ms > 0 && (
                      <span className="text-[9px] opacity-75 mt-1 block">{(run.latency_ms / 1000).toFixed(1)}s</span>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Deliverables Section */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Document Pages column */}
          <div className="md:col-span-2 space-y-4">
            <h2 className="text-sm uppercase font-bold text-slate-400 tracking-wider mb-2">Structured Product Documents</h2>
            
            <div className="grid grid-cols-1 gap-4">
              {pageItems.map((item) => {
                const Icon = item.icon;
                return (
                  <Link
                    key={item.type}
                    href={`/project/${project.id}/${item.type}`}
                    className="group bg-slate-900/30 hover:bg-slate-900/60 border border-slate-900 hover:border-slate-800/80 rounded-xl p-5 flex items-start gap-4 transition-all duration-300"
                  >
                    <div className="p-3 bg-slate-950 rounded-lg border border-slate-800/60 text-violet-400 group-hover:text-violet-300 group-hover:bg-violet-950/20 group-hover:border-violet-900/30 transition-all">
                      <Icon className="h-5 w-5" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-1">
                        <h3 className="font-bold text-slate-200 group-hover:text-slate-100 transition-colors">
                          {item.title}
                        </h3>
                        <ArrowRight className="h-4 w-4 text-slate-600 group-hover:text-violet-400 group-hover:translate-x-1 transition-all" />
                      </div>
                      <p className="text-slate-400 text-xs leading-relaxed">
                        {item.desc}
                      </p>
                    </div>
                  </Link>
                );
              })}
            </div>
          </div>

          {/* Canvas View Block */}
          <div className="md:col-span-1 space-y-4">
            <h2 className="text-sm uppercase font-bold text-slate-400 tracking-wider mb-2">Systems Layout</h2>
            
            <Link
              href={`/project/${project.id}/canvas`}
              className="group block h-[330px] relative bg-gradient-to-b from-slate-900/40 to-slate-950/20 hover:from-slate-900/60 border border-slate-900 hover:border-slate-800/80 rounded-xl overflow-hidden p-6 transition-all duration-300"
            >
              {/* Graphic element representing canvas background */}
              <div className="absolute inset-0 grid grid-cols-6 grid-rows-6 opacity-[0.03] group-hover:opacity-[0.05] pointer-events-none transition-all">
                {Array.from({ length: 36 }).map((_, i) => (
                  <div key={i} className="border border-slate-400" />
                ))}
              </div>

              <div className="relative h-full flex flex-col justify-between z-10">
                <div className="p-3 bg-slate-950 rounded-lg border border-slate-800/60 text-indigo-400 w-11 h-11 flex items-center justify-center group-hover:text-indigo-300 group-hover:bg-indigo-950/20 group-hover:border-indigo-900/30 transition-all">
                  <GitBranch className="h-5 w-5" />
                </div>
                
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-bold text-slate-200 group-hover:text-indigo-400 transition-colors">
                      Interactive Canvas
                    </h3>
                  </div>
                  <p className="text-slate-400 text-xs leading-relaxed mb-4">
                    Modify high-level diagrams, connect microservices, configure databases, and export system designs.
                  </p>
                  <span className="text-[11px] font-semibold text-indigo-400 group-hover:text-indigo-300 flex items-center gap-1 transition-colors">
                    Edit Canvas Nodes &rarr;
                  </span>
                </div>
              </div>
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}

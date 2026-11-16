'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Loader2, Sparkles, AlertCircle } from 'lucide-react';
import SidebarProjects, { ProjectItem } from './SidebarProjects';
import MiddleWorkspace from './MiddleWorkspace';
import FlowchartCanvas from './FlowchartCanvas';
import { fetchWithAuth } from '@/lib/api';

interface WorkspaceLayoutProps {
  initialProjectId?: string;
}

export default function WorkspaceLayout({ initialProjectId }: WorkspaceLayoutProps) {
  const router = useRouter();
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [activeProjectId, setActiveProjectId] = useState<string | null>(initialProjectId || null);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isCanvasExpanded, setIsCanvasExpanded] = useState(false);
  const [loading, setLoading] = useState(true);
  const [activePipelineStep, setActivePipelineStep] = useState<string | null>(null);

  // Real-time Pipeline Progress Tracking via SSE (/api/projects/:id/status)
  useEffect(() => {
    if (!activeProjectId) return;
    const active = projects.find((p) => p.id === activeProjectId);
    if (!active || (active.status !== 'processing' && active.status !== 'queued')) {
      setActivePipelineStep(null);
      return;
    }

    setActivePipelineStep('Initializing agent graph supervisor...');
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const es = new EventSource(`${apiUrl}/api/projects/${activeProjectId}/status`);

    es.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.agent_runs && Array.isArray(payload.agent_runs) && payload.agent_runs.length > 0) {
          const lastRun = payload.agent_runs[payload.agent_runs.length - 1];
          const agentName = String(lastRun.agent_type).replace('_', ' ').toUpperCase();
          setActivePipelineStep(`${agentName} Agent (${lastRun.status})`);
        }

        if (payload.status === 'done' || payload.status === 'failed') {
          setProjects((prev) =>
            prev.map((p) => (p.id === activeProjectId ? { ...p, status: payload.status } : p))
          );
          setActivePipelineStep(null);
          es.close();
        }
      } catch (e) {
        console.error('SSE status stream error:', e);
      }
    };

    es.onerror = () => {
      es.close();
    };

    return () => {
      es.close();
    };
  }, [activeProjectId, projects]);

  // Load user projects on mount
  const loadProjects = async () => {
    try {
      const data = await fetchWithAuth('/api/projects');
      if (Array.isArray(data)) {
        setProjects(data);
        // If no active project yet, select the first one
        if (!activeProjectId && data.length > 0) {
          const firstId = data[0].id;
          setActiveProjectId(firstId);
          window.history.replaceState(null, '', `/project/${firstId}`);
        }
      }
    } catch (err) {
      console.error('Failed to load projects:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProjects();
  }, []);

  // Sync if initialProjectId changes
  useEffect(() => {
    if (initialProjectId && initialProjectId !== activeProjectId) {
      setActiveProjectId(initialProjectId);
    }
  }, [initialProjectId]);

  // Project selection handler (fast shifting between projects)
  const handleSelectProject = (id: string) => {
    setActiveProjectId(id);
    window.history.pushState(null, '', `/project/${id}`);
  };

  // Project creation handler
  const handleCreateProject = async (title: string, problemStatement: string) => {
    try {
      const newProj = await fetchWithAuth('/api/projects', {
        method: 'POST',
        body: JSON.stringify({
          title,
          problem_statement: problemStatement,
        }),
      });

      if (newProj && newProj.id) {
        setProjects((prev) => [newProj, ...prev]);
        setActiveProjectId(newProj.id);
        window.history.pushState(null, '', `/project/${newProj.id}`);
      }
    } catch (err) {
      console.error('Failed to create project:', err);
      alert('Failed to launch project. Please verify server connection.');
    }
  };

  // Project deletion handler
  const handleDeleteProject = async (id: string) => {
    try {
      await fetchWithAuth(`/api/projects/${id}`, {
        method: 'DELETE',
      });
      const remaining = projects.filter((p) => p.id !== id);
      setProjects(remaining);
      if (activeProjectId === id) {
        const nextId = remaining.length > 0 ? remaining[0].id : null;
        setActiveProjectId(nextId);
        if (nextId) {
          window.history.pushState(null, '', `/project/${nextId}`);
        } else {
          window.history.pushState(null, '', '/dashboard');
        }
      }
    } catch (err) {
      console.error('Failed to delete project:', err);
      alert('Could not delete project.');
    }
  };

  const activeProject = projects.find((p) => p.id === activeProjectId);

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-white text-slate-800 font-sans">
      {/* Real-time Agent DAG Execution Progress Banner */}
      {activeProject && (activeProject.status === 'processing' || activeProject.status === 'queued') && (
        <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white text-xs px-4 py-2 flex items-center justify-between border-b border-indigo-500/30 shadow-md z-30 shrink-0">
          <div className="flex items-center gap-2.5 truncate">
            <Loader2 className="w-3.5 h-3.5 animate-spin text-indigo-400 shrink-0" />
            <span className="font-semibold text-slate-200">ATHENA Multi-Agent Orchestrator Running:</span>
            <span className="text-indigo-300 truncate font-mono text-[11px]">
              {activePipelineStep || 'Executing StateGraph nodes in background...'}
            </span>
          </div>
          <span className="text-[10px] bg-indigo-900/60 border border-indigo-700/60 px-2 py-0.5 rounded font-mono text-indigo-300 shrink-0">
            Parallel DAG Mode
          </span>
        </div>
      )}

      <div className="flex flex-1 overflow-hidden">
        {/* Left Pane: Notion-Style Sidebar Projects Switcher */}
        <SidebarProjects
          projects={projects}
          activeProjectId={activeProjectId}
          onSelectProject={handleSelectProject}
          onCreateProject={handleCreateProject}
          onDeleteProject={handleDeleteProject}
          isCollapsed={isSidebarCollapsed}
          onToggleCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
        />

        {/* Middle Pane: Agent Desktop Files & In-line Block Document Editor */}
        {!isCanvasExpanded && (
          <div className="w-1/2 min-w-[380px] h-full flex flex-col transition-all duration-200">
            <MiddleWorkspace
              projectId={activeProjectId}
              projectTitle={activeProject?.title || ''}
              problemStatement={activeProject?.problem_statement}
              projectStatus={activeProject?.status}
            />
          </div>
        )}

        {/* Right Pane: Editable Flowchart Architecture Canvas */}
        <div className={`${isCanvasExpanded ? 'w-full' : 'w-1/2'} h-full flex flex-col transition-all duration-200`}>
          <FlowchartCanvas
            projectId={activeProjectId}
            projectTitle={activeProject?.title || ''}
            isExpanded={isCanvasExpanded}
            onToggleExpand={() => setIsCanvasExpanded(!isCanvasExpanded)}
          />
        </div>
      </div>
    </div>
  );
}

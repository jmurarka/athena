'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
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
    <div className="flex h-screen w-screen overflow-hidden bg-white text-slate-800 font-sans">
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
  );
}

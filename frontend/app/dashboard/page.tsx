'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { Plus, Folder, Clock, Loader2, Play } from 'lucide-react';
import { fetchWithAuth } from '@/lib/api';

interface Project {
  id: string;
  title: string;
  problem_statement: string;
  status: 'queued' | 'processing' | 'done' | 'failed';
  created_at: string;
}

export default function Dashboard() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [title, setTitle] = useState('');
  const [problemStatement, setProblemStatement] = useState('');
  const [error, setError] = useState<string | null>(null);

  // Fetch projects from the backend API on mount
  useEffect(() => {
    async function loadProjects() {
      try {
        setError(null);
        const data = await fetchWithAuth('/api/projects');
        if (Array.isArray(data)) {
          setProjects(data);
        }
      } catch (err: any) {
        console.error('Failed to load projects from API:', err);
        setError('Failed to load projects. Please ensure you are authenticated.');
      } finally {
        setLoading(false);
      }
    }
    loadProjects();
  }, []);

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title || !problemStatement) return;
    setIsSubmitting(true);
    setError(null);
    
    try {
      const newProj = await fetchWithAuth('/api/projects', {
        method: 'POST',
        body: JSON.stringify({
          title,
          problem_statement: problemStatement,
        }),
      });
      if (newProj && newProj.id) {
        setProjects([newProj, ...projects]);
        setTitle('');
        setProblemStatement('');
      }
    } catch (err: any) {
      console.error('Failed to create project:', err);
      setError(err.message || 'Failed to trigger plan generation. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans">
      {/* Background radial gradients for glassmorphism layout */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none z-0">
        <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-violet-900/10 rounded-full blur-[120px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-blue-900/10 rounded-full blur-[120px]" />
      </div>

      <header className="relative z-10 border-b border-slate-900/80 bg-slate-950/80 backdrop-blur-md px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-lg bg-gradient-to-tr from-violet-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-violet-500/20">
            <span className="font-bold text-sm text-white">AP</span>
          </div>
          <span className="font-semibold text-lg tracking-wide bg-clip-text text-transparent bg-gradient-to-r from-slate-100 to-slate-300">
            Agentic Planner
          </span>
        </div>
        <div className="h-8 w-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-xs font-medium cursor-pointer">
          U
        </div>
      </header>

      <main className="relative z-10 max-w-7xl mx-auto px-6 py-10 grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Form: Initiate New Plan */}
        <div className="lg:col-span-1 bg-slate-900/50 backdrop-blur-md border border-slate-900 rounded-xl p-6 shadow-xl">
          <h2 className="text-xl font-bold text-slate-100 mb-2 flex items-center gap-2">
            <Plus className="h-5 w-5 text-violet-500" />
            New Project Plan
          </h2>
          <p className="text-slate-400 text-xs mb-6">
            Input a problem statement. Our orchestrator will trigger specialized agents to outline product vision and systems design.
          </p>
          
          {error && (
            <div className="mb-4 p-3 bg-red-950/40 border border-red-900/60 rounded-lg text-xs text-red-400">
              {error}
            </div>
          )}
          
          <form onSubmit={handleCreateProject} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">Project Name</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Uber for Pets"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2 text-sm text-slate-100 focus:outline-none focus:border-violet-500 transition-colors"
                required
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">Problem Statement</label>
              <textarea
                value={problemStatement}
                onChange={(e) => setProblemStatement(e.target.value)}
                placeholder="Describe your idea or challenge in detail..."
                rows={6}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2 text-sm text-slate-100 focus:outline-none focus:border-violet-500 transition-colors resize-none"
                required
              />
            </div>
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white rounded-lg py-2.5 text-sm font-semibold flex items-center justify-center gap-2 shadow-lg shadow-violet-500/10 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Orchestrating...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4" />
                  Generate Product Plan
                </>
              )}
            </button>
          </form>
        </div>

        {/* Right Section: Recent Work and List */}
        <div className="lg:col-span-2 space-y-6">
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Folder className="h-5 w-5 text-indigo-500" />
            Your Workspaces
          </h2>

          {loading ? (
            <div className="flex items-center justify-center py-20">
              <Loader2 className="h-8 w-8 text-violet-500 animate-spin" />
            </div>
          ) : projects.length === 0 ? (
            <div className="border border-dashed border-slate-800 rounded-xl p-12 text-center">
              <Folder className="h-10 w-10 text-slate-600 mx-auto mb-4" />
              <p className="text-slate-400 text-sm">No active workspaces found. Trigger your first run above!</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {projects.map((project) => (
                <div
                  key={project.id}
                  className="group relative bg-slate-900/30 hover:bg-slate-900/50 backdrop-blur-sm border border-slate-900 hover:border-slate-800/80 rounded-xl p-5 shadow transition-all duration-300 flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-start justify-between mb-3">
                      <h3 className="font-bold text-slate-200 group-hover:text-violet-400 transition-colors">
                        {project.title}
                      </h3>
                      <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded-full ${
                        project.status === 'done' ? 'bg-emerald-950 text-emerald-400 border border-emerald-900' :
                        project.status === 'processing' ? 'bg-amber-950 text-amber-400 border border-amber-900' :
                        'bg-slate-850 text-slate-400 border border-slate-800'
                      }`}>
                        {project.status}
                      </span>
                    </div>
                    <p className="text-slate-400 text-xs line-clamp-3 mb-6">
                      {project.problem_statement}
                    </p>
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-slate-500 border-t border-slate-900/50 pt-4 mt-auto">
                    <span className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {new Date(project.created_at).toLocaleDateString()}
                    </span>
                    <Link
                      href={`/project/${project.id}`}
                      className="text-violet-400 hover:text-violet-300 font-semibold flex items-center gap-1 transition-colors"
                    >
                      Open Workspace &rarr;
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

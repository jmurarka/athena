'use client';

import React, { useState } from 'react';
import { 
  Folder, 
  Plus, 
  Search, 
  Trash2, 
  ChevronRight, 
  Clock, 
  CheckCircle2, 
  Loader2, 
  Layers, 
  Settings, 
  Sparkles,
  X
} from 'lucide-react';

export interface ProjectItem {
  id: string;
  title: string;
  problem_statement: string;
  status: 'queued' | 'processing' | 'done' | 'failed';
  created_at?: string;
}

interface SidebarProjectsProps {
  projects: ProjectItem[];
  activeProjectId: string | null;
  onSelectProject: (id: string) => void;
  onCreateProject: (title: string, problemStatement: string) => Promise<void>;
  onDeleteProject: (id: string) => Promise<void>;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
}

export default function SidebarProjects({
  projects,
  activeProjectId,
  onSelectProject,
  onCreateProject,
  onDeleteProject,
  isCollapsed,
  onToggleCollapse,
}: SidebarProjectsProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newProblem, setNewProblem] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const filteredProjects = projects.filter((p) =>
    p.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (p.problem_statement && p.problem_statement.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim() || !newProblem.trim()) return;
    setIsSubmitting(true);
    try {
      await onCreateProject(newTitle.trim(), newProblem.trim());
      setNewTitle('');
      setNewProblem('');
      setShowModal(false);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (confirm('Are you sure you want to delete this project workspace?')) {
      setDeletingId(id);
      try {
        await onDeleteProject(id);
      } finally {
        setDeletingId(null);
      }
    }
  };

  if (isCollapsed) {
    return (
      <div className="w-12 bg-[#f7f7f5] border-r border-[#e9e9e7] flex flex-col items-center py-3 select-none">
        <button
          onClick={onToggleCollapse}
          title="Expand sidebar"
          className="p-1.5 rounded hover:bg-[#eaeaea] text-slate-600 transition"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
        <div className="mt-4 w-7 h-7 rounded-md bg-[#ede9fe] text-[#7c3aed] flex items-center justify-center font-bold text-xs">
          A
        </div>
        <button
          onClick={() => setShowModal(true)}
          title="New Project"
          className="mt-4 p-1.5 rounded hover:bg-[#ede9fe] text-[#7c3aed] transition"
        >
          <Plus className="w-4 h-4" />
        </button>
      </div>
    );
  }

  return (
    <>
      <aside className="w-64 bg-[#f7f7f5] border-r border-[#e9e9e7] flex flex-col h-full select-none text-[13px] font-sans">
        {/* Notion Workspace Header */}
        <div className="p-3 border-b border-[#e9e9e7] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-[#ede9fe] text-[#7c3aed] border border-[#ddd6fe] flex items-center justify-center font-bold text-xs shadow-xs">
              A
            </div>
            <div className="leading-tight">
              <span className="font-semibold text-slate-800 text-xs block truncate max-w-[130px]">
                Athena Workspace
              </span>
              <span className="text-[10px] text-slate-400 font-normal">Notion Template</span>
            </div>
          </div>
          <button
            onClick={onToggleCollapse}
            title="Collapse sidebar"
            className="p-1 text-slate-400 hover:text-slate-700 hover:bg-[#eaeaea] rounded transition"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Quick Search & Actions */}
        <div className="p-2 space-y-1.5">
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-2 text-slate-400" />
            <input
              type="text"
              placeholder="Search projects..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-[#efefed] hover:bg-[#eaeaea] focus:bg-white text-xs pl-8 pr-2.5 py-1.5 rounded-md border border-transparent focus:border-[#c4b5fd] focus:ring-1 focus:ring-[#8b5cf6] outline-none text-slate-700 placeholder-slate-400 transition"
            />
          </div>

          <button
            onClick={() => setShowModal(true)}
            className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-md bg-[#ede9fe]/80 hover:bg-[#ddd6fe] text-[#6d28d9] font-medium text-xs transition border border-[#ddd6fe]/60 shadow-xs"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>New Specification</span>
          </button>
        </div>

        {/* Projects Section Header */}
        <div className="px-3 pt-3 pb-1 flex items-center justify-between text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
          <span>Projects</span>
          <span className="text-[10px] bg-slate-200/80 px-1.5 py-0.2 rounded text-slate-600 font-mono">
            {projects.length}
          </span>
        </div>

        {/* Projects List */}
        <div className="flex-1 overflow-y-auto px-1.5 py-1 space-y-0.5">
          {filteredProjects.length === 0 ? (
            <div className="px-3 py-6 text-center text-xs text-slate-400">
              {searchQuery ? 'No matching projects' : 'No projects yet. Click "+ New Specification" to create one.'}
            </div>
          ) : (
            filteredProjects.map((p) => {
              const isActive = p.id === activeProjectId;
              return (
                <div
                  key={p.id}
                  onClick={() => onSelectProject(p.id)}
                  className={`group flex items-center justify-between px-2.5 py-1.5 rounded-md cursor-pointer transition text-xs ${
                    isActive
                      ? 'bg-[#ede9fe] text-[#5b21b6] font-medium border-l-[3px] border-[#7c3aed]'
                      : 'text-slate-700 hover:bg-[#eaeaea]'
                  }`}
                >
                  <div className="flex items-center gap-2 truncate pr-1">
                    <span className="text-sm shrink-0">
                      {p.status === 'done' ? '📋' : p.status === 'processing' ? '⚡' : '📁'}
                    </span>
                    <span className="truncate">{p.title || 'Untitled Project'}</span>
                  </div>

                  <div className="flex items-center gap-1.5 shrink-0">
                    {/* Status Dot */}
                    {p.status === 'processing' ? (
                      <span className="w-2 h-2 rounded-full bg-[#8b5cf6] animate-pulse" title="Agents Working" />
                    ) : p.status === 'done' ? (
                      <span className="w-2 h-2 rounded-full bg-emerald-500" title="Completed" />
                    ) : (
                      <span className="w-2 h-2 rounded-full bg-slate-300" title="Queued" />
                    )}

                    {/* Delete Icon */}
                    <button
                      onClick={(e) => handleDelete(e, p.id)}
                      disabled={deletingId === p.id}
                      className="opacity-0 group-hover:opacity-100 p-1 hover:text-rose-600 rounded transition"
                      title="Delete project"
                    >
                      {deletingId === p.id ? (
                        <Loader2 className="w-3 h-3 animate-spin" />
                      ) : (
                        <Trash2 className="w-3 h-3" />
                      )}
                    </button>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Sidebar Footer */}
        <div className="p-3 border-t border-[#e9e9e7] text-[11px] text-slate-400 flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" />
            <span className="text-slate-500 font-medium">Local Ollama</span>
          </div>
          <span className="font-mono text-[10px]">v1.0</span>
        </div>
      </aside>

      {/* New Project Modal (Clean Notion Style with Lavender Accent) */}
      {showModal && (
        <div className="fixed inset-0 z-50 bg-black/30 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl border border-slate-200 max-w-md w-full p-6 space-y-4 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 rounded bg-[#ede9fe] text-[#7c3aed] flex items-center justify-center text-xs font-bold">
                  +
                </div>
                <h3 className="font-semibold text-slate-800 text-sm">Create New Specification</h3>
              </div>
              <button
                onClick={() => setShowModal(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateSubmit} className="space-y-3.5">
              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">
                  Project Title
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. AI-Powered Customer Support Platform"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  className="w-full text-xs px-3 py-2 border border-slate-200 rounded-lg focus:border-[#7c3aed] focus:ring-2 focus:ring-[#ede9fe] outline-none text-slate-800 placeholder-slate-400 transition"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">
                  Problem Statement
                </label>
                <textarea
                  required
                  rows={4}
                  placeholder="Describe the user problem, target audience, technical challenges, and core objectives..."
                  value={newProblem}
                  onChange={(e) => setNewProblem(e.target.value)}
                  className="w-full text-xs px-3 py-2 border border-slate-200 rounded-lg focus:border-[#7c3aed] focus:ring-2 focus:ring-[#ede9fe] outline-none text-slate-800 placeholder-slate-400 transition resize-none"
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-3 py-1.5 rounded-lg border border-slate-200 text-xs font-medium text-slate-600 hover:bg-slate-50 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting || !newTitle.trim() || !newProblem.trim()}
                  className="px-4 py-1.5 rounded-lg bg-[#7c3aed] hover:bg-[#6d28d9] text-white text-xs font-medium transition shadow-xs disabled:opacity-50 flex items-center gap-1.5"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      <span>Generating Plan...</span>
                    </>
                  ) : (
                    <span>Create & Launch Agents</span>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}

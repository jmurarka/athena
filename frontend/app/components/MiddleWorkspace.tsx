'use client';

import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  ArrowLeft, 
  Save, 
  Plus, 
  Trash2, 
  CheckSquare, 
  Square, 
  AlertCircle, 
  Clock, 
  CheckCircle2, 
  Loader2, 
  Layers, 
  ExternalLink,
  Sparkles,
  RefreshCw,
  FolderOpen
} from 'lucide-react';
import { fetchWithAuth } from '@/lib/api';

export interface Block {
  id: string;
  type: 'h1' | 'h2' | 'h3' | 'paragraph' | 'bullet_list' | 'todo' | 'callout' | 'quote';
  content: string;
  checked?: boolean;
}

interface AgentFileConfig {
  type: string;
  title: string;
  icon: string;
  agentName: string;
  ext: string;
  description: string;
}

const AGENT_FILES: AgentFileConfig[] = [
  {
    type: 'product',
    title: 'Product Vision & Core Scope',
    icon: '📄',
    agentName: 'Product Agent',
    ext: '.spec',
    description: 'High-level product vision, user personas, MVP features, and atomic requirements.'
  },
  {
    type: 'market',
    title: 'Market & Competitive Research',
    icon: '📊',
    agentName: 'Research Agent',
    ext: '.analysis',
    description: 'Market landscape, direct competitors, differentiation strategy, and unserved gaps.'
  },
  {
    type: 'system_design',
    title: 'System Architecture & Tech Specs',
    icon: '🏛️',
    agentName: 'Architect Agent',
    ext: '.arch',
    description: 'Component architecture, database schemas, messaging queues, and API contracts.'
  },
  {
    type: 'feasibility',
    title: 'Technical Feasibility & Risks',
    icon: '⚖️',
    agentName: 'Feasibility Agent',
    ext: '.audit',
    description: 'Bottlenecks, architectural complexities, mitigation actions, and staffing requirements.'
  },
  {
    type: 'roadmap',
    title: 'Milestone Roadmap & Sprints',
    icon: '🗺️',
    agentName: 'Roadmap Agent',
    ext: '.plan',
    description: 'Phased timeline, MVP release schedule, deliverables, and deferred V2 items.'
  },
  {
    type: 'validation',
    title: 'Validation & Living Blueprint',
    icon: '🛡️',
    agentName: 'Validation Engine',
    ext: '.audit',
    description: 'Coverage score, architectural contradiction checks, and requirement validation.'
  }
];

// Helper to convert structured agent JSON into Notion blocks
const convertAgentJsonToBlocks = (json: any, pageType: string): Block[] => {
  if (json && Array.isArray(json.blocks)) {
    return json.blocks;
  }
  const result: Block[] = [];
  if (!json) return result;

  if (json.message && json.status === 'generating') {
    result.push({ id: 'b-status', type: 'callout', content: json.message });
    result.push({ id: 'b-wait', type: 'paragraph', content: 'Agent execution is running in the background. Content will refresh once completed.' });
    return result;
  }

  if (pageType === 'product') {
    if (json.vision) {
      result.push({ id: 'v-title', type: 'h1', content: 'Product Vision & Core Scope' });
      result.push({ id: 'v-desc', type: 'paragraph', content: json.vision });
    }
    if (Array.isArray(json.personas) && json.personas.length > 0) {
      result.push({ id: 'p-title', type: 'h2', content: 'Target User Personas' });
      json.personas.forEach((p: any, idx: number) => {
        result.push({
          id: `p-${idx}`,
          type: 'bullet_list',
          content: `${p.name || 'User Persona'} (${p.role || 'Role'}): ${Array.isArray(p.pains) ? p.pains.join(', ') : p.pains || ''}`
        });
      });
    }
    if (Array.isArray(json.features) && json.features.length > 0) {
      result.push({ id: 'f-title', type: 'h2', content: 'Key Feature Requirements' });
      json.features.forEach((f: any, idx: number) => {
        result.push({
          id: `f-${idx}`,
          type: 'todo',
          content: `[${f.priority || 'P1'}] ${f.name}: ${f.description || ''}`,
          checked: false
        });
      });
    }
  } else if (pageType === 'market') {
    if (Array.isArray(json.competitors) && json.competitors.length > 0) {
      result.push({ id: 'c-title', type: 'h1', content: 'Market Landscape & Key Competitors' });
      json.competitors.forEach((c: any, idx: number) => {
        result.push({
          id: `c-${idx}`,
          type: 'bullet_list',
          content: `${c.name || 'Competitor'} — Strengths: ${Array.isArray(c.strengths) ? c.strengths.join(', ') : c.strengths || ''}`
        });
      });
    }
    if (json.differentiation) {
      result.push({ id: 'd-title', type: 'h2', content: 'Differentiation Strategy' });
      result.push({ id: 'd-desc', type: 'callout', content: json.differentiation });
    }
  } else if (pageType === 'system_design') {
    result.push({ id: 'arch-title', type: 'h1', content: 'High-Level System Design' });
    if (json.summary || json.architecture_summary) {
      result.push({ id: 'arch-desc', type: 'paragraph', content: json.summary || json.architecture_summary });
    }
    if (Array.isArray(json.components) && json.components.length > 0) {
      result.push({ id: 'comp-title', type: 'h2', content: 'Core Components & Technologies' });
      json.components.forEach((c: any, idx: number) => {
        result.push({
          id: `comp-${idx}`,
          type: 'bullet_list',
          content: `${c.name || c.component_name} (${c.type || 'Service'}): ${c.tech || c.tech_stack || ''} - ${c.description || ''}`
        });
      });
    }
  } else if (pageType === 'feasibility') {
    if (json.technical_feasibility_summary) {
      result.push({ id: 'fe-title', type: 'h1', content: 'Technical Feasibility Summary' });
      result.push({ id: 'fe-desc', type: 'paragraph', content: json.technical_feasibility_summary });
    }
    if (Array.isArray(json.risks) && json.risks.length > 0) {
      result.push({ id: 'r-title', type: 'h2', content: 'Key Risks & Mitigation Matrix' });
      json.risks.forEach((r: any, idx: number) => {
        result.push({
          id: `r-${idx}`,
          type: 'bullet_list',
          content: `Risk: ${r.risk || ''} [Impact: ${r.impact || 'Medium'}] — Action: ${r.mitigation || ''}`
        });
      });
    }
  } else if (pageType === 'roadmap') {
    if (Array.isArray(json.phases) && json.phases.length > 0) {
      result.push({ id: 'ph-title', type: 'h1', content: 'Development Delivery Roadmap' });
      json.phases.forEach((p: any, idx: number) => {
        result.push({
          id: `ph-${idx}`,
          type: 'callout',
          content: `${p.phase_name || 'Phase'} (${p.duration || '2 weeks'}) — Deliverables: ${Array.isArray(p.deliverables) ? p.deliverables.join(', ') : p.deliverables || ''}`
        });
      });
    }
  } else if (pageType === 'validation') {
    result.push({ id: 'v-h1', type: 'h1', content: 'Living Blueprint Validation Audit' });
    result.push({
      id: 'v-callout',
      type: 'callout',
      content: 'Self-validating system continuously monitors requirement coverage, conflicting decisions, and architectural contradictions.'
    });
  }

  if (result.length === 0) {
    result.push({ id: '1', type: 'h1', content: 'Draft Specification' });
    result.push({ id: '2', type: 'paragraph', content: 'No structured analysis output generated yet. Agents will automatically populate this document.' });
  }

  return result;
};

interface MiddleWorkspaceProps {
  projectId: string | null;
  projectTitle: string;
  problemStatement?: string;
  projectStatus?: string;
}

export default function MiddleWorkspace({
  projectId,
  projectTitle,
  problemStatement,
  projectStatus,
}: MiddleWorkspaceProps) {
  // Navigation: null = Desktop/Files View; string = Active File Document
  const [activeFile, setActiveFile] = useState<AgentFileConfig | null>(null);

  // Document Editor State
  const [blocks, setBlocks] = useState<Block[]>([]);
  const [isLoadingDoc, setIsLoadingDoc] = useState(false);
  const [isSavingDoc, setIsSavingDoc] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [docVersion, setDocVersion] = useState<number>(1);

  // Reset to files desktop view when changing projects
  useEffect(() => {
    setActiveFile(null);
  }, [projectId]);

  // Load document when a file card is clicked
  const handleOpenFile = async (file: AgentFileConfig) => {
    if (!projectId) return;
    setActiveFile(file);
    setIsLoadingDoc(true);
    setSaveSuccess(false);

    try {
      const data = await fetchWithAuth(`/api/projects/${projectId}/pages/${file.type}`);
      if (data && data.content_json) {
        setBlocks(convertAgentJsonToBlocks(data.content_json, file.type));
        setDocVersion(data.version || 1);
      } else {
        setBlocks(convertAgentJsonToBlocks({}, file.type));
      }
    } catch (err) {
      console.error('Failed to load page content:', err);
      // Fallback
      setBlocks(convertAgentJsonToBlocks({}, file.type));
    } finally {
      setIsLoadingDoc(false);
    }
  };

  // Save changes to backend
  const handleSaveDocument = async () => {
    if (!projectId || !activeFile) return;
    setIsSavingDoc(true);
    try {
      await fetchWithAuth(`/api/projects/${projectId}/pages/${activeFile.type}`, {
        method: 'PUT',
        body: JSON.stringify({
          title: activeFile.title,
          content_json: { blocks }
        })
      });
      setSaveSuccess(true);
      setDocVersion((v) => v + 1);
      setTimeout(() => setSaveSuccess(false), 2500);
    } catch (err) {
      console.error('Failed to save document:', err);
      alert('Could not save document updates. Please try again.');
    } finally {
      setIsSavingDoc(false);
    }
  };

  // Block Editing Handlers
  const handleUpdateBlockContent = (id: string, newContent: string) => {
    setBlocks((prev) =>
      prev.map((b) => (b.id === id ? { ...b, content: newContent } : b))
    );
  };

  const handleToggleTodo = (id: string) => {
    setBlocks((prev) =>
      prev.map((b) => (b.id === id ? { ...b, checked: !b.checked } : b))
    );
  };

  const handleAddBlock = (type: Block['type']) => {
    const newBlock: Block = {
      id: `block-${Date.now()}`,
      type,
      content: type === 'h1' ? 'New Heading' : type === 'callout' ? 'Important note...' : 'Start typing...',
      checked: false
    };
    setBlocks((prev) => [...prev, newBlock]);
  };

  const handleDeleteBlock = (id: string) => {
    setBlocks((prev) => prev.filter((b) => b.id !== id));
  };

  if (!projectId) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8 bg-white text-slate-400 font-sans">
        <div className="w-12 h-12 rounded-xl bg-[#f5f3ff] text-[#7c3aed] flex items-center justify-center text-xl mb-3 border border-[#ddd6fe]">
          📋
        </div>
        <h3 className="font-semibold text-slate-700 text-sm mb-1">No Project Selected</h3>
        <p className="text-xs text-slate-400 max-w-sm text-center">
          Select an existing project from the left sidebar or create a new specification to start.
        </p>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col h-full bg-white font-sans overflow-hidden border-r border-[#eaeaea]">
      {/* Notion Top Bar / Breadcrumb */}
      <header className="h-11 px-5 border-b border-[#eaeaea] flex items-center justify-between text-xs text-slate-500 select-none shrink-0 bg-white">
        <div className="flex items-center gap-1.5 truncate">
          <span className="text-slate-400">Projects</span>
          <span className="text-slate-300">/</span>
          <span className="font-medium text-slate-800 truncate max-w-[180px]">
            {projectTitle || 'Untitled'}
          </span>
          {activeFile && (
            <>
              <span className="text-slate-300">/</span>
              <span className="flex items-center gap-1 text-[#6d28d9] font-medium bg-[#f5f3ff] px-2 py-0.5 rounded border border-[#ddd6fe]">
                <span>{activeFile.icon}</span>
                <span className="truncate max-w-[160px]">{activeFile.title}</span>
              </span>
            </>
          )}
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {projectStatus === 'processing' && (
            <span className="flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-medium bg-[#ede9fe] text-[#6d28d9] border border-[#ddd6fe]">
              <Loader2 className="w-3 h-3 animate-spin text-[#7c3aed]" />
              <span>Agents Working</span>
            </span>
          )}

          {activeFile && (
            <button
              onClick={handleSaveDocument}
              disabled={isSavingDoc}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#7c3aed] hover:bg-[#6d28d9] text-white text-xs font-medium transition shadow-xs disabled:opacity-50"
            >
              {isSavingDoc ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : saveSuccess ? (
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-300" />
              ) : (
                <Save className="w-3.5 h-3.5" />
              )}
              <span>{saveSuccess ? 'Saved' : 'Save'}</span>
            </button>
          )}
        </div>
      </header>

      {/* Mode 1: Agent Files Desktop View */}
      {!activeFile ? (
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Notion Page Cover / Header */}
          <div className="space-y-2">
            <div className="text-3xl select-none">🚀</div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">
              {projectTitle || 'Project Specification Workspace'}
            </h1>
            {problemStatement && (
              <p className="text-xs text-slate-500 leading-relaxed max-w-2xl bg-[#f8fafc] border border-slate-200 p-3 rounded-lg">
                <span className="font-semibold text-slate-700 block mb-0.5">Problem Statement:</span>
                {problemStatement}
              </p>
            )}
          </div>

          {/* Documents / Files Section */}
          <div className="space-y-3">
            <div className="flex items-center justify-between border-b border-slate-200 pb-2">
              <div className="flex items-center gap-2 text-xs font-semibold text-slate-600 uppercase tracking-wider">
                <FolderOpen className="w-3.5 h-3.5 text-[#7c3aed]" />
                <span>Agent Specification Files</span>
              </div>
              <span className="text-[11px] text-slate-400">Click any file to open document</span>
            </div>

            {/* Files Grid (Clean Notion Cards with Lavender Contrast) */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {AGENT_FILES.map((file) => (
                <div
                  key={file.type}
                  onClick={() => handleOpenFile(file)}
                  className="group bg-white hover:bg-[#fafafa] border border-slate-200 hover:border-[#c4b5fd] rounded-lg p-3.5 cursor-pointer transition shadow-xs hover:shadow-sm flex flex-col justify-between"
                >
                  <div className="space-y-2">
                    <div className="flex items-start justify-between">
                      <div className="w-8 h-8 rounded-md bg-[#f5f3ff] text-[#7c3aed] border border-[#ddd6fe] flex items-center justify-center text-lg select-none group-hover:scale-105 transition">
                        {file.icon}
                      </div>
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-100 text-slate-500 border border-slate-200">
                        {file.ext}
                      </span>
                    </div>

                    <div>
                      <h4 className="text-xs font-semibold text-slate-800 group-hover:text-[#6d28d9] transition">
                        {file.title}
                      </h4>
                      <p className="text-[11px] text-slate-500 leading-relaxed mt-1 line-clamp-2">
                        {file.description}
                      </p>
                    </div>
                  </div>

                  <div className="pt-3 mt-3 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400">
                    <span className="flex items-center gap-1 text-[#7c3aed] font-medium">
                      <Sparkles className="w-3 h-3" />
                      {file.agentName}
                    </span>
                    <span className="group-hover:translate-x-0.5 text-slate-400 group-hover:text-[#7c3aed] transition font-medium">
                      Open &rarr;
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        /* Mode 2: In-Line Notion Document Editor */
        <div className="flex-1 flex flex-col h-full overflow-hidden">
          {/* Document Sub-header */}
          <div className="px-6 py-2 border-b border-slate-100 flex items-center justify-between text-xs text-slate-500 bg-[#fbfbfa]">
            <button
              onClick={() => setActiveFile(null)}
              className="flex items-center gap-1.5 text-slate-600 hover:text-slate-900 font-medium py-1 px-2 rounded hover:bg-slate-200/60 transition"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to Desktop Files</span>
            </button>
            <div className="flex items-center gap-3 text-[11px] text-slate-400 font-mono">
              <span>Rev {docVersion}</span>
              <span>{blocks.length} blocks</span>
            </div>
          </div>

          {/* Notion Document Canvas */}
          <div className="flex-1 overflow-y-auto px-8 py-6 space-y-4 max-w-3xl w-full mx-auto">
            {/* Document Header */}
            <div className="space-y-1 pb-4 border-b border-slate-100">
              <div className="text-4xl select-none">{activeFile.icon}</div>
              <h1 className="text-2xl font-bold tracking-tight text-slate-900">
                {activeFile.title}
              </h1>
              <div className="flex items-center gap-2 text-xs text-slate-400 pt-1">
                <span className="px-2 py-0.5 rounded bg-[#ede9fe] text-[#6d28d9] font-medium border border-[#ddd6fe]">
                  {activeFile.agentName}
                </span>
                <span>•</span>
                <span>Notion Block Format</span>
              </div>
            </div>

            {/* Document Blocks */}
            {isLoadingDoc ? (
              <div className="py-12 flex flex-col items-center justify-center gap-2 text-slate-400">
                <Loader2 className="w-5 h-5 animate-spin text-[#7c3aed]" />
                <span className="text-xs">Loading document blocks...</span>
              </div>
            ) : (
              <div className="space-y-2.5">
                {blocks.map((block) => (
                  <div key={block.id} className="group relative flex items-start gap-2">
                    {/* Block Icon / Type Indicator */}
                    {block.type === 'todo' && (
                      <button
                        onClick={() => handleToggleTodo(block.id)}
                        className="mt-1 text-slate-400 hover:text-[#7c3aed] transition"
                      >
                        {block.checked ? (
                          <CheckSquare className="w-4 h-4 text-[#7c3aed]" />
                        ) : (
                          <Square className="w-4 h-4" />
                        )}
                      </button>
                    )}

                    {block.type === 'bullet_list' && (
                      <span className="text-slate-400 text-lg leading-none mt-1 select-none">•</span>
                    )}

                    {/* Block Content Input */}
                    <div className="flex-1">
                      {block.type === 'h1' ? (
                        <input
                          type="text"
                          value={block.content}
                          onChange={(e) => handleUpdateBlockContent(block.id, e.target.value)}
                          className="w-full font-bold text-lg text-slate-900 border-b border-transparent focus:border-[#7c3aed] outline-none py-1 transition bg-transparent"
                        />
                      ) : block.type === 'h2' ? (
                        <input
                          type="text"
                          value={block.content}
                          onChange={(e) => handleUpdateBlockContent(block.id, e.target.value)}
                          className="w-full font-semibold text-sm text-slate-800 border-b border-transparent focus:border-[#7c3aed] outline-none py-1 transition bg-transparent"
                        />
                      ) : block.type === 'callout' ? (
                        <div className="flex items-start gap-2 p-3 rounded-lg bg-[#f5f3ff] border border-[#ddd6fe] text-xs text-[#5b21b6]">
                          <span className="text-sm select-none">💡</span>
                          <textarea
                            rows={2}
                            value={block.content}
                            onChange={(e) => handleUpdateBlockContent(block.id, e.target.value)}
                            className="w-full bg-transparent outline-none resize-none leading-relaxed text-[#5b21b6]"
                          />
                        </div>
                      ) : (
                        <textarea
                          rows={Math.max(1, Math.ceil(block.content.length / 80))}
                          value={block.content}
                          onChange={(e) => handleUpdateBlockContent(block.id, e.target.value)}
                          className={`w-full text-xs text-slate-700 outline-none resize-none leading-relaxed py-0.5 bg-transparent border-b border-transparent focus:border-slate-300 transition ${
                            block.checked ? 'line-through text-slate-400' : ''
                          }`}
                        />
                      )}
                    </div>

                    {/* Block Delete Button */}
                    <button
                      onClick={() => handleDeleteBlock(block.id)}
                      className="opacity-0 group-hover:opacity-100 p-1 text-slate-300 hover:text-rose-500 rounded transition"
                      title="Delete block"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))}

                {/* Add Block Notion Action Bar */}
                <div className="pt-4 border-t border-slate-100 flex items-center gap-1.5 flex-wrap">
                  <span className="text-[11px] text-slate-400 mr-1 select-none">+ Add:</span>
                  <button
                    onClick={() => handleAddBlock('paragraph')}
                    className="px-2 py-1 text-[11px] rounded bg-slate-100 hover:bg-slate-200 text-slate-600 transition"
                  >
                    Paragraph
                  </button>
                  <button
                    onClick={() => handleAddBlock('h1')}
                    className="px-2 py-1 text-[11px] rounded bg-slate-100 hover:bg-slate-200 text-slate-600 transition"
                  >
                    H1 Heading
                  </button>
                  <button
                    onClick={() => handleAddBlock('h2')}
                    className="px-2 py-1 text-[11px] rounded bg-slate-100 hover:bg-slate-200 text-slate-600 transition"
                  >
                    H2 Subheading
                  </button>
                  <button
                    onClick={() => handleAddBlock('bullet_list')}
                    className="px-2 py-1 text-[11px] rounded bg-slate-100 hover:bg-slate-200 text-slate-600 transition"
                  >
                    Bullet Item
                  </button>
                  <button
                    onClick={() => handleAddBlock('todo')}
                    className="px-2 py-1 text-[11px] rounded bg-slate-100 hover:bg-slate-200 text-slate-600 transition"
                  >
                    To-Do
                  </button>
                  <button
                    onClick={() => handleAddBlock('callout')}
                    className="px-2 py-1 text-[11px] rounded bg-[#ede9fe] hover:bg-[#ddd6fe] text-[#6d28d9] transition font-medium"
                  >
                    Lavender Callout
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

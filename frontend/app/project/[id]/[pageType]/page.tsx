'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { Save, ArrowLeft, Loader2, Sparkles, AlertCircle, Plus, Trash2 } from 'lucide-react';
import { fetchWithAuth } from '@/lib/api';

interface Block {
  id: string;
  type: 'h1' | 'h2' | 'paragraph' | 'bullet_list';
  content: string;
}

// Converter from structured database formats to editor blocks
const convertJsonToBlocks = (json: any, type: string): Block[] => {
  if (json && Array.isArray(json.blocks)) {
    return json.blocks;
  }

  const result: Block[] = [];
  if (!json) return result;
  
  if (type === 'product') {
    if (json.vision) {
      result.push({ id: 'v-title', type: 'h1', content: 'Product Vision & Core Scope' });
      result.push({ id: 'v-desc', type: 'paragraph', content: json.vision });
    }
    if (Array.isArray(json.personas) && json.personas.length > 0) {
      result.push({ id: 'p-title', type: 'h2', content: 'Target User Personas' });
      json.personas.forEach((p: any, idx: number) => {
        result.push({
          id: `p-${idx}`,
          type: 'paragraph',
          content: `Persona: ${p.name || ''} (${p.role || ''}) - Pain Points: ${Array.isArray(p.pains) ? p.pains.join(', ') : p.pains || ''}`
        });
      });
    }
    if (Array.isArray(json.features) && json.features.length > 0) {
      result.push({ id: 'f-title', type: 'h2', content: 'Epic Features & Priority Matrix' });
      json.features.forEach((f: any, idx: number) => {
        result.push({
          id: `f-${idx}`,
          type: 'bullet_list',
          content: `[Priority: ${f.priority || 'Medium'}] ${f.name}: ${f.description || ''}`
        });
      });
    }
    if (Array.isArray(json.nfrs) && json.nfrs.length > 0) {
      result.push({ id: 'nfr-title', type: 'h2', content: 'Non-Functional Requirements' });
      json.nfrs.forEach((n: any, idx: number) => {
        result.push({
          id: `nfr-${idx}`,
          type: 'bullet_list',
          content: `${n.metric || ''}: ${n.value || ''}`
        });
      });
    }
  } else if (type === 'market') {
    if (Array.isArray(json.competitors) && json.competitors.length > 0) {
      result.push({ id: 'c-title', type: 'h1', content: 'Key Space Competitors' });
      json.competitors.forEach((c: any, idx: number) => {
        result.push({
          id: `c-${idx}`,
          type: 'paragraph',
          content: `Competitor: ${c.name || ''} | Strengths: ${Array.isArray(c.strengths) ? c.strengths.join(', ') : c.strengths || ''} | Gaps: ${Array.isArray(c.weaknesses) ? c.weaknesses.join(', ') : c.weaknesses || ''}`
        });
      });
    }
    if (Array.isArray(json.gaps) && json.gaps.length > 0) {
      result.push({ id: 'g-title', type: 'h2', content: 'Unserved Market Gaps' });
      json.gaps.forEach((g: any, idx: number) => {
        result.push({ id: `g-${idx}`, type: 'bullet_list', content: g });
      });
    }
    if (json.differentiation) {
      result.push({ id: 'd-title', type: 'h2', content: 'Value Proposition & Differentiation Strategy' });
      result.push({ id: 'd-desc', type: 'paragraph', content: json.differentiation });
    }
  } else if (type === 'feasibility') {
    if (json.technical_feasibility_summary) {
      result.push({ id: 'fe-title', type: 'h1', content: 'Technical Feasibility Executive Summary' });
      result.push({ id: 'fe-desc', type: 'paragraph', content: json.technical_feasibility_summary });
    }
    if (Array.isArray(json.risks) && json.risks.length > 0) {
      result.push({ id: 'r-title', type: 'h2', content: 'Implementation Risks & Mitigation Plans' });
      json.risks.forEach((r: any, idx: number) => {
        result.push({
          id: `r-${idx}`,
          type: 'paragraph',
          content: `Risk: ${r.risk || ''} [Impact: ${r.impact || 'Medium'}] - Mitigation Action: ${r.mitigation || ''}`
        });
      });
    }
    if (Array.isArray(json.resource_requirements) && json.resource_requirements.length > 0) {
      result.push({ id: 'res-title', type: 'h2', content: 'Staffing & Technical Resource Profiles' });
      json.resource_requirements.forEach((res: any, idx: number) => {
        result.push({ id: `res-${idx}`, type: 'bullet_list', content: res });
      });
    }
  } else if (type === 'roadmap') {
    if (Array.isArray(json.phases) && json.phases.length > 0) {
      result.push({ id: 'ph-title', type: 'h1', content: 'Milestone Development Roadmap' });
      json.phases.forEach((p: any, idx: number) => {
        result.push({
          id: `ph-${idx}`,
          type: 'paragraph',
          content: `${p.phase_name || ''} (${p.duration || ''}) - Key Deliverables: ${Array.isArray(p.deliverables) ? p.deliverables.join(', ') : p.deliverables || ''}`
        });
      });
    }
    if (Array.isArray(json.mvp_scope) && json.mvp_scope.length > 0) {
      result.push({ id: 'mvp-title', type: 'h2', content: 'Core MVP Scope Details' });
      json.mvp_scope.forEach((m: any, idx: number) => {
        result.push({ id: `mvp-${idx}`, type: 'bullet_list', content: m });
      });
    }
    if (Array.isArray(json.v2_scope) && json.v2_scope.length > 0) {
      result.push({ id: 'v2-title', type: 'h2', content: 'Deferred scale V2 scope' });
      json.v2_scope.forEach((v: any, idx: number) => {
        result.push({ id: `v2-${idx}`, type: 'bullet_list', content: v });
      });
    }
  }

  // Default block schema fallback
  if (result.length === 0) {
    result.push({ id: '1', type: 'h1', content: 'Blank Outline' });
    result.push({ id: '2', type: 'paragraph', content: 'No analysis results generated yet. Execute graph run first.' });
  }

  return result;
};

export default function DocumentBlockEditor() {
  const { id, pageType } = useParams();
  const router = useRouter();
  const [title, setTitle] = useState('');
  const [blocks, setBlocks] = useState<Block[]>([]);
  const [loading, setLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id || !pageType) return;

    async function loadPage() {
      try {
        setLoading(true);
        setError(null);
        
        // Fetch page details from API
        const data = await fetchWithAuth(`/api/projects/${id}/pages/${pageType}`);
        setTitle(data.title || 'Workspace Document');
        
        const parsedBlocks = convertJsonToBlocks(data.content_json, pageType as string);
        setBlocks(parsedBlocks);
      } catch (err: any) {
        console.error('Failed to load page contents:', err);
        setError(err.message || 'Failed to load page records.');
      } finally {
        setLoading(false);
      }
    }
    
    loadPage();
  }, [id, pageType]);

  const handleUpdateBlockContent = (blockId: string, text: string) => {
    setBlocks(blocks.map(b => b.id === blockId ? { ...b, content: text } : b));
  };

  const handleAddBlock = (type: 'h2' | 'paragraph' | 'bullet_list') => {
    const newBlock: Block = {
      id: Math.random().toString(36).substring(7),
      type,
      content: ''
    };
    setBlocks([...blocks, newBlock]);
  };

  const handleDeleteBlock = (blockId: string) => {
    setBlocks(blocks.filter(b => b.id !== blockId));
  };

  const handleSavePage = async () => {
    setIsSaving(true);
    try {
      await fetchWithAuth(`/api/projects/${id}/pages/${pageType}`, {
        method: 'PUT',
        body: JSON.stringify({
          title,
          content_json: { blocks }
        })
      });
      alert('Document saved successfully!');
    } catch (err: any) {
      console.error('Failed to save document:', err);
      alert(`Save failed: ${err.message || 'Failed to write updates.'}`);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans">
      {/* Header bar */}
      <header className="relative z-10 border-b border-slate-900/80 bg-slate-950/80 backdrop-blur-md px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href={`/project/${id}`} className="text-slate-400 hover:text-slate-200 transition-colors">
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <h1 className="font-bold text-base text-slate-100">{title}</h1>
            <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">{pageType} editor</span>
          </div>
        </div>

        <button
          onClick={handleSavePage}
          disabled={isSaving}
          className="bg-violet-600 hover:bg-violet-500 text-white rounded-lg px-4 py-2 text-xs font-semibold flex items-center gap-1.5 cursor-pointer disabled:opacity-50 transition-colors"
        >
          {isSaving ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <Save className="h-3.5 w-3.5" />
          )}
          Save Changes
        </button>
      </header>

      {/* Editor Content Area */}
      <main className="max-w-4xl mx-auto px-6 py-10">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="h-8 w-8 text-violet-500 animate-spin" />
          </div>
        ) : (
          <div className="space-y-6 bg-slate-900/10 border border-slate-900/60 rounded-xl p-8 backdrop-blur-sm min-h-[500px]">
            <div className="flex items-center gap-2 text-xs text-violet-400 bg-violet-950/20 border border-violet-900/20 rounded-lg px-3 py-2 mb-6">
              <Sparkles className="h-4 w-4" />
              <span>Generated autonomously by our Product Agent. Click on any text block to edit.</span>
            </div>

            {/* Render Editable Blocks */}
            <div className="space-y-4">
              {blocks.map((block) => (
                <div key={block.id} className="group relative flex items-start gap-2">
                  <div className="flex-1">
                    {block.type === 'h1' && (
                      <input
                        type="text"
                        value={block.content}
                        onChange={(e) => handleUpdateBlockContent(block.id, e.target.value)}
                        className="w-full bg-transparent border-b border-transparent focus:border-violet-500 text-2xl font-bold text-slate-100 focus:outline-none py-1"
                      />
                    )}
                    {block.type === 'h2' && (
                      <input
                        type="text"
                        value={block.content}
                        onChange={(e) => handleUpdateBlockContent(block.id, e.target.value)}
                        className="w-full bg-transparent border-b border-transparent focus:border-violet-500 text-lg font-bold text-slate-200 focus:outline-none py-1"
                      />
                    )}
                    {block.type === 'paragraph' && (
                      <textarea
                        value={block.content}
                        onChange={(e) => handleUpdateBlockContent(block.id, e.target.value)}
                        rows={2}
                        className="w-full bg-transparent border-b border-transparent focus:border-violet-500 text-sm text-slate-350 leading-relaxed focus:outline-none py-1 resize-none"
                      />
                    )}
                    {block.type === 'bullet_list' && (
                      <div className="flex items-center gap-2">
                        <span className="text-violet-500 select-none">•</span>
                        <input
                          type="text"
                          value={block.content}
                          onChange={(e) => handleUpdateBlockContent(block.id, e.target.value)}
                          className="w-full bg-transparent border-b border-transparent focus:border-violet-500 text-sm text-slate-300 focus:outline-none py-1"
                        />
                      </div>
                    )}
                  </div>
                  
                  {/* Delete Block option on hover */}
                  <button
                    onClick={() => handleDeleteBlock(block.id)}
                    className="opacity-0 group-hover:opacity-100 text-slate-600 hover:text-rose-400 p-1 transition-opacity cursor-pointer"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              ))}
            </div>

            {/* Quick Add Toolbar */}
            <div className="flex items-center gap-2 border-t border-slate-900/60 pt-6 mt-8">
              <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider mr-2">Add block:</span>
              <button
                onClick={() => handleAddBlock('h2')}
                className="bg-slate-900 hover:bg-slate-850 border border-slate-850 rounded px-2.5 py-1 text-xs text-slate-300 cursor-pointer transition-colors"
              >
                + Heading
              </button>
              <button
                onClick={() => handleAddBlock('paragraph')}
                className="bg-slate-900 hover:bg-slate-850 border border-slate-850 rounded px-2.5 py-1 text-xs text-slate-300 cursor-pointer transition-colors"
              >
                + Paragraph
              </button>
              <button
                onClick={() => handleAddBlock('bullet_list')}
                className="bg-slate-900 hover:bg-slate-850 border border-slate-850 rounded px-2.5 py-1 text-xs text-slate-300 cursor-pointer transition-colors"
              >
                + Bullet Point
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

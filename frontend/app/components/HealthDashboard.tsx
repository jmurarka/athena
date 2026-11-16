'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { getProjectGraph, editTechDecision } from '../../lib/api';
import { AlertTriangle, ShieldAlert, RefreshCw, Cpu } from 'lucide-react';

interface HealthDashboardProps {
  projectId: string;
}

interface HealthMetrics {
  coverage_score?: number;
  contradiction_rate?: number;
  unsupported_claim_rate?: number;
  critical_count?: number;
  warning_count?: number;
  review_count?: number;
  total_requirements?: number;
  mapped_requirements?: number;
}

interface ValidationIssue {
  id: string;
  severity: string;
  code: string;
  title: string;
  description: string;
  suggested_fix?: string;
  affected_entities?: string[];
}

interface TechDecision {
  id: string;
  topic: string;
  chosen_option: string;
  why_chosen: string;
  why_not_alternatives?: string;
  trade_offs?: string;
}

interface GraphData {
  project_id: string;
  health_metrics?: HealthMetrics;
  validation_issues?: ValidationIssue[];
  decisions?: TechDecision[];
  requirements?: Array<{ id: string; code: string; title: string; category: string; priority: string }>;
  features?: Array<{ id: string; code: string; title: string; is_mvp: boolean }>;
}

export default function HealthDashboard({ projectId }: HealthDashboardProps) {
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editingDecisionId, setEditingDecisionId] = useState<string | null>(null);
  const [newOption, setNewOption] = useState('');
  const [updating, setUpdating] = useState(false);

  const loadGraph = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getProjectGraph(projectId);
      setGraphData(data);
      setError(null);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load project graph';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    let isMounted = true;
    const fetchInitial = async () => {
      try {
        setLoading(true);
        const data = await getProjectGraph(projectId);
        if (isMounted) {
          setGraphData(data);
          setError(null);
        }
      } catch (err: unknown) {
        if (isMounted) {
          const msg = err instanceof Error ? err.message : 'Failed to load project graph';
          setError(msg);
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchInitial();

    return () => {
      isMounted = false;
    };
  }, [projectId]);

  const handleEditDecision = async (decisionId: string) => {
    if (!newOption.trim()) return;
    try {
      setUpdating(true);
      await editTechDecision(projectId, decisionId, newOption);
      setEditingDecisionId(null);
      setNewOption('');
      await loadGraph(); // Reload updated graph and revalidation metrics
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Revalidation failed';
      alert(`Revalidation failed: ${msg}`);
    } finally {
      setUpdating(false);
    }
  };

  if (loading) {
    return (
      <div className="p-8 bg-slate-900/60 rounded-2xl border border-slate-800 text-slate-300 flex flex-col items-center justify-center gap-3">
        <RefreshCw className="w-6 h-6 animate-spin text-indigo-400" />
        <p className="text-sm font-medium text-slate-400">Auditing Living Blueprint & Health Graph...</p>
      </div>
    );
  }

  if (error || !graphData) {
    return (
      <div className="p-6 bg-slate-900/60 text-rose-400 rounded-2xl border border-rose-900/40 space-y-3">
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-5 h-5 text-rose-500" />
          <h4 className="font-semibold text-rose-300">Validation Audit Graph Pending</h4>
        </div>
        <p className="text-xs text-slate-400">
          The validation engine runs automatically upon completion of the agent pipeline.
          {error && ` (${error})`}
        </p>
        <button
          onClick={loadGraph}
          className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-medium transition"
        >
          Retry Audit
        </button>
      </div>
    );
  }

  const metrics = graphData.health_metrics || {};
  const coveragePercent = Math.round((metrics.coverage_score || 0) * 100);

  return (
    <div className="space-y-6 text-slate-100 font-sans">
      {/* Top Header Card */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950/70 to-slate-900 p-6 rounded-2xl border border-indigo-500/30 shadow-xl">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              <span className="text-indigo-400">🛡️ Living Blueprint</span>
              <span className="text-slate-400 font-normal">| Validation Audit</span>
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Automated "Break My Plan" validation engine detecting architecture contradictions and coverage gaps
            </p>
          </div>

          <button
            onClick={loadGraph}
            className="px-3.5 py-1.5 text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg transition-all shadow-md flex items-center gap-1.5"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Re-audit Blueprint</span>
          </button>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-5">
          <div className="bg-slate-950/80 p-3.5 rounded-xl border border-slate-800/80">
            <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider block">Requirement Coverage</span>
            <div className="flex items-baseline gap-2 mt-1.5">
              <span className="text-2xl font-black text-emerald-400">{coveragePercent}%</span>
              <span className="text-[11px] text-slate-400">
                ({metrics.mapped_requirements || 0}/{metrics.total_requirements || 0})
              </span>
            </div>
          </div>

          <div className="bg-slate-950/80 p-3.5 rounded-xl border border-slate-800/80">
            <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider block">Critical Blockers</span>
            <div className="text-2xl font-black text-rose-500 mt-1.5">
              {metrics.critical_count || 0}
            </div>
          </div>

          <div className="bg-slate-950/80 p-3.5 rounded-xl border border-slate-800/80">
            <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider block">Warnings</span>
            <div className="text-2xl font-black text-amber-400 mt-1.5">
              {metrics.warning_count || 0}
            </div>
          </div>

          <div className="bg-slate-950/80 p-3.5 rounded-xl border border-slate-800/80">
            <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider block">Review Suggestions</span>
            <div className="text-2xl font-black text-blue-400 mt-1.5">
              {metrics.review_count || 0}
            </div>
          </div>
        </div>
      </div>

      {/* "Break My Plan" Validation Issues */}
      {graphData.validation_issues && graphData.validation_issues.length > 0 && (
        <div className="bg-slate-900/80 p-5 rounded-2xl border border-rose-900/30 shadow-lg">
          <h3 className="text-sm font-bold text-rose-400 flex items-center gap-2 mb-3">
            <AlertTriangle className="w-4 h-4 text-rose-400" />
            <span>"Break My Plan" Validation Alerts ({graphData.validation_issues.length})</span>
          </h3>
          <div className="space-y-3">
            {graphData.validation_issues.map((issue) => {
              const isCritical = issue.severity.toLowerCase() === 'critical';
              const isWarning = issue.severity.toLowerCase() === 'warning';
              const borderColor = isCritical ? 'border-rose-500/40 bg-rose-950/20' : isWarning ? 'border-amber-500/40 bg-amber-950/20' : 'border-blue-500/40 bg-blue-950/20';
              const badgeBg = isCritical ? 'bg-rose-500/20 text-rose-300' : isWarning ? 'bg-amber-500/20 text-amber-300' : 'bg-blue-500/20 text-blue-300';

              return (
                <div key={issue.id} className={`p-3.5 rounded-xl border ${borderColor} transition-all`}>
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-semibold text-xs text-slate-200">{issue.title}</span>
                    <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase ${badgeBg}`}>
                      {issue.severity}
                    </span>
                  </div>
                  <p className="text-xs text-slate-300 mt-1.5 leading-relaxed">{issue.description}</p>
                  {issue.suggested_fix && (
                    <div className="mt-2.5 p-2.5 bg-slate-950/80 rounded-lg border border-slate-800 text-xs text-emerald-300">
                      <span className="font-semibold text-emerald-400">💡 Suggested Fix: </span>
                      {issue.suggested_fix}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Technology Decision Explain & Challenge */}
      <div className="bg-slate-900/80 p-5 rounded-2xl border border-slate-800 shadow-lg">
        <h3 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
          <Cpu className="w-4 h-4 text-indigo-400" />
          <span>Technology Decisions ("Explain & Challenge")</span>
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
          {graphData.decisions && graphData.decisions.length > 0 ? (
            graphData.decisions.map((dec) => (
              <div key={dec.id} className="p-4 bg-slate-950/80 rounded-xl border border-slate-800/90 space-y-2.5">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-semibold text-indigo-400 uppercase tracking-wider">{dec.topic}</span>
                  <span className="px-2 py-0.5 text-xs font-bold bg-indigo-950 text-indigo-300 rounded border border-indigo-800/80">
                    {dec.chosen_option}
                  </span>
                </div>

                <div>
                  <span className="text-[10px] text-slate-400 font-semibold block">WHY CHOSEN:</span>
                  <p className="text-xs text-slate-300 mt-0.5 leading-relaxed">{dec.why_chosen}</p>
                </div>

                {dec.why_not_alternatives && (
                  <div>
                    <span className="text-[10px] text-slate-400 font-semibold block">WHY NOT ALTERNATIVES:</span>
                    <p className="text-xs text-slate-400 mt-0.5 leading-relaxed">{dec.why_not_alternatives}</p>
                  </div>
                )}

                {dec.trade_offs && (
                  <div>
                    <span className="text-[10px] text-amber-400/90 font-semibold block">TRADE-OFFS & RISKS:</span>
                    <p className="text-xs text-slate-400 mt-0.5 leading-relaxed">{dec.trade_offs}</p>
                  </div>
                )}

                <div className="pt-2 border-t border-slate-800/70">
                  {editingDecisionId === dec.id ? (
                    <div className="space-y-2">
                      <input
                        type="text"
                        placeholder="Enter new tech stack choice..."
                        value={newOption}
                        onChange={(e) => setNewOption(e.target.value)}
                        className="w-full text-xs px-2.5 py-1.5 bg-slate-900 border border-indigo-500 rounded text-slate-200 focus:outline-none"
                      />
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleEditDecision(dec.id)}
                          disabled={updating}
                          className="px-2.5 py-1 bg-emerald-600 text-xs font-semibold text-white rounded hover:bg-emerald-500 disabled:opacity-50"
                        >
                          {updating ? 'Revalidating...' : 'Apply & Revalidate'}
                        </button>
                        <button
                          onClick={() => setEditingDecisionId(null)}
                          className="px-2.5 py-1 bg-slate-800 text-xs text-slate-400 rounded hover:bg-slate-700"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    <button
                      onClick={() => {
                        setEditingDecisionId(dec.id);
                        setNewOption(dec.chosen_option);
                      }}
                      className="text-xs text-indigo-400 hover:text-indigo-300 font-medium underline flex items-center gap-1"
                    >
                      ✏️ Edit Decision (Triggers Living Blueprint Revalidation)
                    </button>
                  )}
                </div>
              </div>
            ))
          ) : (
            <p className="text-xs text-slate-400 col-span-2">No explicit architecture decisions logged yet.</p>
          )}
        </div>
      </div>
    </div>
  );
}

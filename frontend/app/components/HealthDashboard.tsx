'use client';

import React, { useState, useEffect } from 'react';
import { getProjectGraph, editTechDecision } from '../../lib/api';

interface HealthDashboardProps {
  projectId: string;
}

export default function HealthDashboard({ projectId }: HealthDashboardProps) {
  const [graphData, setGraphData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editingDecisionId, setEditingDecisionId] = useState<string | null>(null);
  const [newOption, setNewOption] = useState('');
  const [updating, setUpdating] = useState(false);

  const loadGraph = async () => {
    try {
      setLoading(true);
      const data = await getProjectGraph(projectId);
      setGraphData(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load project graph');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadGraph();
  }, [projectId]);

  const handleEditDecision = async (decisionId: string) => {
    if (!newOption.trim()) return;
    try {
      setUpdating(true);
      await editTechDecision(projectId, decisionId, newOption);
      setEditingDecisionId(null);
      setNewOption('');
      await loadGraph(); // Reload updated graph and revalidation metrics
    } catch (err: any) {
      alert(`Revalidation failed: ${err.message}`);
    } finally {
      setUpdating(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6 bg-slate-900 text-slate-200 rounded-xl border border-slate-800 animate-pulse">
        <p className="text-slate-400">Loading ATHENA Project Health & Validation Graph...</p>
      </div>
    );
  }

  if (error || !graphData) {
    return (
      <div className="p-6 bg-slate-900 text-rose-400 rounded-xl border border-rose-900/50">
        <p>Error loading health metrics: {error}</p>
      </div>
    );
  }

  const metrics = graphData.health_metrics || {};
  const coveragePercent = Math.round((metrics.coverage_score || 0) * 100);

  return (
    <div className="space-y-6 text-slate-100 font-sans">
      {/* Top Header Card */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 p-6 rounded-2xl border border-indigo-500/30 shadow-xl">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              <span className="text-indigo-400">⚡ ATHENA</span> Project Health & Blueprint
            </h2>
            <p className="text-sm text-slate-400 mt-1">
              Structured Requirement & Decision Graph with Automated "Break My Plan" Validation Engine
            </p>
          </div>

          <button
            onClick={loadGraph}
            className="px-4 py-2 text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg transition-all shadow-md"
          >
            🔄 Refresh Graph & Revalidate
          </button>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
          <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Requirement Coverage</span>
            <div className="flex items-baseline gap-2 mt-2">
              <span className="text-3xl font-extrabold text-emerald-400">{coveragePercent}%</span>
              <span className="text-xs text-slate-400">
                ({metrics.mapped_requirements || 0}/{metrics.total_requirements || 0})
              </span>
            </div>
          </div>

          <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Critical Blockers</span>
            <div className="text-3xl font-extrabold text-rose-500 mt-2">
              {metrics.critical_count || 0}
            </div>
          </div>

          <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Warnings</span>
            <div className="text-3xl font-extrabold text-amber-400 mt-2">
              {metrics.warning_count || 0}
            </div>
          </div>

          <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Review Suggestions</span>
            <div className="text-3xl font-extrabold text-blue-400 mt-2">
              {metrics.review_count || 0}
            </div>
          </div>
        </div>
      </div>

      {/* "Break My Plan" Validation Issues */}
      {graphData.validation_issues && graphData.validation_issues.length > 0 && (
        <div className="bg-slate-900/90 p-6 rounded-2xl border border-rose-900/40 shadow-lg">
          <h3 className="text-lg font-bold text-rose-400 flex items-center gap-2 mb-4">
            🔴 "Break My Plan" Validation Alerts
          </h3>
          <div className="space-y-4">
            {graphData.validation_issues.map((issue: any) => {
              const isCritical = issue.severity === 'critical';
              const isWarning = issue.severity === 'warning';
              const borderColor = isCritical ? 'border-rose-500/40 bg-rose-950/20' : isWarning ? 'border-amber-500/40 bg-amber-950/20' : 'border-blue-500/40 bg-blue-950/20';
              const badgeBg = isCritical ? 'bg-rose-500/20 text-rose-300' : isWarning ? 'bg-amber-500/20 text-amber-300' : 'bg-blue-500/20 text-blue-300';

              return (
                <div key={issue.id} className={`p-4 rounded-xl border ${borderColor} transition-all`}>
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-semibold text-slate-200">{issue.title}</span>
                    <span className={`text-xs px-2.5 py-0.5 rounded-full font-semibold uppercase ${badgeBg}`}>
                      {issue.severity}
                    </span>
                  </div>
                  <p className="text-sm text-slate-300 mt-2">{issue.description}</p>
                  {issue.suggested_fix && (
                    <div className="mt-3 p-3 bg-slate-950/70 rounded-lg border border-slate-800 text-xs text-emerald-300">
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
      <div className="bg-slate-900/90 p-6 rounded-2xl border border-slate-800 shadow-lg">
        <h3 className="text-lg font-bold text-white mb-4">
          🧠 Technology Decisions ("Explain & Challenge")
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {graphData.decisions && graphData.decisions.map((dec: any) => (
            <div key={dec.id} className="p-4 bg-slate-950/80 rounded-xl border border-slate-800 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-indigo-400 uppercase tracking-wider">{dec.topic}</span>
                <span className="px-2.5 py-1 text-xs font-bold bg-indigo-950 text-indigo-300 rounded-md border border-indigo-800">
                  {dec.chosen_option}
                </span>
              </div>

              <div>
                <span className="text-xs text-slate-400 font-semibold block">WHY CHOSEN:</span>
                <p className="text-xs text-slate-300 mt-0.5">{dec.why_chosen}</p>
              </div>

              {dec.why_not_alternatives && (
                <div>
                  <span className="text-xs text-slate-400 font-semibold block">WHY NOT ALTERNATIVES:</span>
                  <p className="text-xs text-slate-400 mt-0.5">{dec.why_not_alternatives}</p>
                </div>
              )}

              {dec.trade_offs && (
                <div>
                  <span className="text-xs text-amber-400/90 font-semibold block">TRADE-OFFS & RISKS:</span>
                  <p className="text-xs text-slate-400 mt-0.5">{dec.trade_offs}</p>
                </div>
              )}

              {/* Editable Living Blueprint Action */}
              <div className="pt-2 border-t border-slate-800/60">
                {editingDecisionId === dec.id ? (
                  <div className="space-y-2">
                    <input
                      type="text"
                      placeholder={`Enter new option (e.g. PostgreSQL)`}
                      value={newOption}
                      onChange={(e) => setNewOption(e.target.value)}
                      className="w-full text-xs px-3 py-1.5 bg-slate-900 border border-indigo-500 rounded text-slate-200 focus:outline-none"
                    />
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleEditDecision(dec.id)}
                        disabled={updating}
                        className="px-3 py-1 bg-emerald-600 text-xs font-semibold text-white rounded hover:bg-emerald-500 disabled:opacity-50"
                      >
                        {updating ? 'Revalidating...' : 'Apply & Revalidate'}
                      </button>
                      <button
                        onClick={() => setEditingDecisionId(null)}
                        className="px-3 py-1 bg-slate-800 text-xs text-slate-400 rounded hover:bg-slate-700"
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
          ))}
        </div>
      </div>
    </div>
  );
}

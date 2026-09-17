import Link from 'next/link';
import { ArrowRight, Sparkles, Shield, Zap, RefreshCw, Cpu, CheckCircle2, Search } from 'lucide-react';

export default function Home() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between font-sans relative overflow-hidden">
      {/* Background gradients */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none z-0">
        <div className="absolute top-[-20%] left-[-20%] w-[60%] h-[60%] bg-indigo-900/15 rounded-full blur-[140px]" />
        <div className="absolute bottom-[-20%] right-[-20%] w-[60%] h-[60%] bg-violet-900/15 rounded-full blur-[140px]" />
      </div>

      {/* Navigation Header */}
      <header className="relative z-10 max-w-7xl w-full mx-auto px-6 py-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-violet-600 to-emerald-500 flex items-center justify-center shadow-lg shadow-indigo-500/25">
            <span className="font-black text-base text-white">A</span>
          </div>
          <div>
            <span className="font-extrabold text-xl tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-slate-100 via-indigo-200 to-slate-300">
              ATHENA
            </span>
            <span className="block text-[10px] font-semibold text-indigo-400 tracking-wider uppercase">Local-First Agentic AI Platform</span>
          </div>
        </div>
        <div>
          <Link
            href="/dashboard"
            className="border border-indigo-500/30 hover:border-indigo-500 bg-indigo-950/40 backdrop-blur text-xs font-bold text-indigo-200 px-5 py-2.5 rounded-xl transition-all shadow-md hover:shadow-indigo-500/20"
          >
            Launch ATHENA Workspace &rarr;
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <main className="relative z-10 max-w-5xl mx-auto text-center px-6 py-16 my-auto flex flex-col items-center">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-indigo-950/60 border border-indigo-500/40 text-indigo-300 text-xs font-bold mb-8 shadow-lg shadow-indigo-950/50">
          <Sparkles className="h-4 w-4 text-indigo-400" />
          <span>Requirement Graph • "Break My Plan" Validation • Local AI Inference</span>
        </div>
        
        <h1 className="text-4xl md:text-6xl font-black tracking-tight text-white mb-6 leading-[1.15]">
          Transform Raw Ideas into Structured,{' '}
          <span className="bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 via-violet-400 to-emerald-400">
            Validated System Blueprints
          </span>
        </h1>
        
        <p className="text-slate-300 text-base md:text-lg max-w-3xl mb-10 leading-relaxed">
          ATHENA is an open-source, local-first agentic AI platform that converts natural language problem statements into a traceable 
          <strong className="text-white"> Requirement & Decision Graph</strong>, self-validates plans for missing requirements or architectural contradictions, 
          and continuously updates affected components as your design evolves.
        </p>

        <div className="flex flex-col sm:flex-row items-center gap-4 mb-16">
          <Link
            href="/dashboard"
            className="bg-gradient-to-r from-indigo-600 via-violet-600 to-indigo-700 hover:from-indigo-500 hover:to-violet-500 text-white font-extrabold rounded-xl px-9 py-4 text-sm flex items-center gap-3 shadow-xl shadow-indigo-500/25 transition-all transform hover:-translate-y-0.5"
          >
            Open Project Engineering Canvas
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>

        {/* Core Architectural Pillars */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 w-full text-left">
          <div className="border border-slate-800 bg-slate-900/40 rounded-2xl p-5 backdrop-blur-md">
            <Cpu className="h-6 w-6 text-indigo-400 mb-3" />
            <h3 className="font-bold text-slate-100 text-sm mb-1">Local-First AI</h3>
            <p className="text-slate-400 text-xs leading-relaxed">
              Model-independent support for Ollama, llama.cpp, and vLLM for zero cloud egress cost and offline privacy.
            </p>
          </div>

          <div className="border border-slate-800 bg-slate-900/40 rounded-2xl p-5 backdrop-blur-md">
            <Zap className="h-6 w-6 text-emerald-400 mb-3" />
            <h3 className="font-bold text-slate-100 text-sm mb-1">Requirement Graph</h3>
            <p className="text-slate-400 text-xs leading-relaxed">
              Connects REQ-xxx codes to Features, Architecture Components, and Test Boundaries for full engineering traceability.
            </p>
          </div>

          <div className="border border-slate-800 bg-slate-900/40 rounded-2xl p-5 backdrop-blur-md">
            <CheckCircle2 className="h-6 w-6 text-rose-400 mb-3" />
            <h3 className="font-bold text-slate-100 text-sm mb-1 font-mono">"Break My Plan"</h3>
            <p className="text-slate-400 text-xs leading-relaxed">
              Automated validation engine that scans for missing authentication, scale mismatches, and unsupported claims.
            </p>
          </div>

          <div className="border border-slate-800 bg-slate-900/40 rounded-2xl p-5 backdrop-blur-md">
            <RefreshCw className="h-6 w-6 text-violet-400 mb-3" />
            <h3 className="font-bold text-slate-100 text-sm mb-1">Living Blueprint</h3>
            <p className="text-slate-400 text-xs leading-relaxed">
              Edits to requirements or database decisions automatically propagate to dependent components and trigger revalidation.
            </p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="relative z-10 max-w-7xl w-full mx-auto px-6 py-6 border-t border-slate-900/80 flex flex-wrap items-center justify-between text-xs text-slate-500">
        <span>&copy; {new Date().getFullYear()} ATHENA Platform • Soumashree Das, Iti Karmakar, Jhanvi Murarka</span>
        <span>Built with Next.js, FastAPI, LangGraph & PostgreSQL</span>
      </footer>
    </div>
  );
}

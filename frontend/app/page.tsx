import Link from 'next/link';
import { ArrowRight, Sparkles, Shield, Zap, RefreshCw } from 'lucide-react';

export default function Home() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between font-sans relative overflow-hidden">
      {/* Background gradients */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none z-0">
        <div className="absolute top-[-20%] left-[-20%] w-[60%] h-[60%] bg-violet-900/10 rounded-full blur-[140px]" />
        <div className="absolute bottom-[-20%] right-[-20%] w-[60%] h-[60%] bg-blue-900/10 rounded-full blur-[140px]" />
      </div>

      {/* Navigation Header */}
      <header className="relative z-10 max-w-7xl w-full mx-auto px-6 py-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-violet-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-violet-500/25">
            <span className="font-extrabold text-sm text-white">AP</span>
          </div>
          <span className="font-bold text-xl tracking-wide bg-clip-text text-transparent bg-gradient-to-r from-slate-50 to-slate-200">
            Agentic Planner
          </span>
        </div>
        <div>
          <Link
            href="/dashboard"
            className="border border-slate-800 hover:border-slate-700 bg-slate-900/20 backdrop-blur text-xs font-semibold px-4 py-2 rounded-lg transition-all"
          >
            Sign In
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <main className="relative z-10 max-w-4xl mx-auto text-center px-6 py-20 my-auto flex flex-col items-center">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-violet-950/30 border border-violet-900/40 text-violet-400 text-xs font-semibold mb-8 select-none shadow-inner shadow-violet-950/50">
          <Sparkles className="h-3.5 w-3.5" />
          <span>Autonomous Multi-Agent Orchestrator</span>
        </div>
        
        <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight text-white mb-6 leading-[1.1]">
          Automated Product Planning &{' '}
          <span className="bg-clip-text text-transparent bg-gradient-to-r from-violet-400 via-indigo-400 to-blue-400">
            System Design
          </span>
        </h1>
        
        <p className="text-slate-400 text-base md:text-lg max-w-2xl mb-10 leading-relaxed">
          Provide a single product concept. Our pipeline orchestrates 5 specialized AI agents in parallel, outputting structured Notion-style documentation and interactive architecture canvases.
        </p>

        <div className="flex flex-col sm:flex-row items-center gap-4">
          <Link
            href="/dashboard"
            className="bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white font-bold rounded-lg px-8 py-3.5 text-sm flex items-center gap-2 shadow-lg shadow-violet-500/20 transition-all transform hover:-translate-y-0.5"
          >
            Launch Dashboard
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>

        {/* Feature Highlights Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 w-full max-w-5xl mt-24">
          <div className="border border-slate-900 bg-slate-900/10 rounded-xl p-5 text-left backdrop-blur-sm">
            <Zap className="h-5 w-5 text-violet-500 mb-3" />
            <h3 className="font-semibold text-slate-200 text-sm mb-1">Parallel Pipeline</h3>
            <p className="text-slate-400 text-xs leading-relaxed">
              Product and market insights execute in parallel under 90 seconds.
            </p>
          </div>
          <div className="border border-slate-900 bg-slate-900/10 rounded-xl p-5 text-left backdrop-blur-sm">
            <RefreshCw className="h-5 w-5 text-indigo-500 mb-3" />
            <h3 className="font-semibold text-slate-200 text-sm mb-1">Interactive Canvas</h3>
            <p className="text-slate-400 text-xs leading-relaxed">
              Edit nodes and connectors dynamically using our integrated React Flow interface.
            </p>
          </div>
          <div className="border border-slate-900 bg-slate-900/10 rounded-xl p-5 text-left backdrop-blur-sm">
            <Shield className="h-5 w-5 text-blue-500 mb-3" />
            <h3 className="font-semibold text-slate-200 text-sm mb-1">Row Level Isolation</h3>
            <p className="text-slate-400 text-xs leading-relaxed">
              Strict workspace isolation protects multi-tenant proprietary data structures.
            </p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="relative z-10 max-w-7xl w-full mx-auto px-6 py-8 border-t border-slate-900/50 flex items-center justify-between text-xs text-slate-500">
        <span>&copy; {new Date().getFullYear()} Agentic Planner Platform. All rights reserved.</span>
        <span>Built with Next.js, FastAPI & LangGraph</span>
      </footer>
    </div>
  );
}

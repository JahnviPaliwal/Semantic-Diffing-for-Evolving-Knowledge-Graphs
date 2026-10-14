import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { GitCompare, Layers, Activity, Key, Eye, EyeOff, ShieldAlert, Check, Trash2, X, Sparkles } from 'lucide-react';
import { useApiKey } from '../context/ApiKeyContext';

export const Navbar: React.FC = () => {
  const location = useLocation();
  const { apiKey, hasApiKey, setApiKey, clearApiKey } = useApiKey();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const [showKey, setShowKey] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const isProjectsActive = location.pathname === '/' || location.pathname.startsWith('/projects');
  const isEvalActive = location.pathname.startsWith('/evaluation');

  const handleOpenModal = () => {
    setInputValue(apiKey);
    setShowKey(false);
    setStatusMessage(null);
    setIsModalOpen(true);
  };

  const handleSaveKey = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim()) {
      clearApiKey();
      setStatusMessage('Key cleared.');
    } else {
      setApiKey(inputValue.trim());
      setStatusMessage('Groq API Key active in session memory.');
    }
    setTimeout(() => {
      setIsModalOpen(false);
    }, 700);
  };

  const handleClearKey = () => {
    clearApiKey();
    setInputValue('');
    setStatusMessage('Key removed from session memory.');
  };

  const getMaskedKey = (key: string) => {
    if (!key) return '';
    if (key.length <= 8) return '••••••••';
    return `${key.slice(0, 4)}••••${key.slice(-4)}`;
  };

  return (
    <>
      <nav className="bg-slate-900 border-b border-slate-800 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            {/* Logo & Brand */}
            <div className="flex items-center space-x-3">
              <Link to="/" className="flex items-center space-x-2 text-emerald-400 hover:text-emerald-300 font-bold text-lg tracking-tight">
                <div className="p-2 bg-emerald-500/10 rounded-lg border border-emerald-500/20">
                  <GitCompare className="w-5 h-5 text-emerald-400" />
                </div>
                <span>Semantic KG Diff</span>
              </Link>
              <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 border border-slate-700 text-slate-400 font-mono">
                v2.0
              </span>
            </div>

            {/* Navigation Links */}
            <div className="flex items-center space-x-1">
              <Link
                to="/"
                className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isProjectsActive
                    ? 'bg-slate-800 text-emerald-400'
                    : 'text-slate-300 hover:text-white hover:bg-slate-800/50'
                }`}
              >
                <Layers className="w-4 h-4" />
                <span>Projects</span>
              </Link>

              <Link
                to="/evaluation"
                className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isEvalActive
                    ? 'bg-slate-800 text-emerald-400'
                    : 'text-slate-300 hover:text-white hover:bg-slate-800/50'
                }`}
              >
                <Activity className="w-4 h-4" />
                <span>Evaluation & Benchmark</span>
              </Link>
            </div>

            {/* Ephemeral Groq API Key & Status */}
            <div className="flex items-center space-x-3">
              <button
                type="button"
                onClick={handleOpenModal}
                className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                  hasApiKey
                    ? 'bg-emerald-950/50 border-emerald-700/60 text-emerald-300 hover:bg-emerald-900/60'
                    : 'bg-slate-800/80 border-slate-700 text-slate-300 hover:bg-slate-800 hover:border-slate-600'
                }`}
                title="Manage ephemeral Groq API Key"
              >
                <Key className={`w-3.5 h-3.5 ${hasApiKey ? 'text-emerald-400' : 'text-slate-400'}`} />
                {hasApiKey ? (
                  <>
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                    <span>Groq Key: {getMaskedKey(apiKey)}</span>
                  </>
                ) : (
                  <span>Set Groq API Key</span>
                )}
              </button>

              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-800/60 text-slate-400 border border-slate-700/60">
                <span className="w-2 h-2 rounded-full bg-emerald-400" />
                Open Workspace
              </span>
            </div>
          </div>
        </div>
      </nav>

      {/* Ephemeral Key Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl relative text-slate-100">
            <button
              onClick={() => setIsModalOpen(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-3 mb-4">
              <div className="p-2.5 bg-emerald-500/10 border border-emerald-500/20 rounded-xl">
                <Key className="w-6 h-6 text-emerald-400" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white">Groq API Key (Session Only)</h3>
                <p className="text-xs text-slate-400">Zero persistence • Cleared immediately on page refresh</p>
              </div>
            </div>

            {/* Zero-persistence notice */}
            <div className="mb-4 p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-200/90 flex gap-2.5 items-start">
              <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
              <div>
                <strong className="text-amber-300 font-semibold">Ephemeral Storage Policy:</strong>
                <p className="mt-0.5 text-slate-300">
                  Your Groq API key is held solely in volatile browser memory and sent per-request via HTTP headers.
                  It is <strong>never stored in the database or localStorage</strong>, and is wiped completely as soon as you refresh or close this page.
                </p>
              </div>
            </div>

            {/* Active Document-Ready Model Notice */}
            <div className="mb-4 p-3 bg-slate-950/80 border border-slate-800 rounded-xl text-xs space-y-1.5">
              <div className="font-semibold text-slate-200 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
                <span>Active Groq Model (Exclusively Configured):</span>
              </div>
              <div className="pl-4">
                <p className="text-[11px] text-slate-300">
                  <code className="text-emerald-400 font-bold">qwen/qwen3.8-27b</code> • 128K context (131,072 tokens) • 16K completion • 100% free on GroqCloud
                </p>
                <p className="text-[10px] text-slate-400 pt-0.5">
                  Deep reasoning & multimodal architecture optimized for dense document extraction.
                </p>
              </div>
            </div>

            <form onSubmit={handleSaveKey} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5 uppercase tracking-wider">
                  Groq API Key
                </label>
                <div className="relative">
                  <input
                    type={showKey ? 'text' : 'password'}
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    placeholder="gsk_..."
                    autoFocus
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 pr-10 font-mono"
                  />
                  <button
                    type="button"
                    onClick={() => setShowKey(!showKey)}
                    className="absolute right-3 top-2.5 text-slate-400 hover:text-white"
                  >
                    {showKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                <p className="mt-1 text-[11px] text-slate-400">
                  Leave blank to use the offline heuristic extraction & deterministic summary fallback.
                </p>
              </div>

              {statusMessage && (
                <div className="text-xs p-2 rounded-lg bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 flex items-center gap-1.5">
                  <Check className="w-3.5 h-3.5" />
                  <span>{statusMessage}</span>
                </div>
              )}

              <div className="flex items-center justify-between pt-2">
                {hasApiKey ? (
                  <button
                    type="button"
                    onClick={handleClearKey}
                    className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-medium text-rose-400 hover:text-rose-300 hover:bg-rose-500/10 transition-colors"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                    <span>Clear / Delete Now</span>
                  </button>
                ) : <span />}

                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setIsModalOpen(false)}
                    className="px-3.5 py-2 rounded-xl text-xs font-medium text-slate-300 hover:text-white hover:bg-slate-800 transition-colors"
                  >
                    Close
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 rounded-xl text-xs font-semibold bg-emerald-500 text-slate-950 hover:bg-emerald-400 transition-colors shadow-lg shadow-emerald-500/20"
                  >
                    Save for Session
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
};

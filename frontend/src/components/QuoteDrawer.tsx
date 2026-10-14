import React from 'react';
import { X, FileText, ShieldAlert, CheckCircle2, BookOpen } from 'lucide-react';
import { DiffItem } from '../api/types';

interface QuoteDrawerProps {
  item: DiffItem | null;
  onClose: () => void;
}

export const QuoteDrawer: React.FC<QuoteDrawerProps> = ({ item, onClose }) => {
  if (!item) return null;

  const severityBadgeColor = {
    CRITICAL: 'bg-rose-500/20 text-rose-400 border-rose-500/30',
    HIGH: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    MEDIUM: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    LOW: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
  }[item.severity];

  const changeTypeBadgeColor = {
    ADDED: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
    REMOVED: 'bg-rose-500/20 text-rose-400 border-rose-500/30',
    RENAMED: 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30',
    MODIFIED: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    UNCHANGED: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
  }[item.change_type];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-2xl overflow-hidden shadow-2xl flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-900/80">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-slate-800 rounded-lg text-emerald-400">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-slate-100">Source Quote & Provenance</h3>
              <p className="text-xs text-slate-400 font-mono">
                {item.element_type.toUpperCase()} • {item.canonical_name}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-100 rounded-lg hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6 overflow-y-auto">
          {/* Status Badges */}
          <div className="flex flex-wrap gap-2">
            <span className={`px-2.5 py-1 rounded-full text-xs font-semibold border ${changeTypeBadgeColor}`}>
              {item.change_type}
            </span>
            <span className={`px-2.5 py-1 rounded-full text-xs font-semibold border ${severityBadgeColor}`}>
              {item.severity} SEVERITY
            </span>
            {item.confidence && (
              <span className="px-2.5 py-1 rounded-full text-xs font-mono bg-slate-800 text-slate-300 border border-slate-700">
                Confidence: {(item.confidence * 100).toFixed(0)}%
              </span>
            )}
            {item.chunk_reference && (
              <span className="px-2.5 py-1 rounded-full text-xs font-mono bg-slate-800 text-slate-300 border border-slate-700">
                {item.chunk_reference}
              </span>
            )}
          </div>

          {/* Previous Name if Renamed */}
          {item.previous_name && (
            <div className="p-3 bg-slate-950/60 border border-slate-800 rounded-xl">
              <div className="text-xs text-slate-400 uppercase tracking-wider mb-1">Previous Form</div>
              <div className="text-sm font-mono text-slate-300 line-through decoration-rose-500">
                {item.previous_name}
              </div>
            </div>
          )}

          {/* Verbatim Source Quote */}
          <div>
            <div className="flex items-center space-x-2 text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
              <BookOpen className="w-4 h-4 text-emerald-400" />
              <span>Verbatim Source Grounding</span>
            </div>
            <div className="p-4 bg-slate-950 border border-slate-800/80 rounded-xl relative">
              <div className="absolute top-2 right-2 text-xs font-mono text-slate-600">quote</div>
              <p className="text-sm text-slate-200 italic leading-relaxed font-serif">
                "{item.source_quote || 'No direct source quote grounded for this entry.'}"
              </p>
            </div>
          </div>

          {/* Rationale / Explanation */}
          {item.rationale && (
            <div>
              <div className="flex items-center space-x-2 text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                <ShieldAlert className="w-4 h-4 text-amber-400" />
                <span>Domain Impact Rationale</span>
              </div>
              <div className="p-3.5 bg-amber-950/10 border border-amber-900/30 rounded-xl text-xs text-amber-200/90 leading-relaxed">
                {item.rationale}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-slate-800 bg-slate-900/50 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

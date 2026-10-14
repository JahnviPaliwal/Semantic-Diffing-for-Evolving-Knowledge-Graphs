import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { diffApi } from '../api/client';
import { DiffResponse, DiffItem } from '../api/types';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { CytoscapeGraph } from '../components/CytoscapeGraph';
import { ChangesTable } from '../components/ChangesTable';
import { QuoteDrawer } from '../components/QuoteDrawer';
import { 
  ArrowLeft, 
  Sparkles, 
  GitCompare, 
  Calendar, 
  Layers, 
  FileSpreadsheet,
  FileCode,
  SlidersHorizontal,
  Info
} from 'lucide-react';

export const DiffDetailPage: React.FC = () => {
  const { projectId, diffId } = useParams<{ projectId: string; diffId: string }>();
  const numProjectId = parseInt(projectId || '0', 10);
  const numDiffId = parseInt(diffId || '0', 10);

  const [diff, setDiff] = useState<DiffResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Active view: 'split' | 'graph' | 'table'
  const [viewMode, setViewMode] = useState<'split' | 'graph' | 'table'>('split');

  // Selected item for sliding quote drawer
  const [selectedItem, setSelectedItem] = useState<DiffItem | null>(null);

  useEffect(() => {
    const fetchDiff = async () => {
      if (!numProjectId || !numDiffId) return;
      try {
        setIsLoading(true);
        const data = await diffApi.get(numProjectId, numDiffId);
        setDiff(data);
      } catch (err: any) {
        setError(err.response?.data?.error?.message || err.message || 'Failed to load diff result');
      } finally {
        setIsLoading(false);
      }
    };

    fetchDiff();
  }, [numProjectId, numDiffId]);

  if (isLoading) {
    return <LoadingSpinner message="Loading semantic differential analysis..." />;
  }

  if (error || !diff) {
    return (
      <div className="p-8 text-center text-slate-400">
        <p className="text-rose-400 mb-4">{error || 'Diff not found'}</p>
        <Link to="/" className="text-xs text-indigo-400 underline">Return to Dashboard</Link>
      </div>
    );
  }

  const items = diff.changes?.items || [];
  const addedEntitiesCount = diff.changes?.added_entities?.length || 0;
  const removedEntitiesCount = diff.changes?.removed_entities?.length || 0;
  const renamedEntitiesCount = diff.changes?.renamed_entities?.length || 0;
  const addedRelationsCount = diff.changes?.added_relations?.length || 0;
  const removedRelationsCount = diff.changes?.removed_relations?.length || 0;

  return (
    <div className="space-y-6">
      {/* Top Breadcrumb & Actions Bar */}
      <div>
        <Link
          to={`/projects/${diff.project_id}`}
          className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-400 hover:text-indigo-400 mb-2 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Project
        </Link>
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
                <GitCompare className="w-6 h-6 text-indigo-400" />
                Diff Analysis: {diff.from_version_label || `v${diff.from_version_id}`} → {diff.to_version_label || `v${diff.to_version_id}`}
              </h1>
            </div>
            <p className="text-xs text-slate-400 mt-1 flex items-center gap-3">
              <span>Diff ID: <code className="text-slate-300">#{diff.id}</code></span>
              <span>•</span>
              <span className="flex items-center gap-1">
                <Calendar className="w-3 h-3 text-slate-500" />
                {new Date(diff.created_at).toLocaleString()}
              </span>
            </p>
          </div>

          <div className="flex items-center gap-2">
            <a
              href={diffApi.exportUrl(diff.project_id, diff.id, 'csv')}
              download
              className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 text-xs font-medium rounded-lg transition-colors"
            >
              <FileSpreadsheet className="w-4 h-4 text-emerald-400" />
              Export CSV
            </a>
            <a
              href={diffApi.exportUrl(diff.project_id, diff.id, 'json')}
              download
              className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 text-xs font-medium rounded-lg transition-colors"
            >
              <FileCode className="w-4 h-4 text-indigo-400" />
              Export JSON
            </a>
          </div>
        </div>
      </div>

      {/* Metrics Banner */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-3 text-center">
          <div className="text-xs font-medium text-slate-400">Total Changes</div>
          <div className="text-xl font-bold text-slate-100 mt-1">{items.length}</div>
        </div>
        <div className="bg-emerald-950/20 border border-emerald-900/50 rounded-lg p-3 text-center">
          <div className="text-xs font-medium text-emerald-400">Entities Added</div>
          <div className="text-xl font-bold text-emerald-300 mt-1">+{addedEntitiesCount}</div>
        </div>
        <div className="bg-rose-950/20 border border-rose-900/50 rounded-lg p-3 text-center">
          <div className="text-xs font-medium text-rose-400">Entities Removed</div>
          <div className="text-xl font-bold text-rose-300 mt-1">-{removedEntitiesCount}</div>
        </div>
        <div className="bg-indigo-950/20 border border-indigo-900/50 rounded-lg p-3 text-center">
          <div className="text-xs font-medium text-indigo-400">Entities Renamed</div>
          <div className="text-xl font-bold text-indigo-300 mt-1">~{renamedEntitiesCount}</div>
        </div>
        <div className="bg-emerald-950/20 border border-emerald-900/50 rounded-lg p-3 text-center">
          <div className="text-xs font-medium text-emerald-400">Relations Added</div>
          <div className="text-xl font-bold text-emerald-300 mt-1">+{addedRelationsCount}</div>
        </div>
        <div className="bg-rose-950/20 border border-rose-900/50 rounded-lg p-3 text-center">
          <div className="text-xs font-medium text-rose-400">Relations Removed</div>
          <div className="text-xl font-bold text-rose-300 mt-1">-{removedRelationsCount}</div>
        </div>
      </div>

      {/* Severity Breakdown Strip */}
      {diff.severity_summary && (
        <div className="flex flex-wrap items-center gap-3 p-3 bg-slate-900 border border-slate-800 rounded-lg text-xs">
          <span className="text-slate-400 font-semibold">Severity Breakdown:</span>
          <span className="px-2 py-0.5 rounded bg-rose-950/60 text-rose-300 border border-rose-800">
            Critical: {diff.severity_summary.CRITICAL || 0}
          </span>
          <span className="px-2 py-0.5 rounded bg-amber-950/60 text-amber-300 border border-amber-800">
            High: {diff.severity_summary.HIGH || 0}
          </span>
          <span className="px-2 py-0.5 rounded bg-blue-950/60 text-blue-300 border border-blue-800">
            Medium: {diff.severity_summary.MEDIUM || 0}
          </span>
          <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
            Low: {diff.severity_summary.LOW || 0}
          </span>
        </div>
      )}

      {/* Executive Summary Card */}
      {diff.narrative && (
        <div className="bg-gradient-to-r from-indigo-950/40 via-slate-900 to-slate-900 border border-indigo-800/40 rounded-xl p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-2 text-indigo-300 font-semibold text-sm">
            <Sparkles className="w-4 h-4 text-indigo-400" />
            Executive Semantic Summary
          </div>
          <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-line">
            {diff.narrative}
          </p>
        </div>
      )}

      {/* View Mode Switcher */}
      <div className="flex items-center justify-between pb-2 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setViewMode('split')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              viewMode === 'split'
                ? 'bg-indigo-600 text-white'
                : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'
            }`}
          >
            Split View
          </button>
          <button
            onClick={() => setViewMode('graph')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              viewMode === 'graph'
                ? 'bg-indigo-600 text-white'
                : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'
            }`}
          >
            Graph View
          </button>
          <button
            onClick={() => setViewMode('table')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              viewMode === 'table'
                ? 'bg-indigo-600 text-white'
                : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'
            }`}
          >
            Table View
          </button>
        </div>

        <div className="text-xs text-slate-400 flex items-center gap-2">
          <Info className="w-3.5 h-3.5 text-slate-500" />
          <span>Click any row or graph element to inspect grounded source quotes.</span>
        </div>
      </div>

      {/* Main Content Areas */}
      <div className="space-y-6">
        {/* Graph Display (Split or Full) */}
        {(viewMode === 'split' || viewMode === 'graph') && (
          <div>
            <CytoscapeGraph
              diffChanges={diff.changes}
              title={`Differential Graph (v${diff.from_version_id} → v${diff.to_version_id})`}
            />
          </div>
        )}

        {/* Changes Table Display (Split or Full) */}
        {(viewMode === 'split' || viewMode === 'table') && (
          <div>
            <ChangesTable
              items={items}
              onSelectItem={(item) => setSelectedItem(item)}
            />
          </div>
        )}
      </div>

      {/* Sliding Provenance Quote Drawer */}
      <QuoteDrawer
        item={selectedItem}
        onClose={() => setSelectedItem(null)}
      />
    </div>
  );
};

import React from 'react';
import { GitCommit, ArrowRight, Calendar, Layers, Activity } from 'lucide-react';
import { Version } from '../api/types';

interface TimelineVisualizerProps {
  versions: Version[];
  onDiffSelect?: (v1Id: string, v2Id: string) => void;
  selectedPair?: [string, string] | null;
  className?: string;
}

export const TimelineVisualizer: React.FC<TimelineVisualizerProps> = ({
  versions,
  onDiffSelect,
  selectedPair,
  className = '',
}) => {
  const [selectedV1, setSelectedV1] = React.useState<string>(selectedPair ? selectedPair[0] : '');
  const [selectedV2, setSelectedV2] = React.useState<string>(selectedPair ? selectedPair[1] : '');

  // Sort versions by version number ascending
  const sorted = [...versions].sort((a, b) => {
    const numA = (a as any).version_num ?? (a as any).version_number ?? 0;
    const numB = (b as any).version_num ?? (b as any).version_number ?? 0;
    return numA - numB;
  });

  const handleTriggerDiff = () => {
    if (selectedV1 && selectedV2 && selectedV1 !== selectedV2 && onDiffSelect) {
      onDiffSelect(selectedV1, selectedV2);
    }
  };

  if (sorted.length === 0) {
    return (
      <div className={`bg-slate-900 border border-slate-800 rounded-xl p-6 text-center text-slate-400 ${className}`}>
        No versions uploaded yet to visualize timeline.
      </div>
    );
  }

  return (
    <div className={`bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm ${className}`}>
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-6 border-b border-slate-800 gap-4">
        <div>
          <h3 className="text-lg font-semibold text-slate-100 flex items-center gap-2">
            <GitCommit className="w-5 h-5 text-indigo-400" />
            Knowledge Graph Evolution Timeline
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Tracking graph entity changes, relationships, and temporal persistence across sequential versions.
          </p>
        </div>

        {sorted.length >= 2 && onDiffSelect && (
          <div className="flex items-center gap-3 bg-slate-950 p-2.5 rounded-lg border border-slate-800">
            <span className="text-xs text-slate-400 font-medium">Compare:</span>
            <select
              value={selectedV1}
              onChange={(e) => setSelectedV1(e.target.value)}
              className="bg-slate-900 border border-slate-700 text-xs text-slate-200 rounded px-2 py-1 focus:ring-1 focus:ring-indigo-500 focus:outline-none"
            >
              <option value="">Select V1 (Base)</option>
              {sorted.map((v) => {
                const num = (v as any).version_num ?? (v as any).version_number ?? v.id;
                return (
                  <option key={String(v.id)} value={String(v.id)}>
                    v{num}: {v.filename}
                  </option>
                );
              })}
            </select>
            <ArrowRight className="w-4 h-4 text-slate-500" />
            <select
              value={selectedV2}
              onChange={(e) => setSelectedV2(e.target.value)}
              className="bg-slate-900 border border-slate-700 text-xs text-slate-200 rounded px-2 py-1 focus:ring-1 focus:ring-indigo-500 focus:outline-none"
            >
              <option value="">Select V2 (Target)</option>
              {sorted.map((v) => {
                const num = (v as any).version_num ?? (v as any).version_number ?? v.id;
                return (
                  <option key={String(v.id)} value={String(v.id)}>
                    v{num}: {v.filename}
                  </option>
                );
              })}
            </select>
            <button
              onClick={handleTriggerDiff}
              disabled={!selectedV1 || !selectedV2 || selectedV1 === selectedV2}
              className="px-3 py-1 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed text-xs font-medium text-white rounded transition-colors"
            >
              Compute Diff
            </button>
          </div>
        )}
      </div>

      {/* Horizontal timeline scroll */}
      <div className="mt-8 overflow-x-auto pb-4 pt-2">
        <div className="flex items-stretch min-w-max gap-4 px-2">
          {sorted.map((version, index) => {
            const vId = String(version.id);
            const isBase = selectedV1 === vId;
            const isTarget = selectedV2 === vId;
            const verNum = (version as any).version_num ?? (version as any).version_number ?? index + 1;
            const nodeCount = version.node_count ?? (version as any).graph_data?.nodes?.length ?? 0;
            const edgeCount = version.edge_count ?? (version as any).graph_data?.edges?.length ?? 0;

            return (
              <React.Fragment key={vId}>
                <div
                  className={`relative flex flex-col justify-between w-64 p-4 rounded-lg border transition-all ${
                    isBase
                      ? 'bg-blue-950/40 border-blue-500 ring-2 ring-blue-500/20'
                      : isTarget
                      ? 'bg-indigo-950/40 border-indigo-500 ring-2 ring-indigo-500/20'
                      : 'bg-slate-950 border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="px-2 py-0.5 text-xs font-semibold rounded bg-slate-800 text-indigo-300">
                        Version {verNum}
                      </span>
                      {isBase && (
                        <span className="text-[10px] uppercase font-bold text-blue-400 bg-blue-950 px-1.5 py-0.5 rounded border border-blue-800">
                          Base (v1)
                        </span>
                      )}
                      {isTarget && (
                        <span className="text-[10px] uppercase font-bold text-indigo-400 bg-indigo-950 px-1.5 py-0.5 rounded border border-indigo-800">
                          Target (v2)
                        </span>
                      )}
                    </div>
                    <h4 className="text-sm font-medium text-slate-200 truncate" title={version.filename}>
                      {version.filename}
                    </h4>
                    <p className="text-[11px] text-slate-400 flex items-center gap-1 mt-1">
                      <Calendar className="w-3 h-3" />
                      {new Date(version.created_at).toLocaleDateString()}
                    </p>
                  </div>

                  <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
                    <span className="flex items-center gap-1">
                      <Layers className="w-3.5 h-3.5 text-slate-500" />
                      <strong className="text-slate-300">{nodeCount}</strong> entities
                    </span>
                    <span className="flex items-center gap-1">
                      <Activity className="w-3.5 h-3.5 text-slate-500" />
                      <strong className="text-slate-300">{edgeCount}</strong> relations
                    </span>
                  </div>

                  {onDiffSelect && sorted.length > 1 && (
                    <div className="mt-3 pt-2 flex gap-1.5">
                      <button
                        onClick={() => setSelectedV1(vId)}
                        className={`text-[10px] px-2 py-1 rounded flex-1 font-medium transition-colors ${
                          isBase
                            ? 'bg-blue-600 text-white'
                            : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                        }`}
                      >
                        Set Base
                      </button>
                      <button
                        onClick={() => setSelectedV2(vId)}
                        className={`text-[10px] px-2 py-1 rounded flex-1 font-medium transition-colors ${
                          isTarget
                            ? 'bg-indigo-600 text-white'
                            : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                        }`}
                      >
                        Set Target
                      </button>
                    </div>
                  )}
                </div>

                {index < sorted.length - 1 && (
                  <div className="flex flex-col items-center justify-center self-center px-1">
                    <div className="w-8 h-0.5 bg-slate-700 relative">
                      <div className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-1 border-t-4 border-b-4 border-l-6 border-t-transparent border-b-transparent border-l-slate-700" />
                    </div>
                    {onDiffSelect && (
                      <button
                        onClick={() => onDiffSelect(vId, String(sorted[index + 1].id))}
                        className="mt-2 text-[10px] text-slate-400 hover:text-indigo-400 transition-colors whitespace-nowrap"
                        title="Diff Pair"
                      >
                        Diff Pair
                      </button>
                    )}
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>
    </div>
  );
};

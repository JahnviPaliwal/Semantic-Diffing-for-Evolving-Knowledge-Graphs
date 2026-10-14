import React, { useState } from 'react';
import { Search, Filter, Eye, ChevronRight } from 'lucide-react';
import { DiffItem, SeverityLevel, ChangeType } from '../api/types';

interface ChangesTableProps {
  items: DiffItem[];
  onSelectItem: (item: DiffItem) => void;
}

export const ChangesTable: React.FC<ChangesTableProps> = ({ items, onSelectItem }) => {
  const [selectedSeverity, setSelectedSeverity] = useState<string>('ALL');
  const [selectedType, setSelectedType] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const filteredItems = items.filter((item) => {
    const matchesSeverity = selectedSeverity === 'ALL' || item.severity === selectedSeverity;
    const matchesType = selectedType === 'ALL' || item.change_type === selectedType;
    const matchesSearch =
      searchQuery === '' ||
      item.canonical_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (item.source_quote && item.source_quote.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (item.rationale && item.rationale.toLowerCase().includes(searchQuery.toLowerCase()));

    return matchesSeverity && matchesType && matchesSearch;
  });

  const getSeverityStyle = (sev: SeverityLevel) => {
    switch (sev) {
      case 'CRITICAL':
        return 'bg-rose-500/10 text-rose-400 border-rose-500/30';
      case 'HIGH':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
      case 'MEDIUM':
        return 'bg-blue-500/10 text-blue-400 border-blue-500/30';
      case 'LOW':
        return 'bg-slate-500/10 text-slate-400 border-slate-600/30';
    }
  };

  const getChangeTypeStyle = (type: ChangeType) => {
    switch (type) {
      case 'ADDED':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
      case 'REMOVED':
        return 'bg-rose-500/10 text-rose-400 border-rose-500/30';
      case 'RENAMED':
        return 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30';
      case 'MODIFIED':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
      case 'UNCHANGED':
        return 'bg-slate-500/10 text-slate-400 border-slate-600/30';
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-lg">
      {/* Controls Bar */}
      <div className="p-4 border-b border-slate-800 flex flex-col md:flex-row gap-4 items-start md:items-center justify-between bg-slate-900/50">
        {/* Search */}
        <div className="relative w-full md:w-72">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search changes or quotes..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition-colors"
          />
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-2 w-full md:w-auto">
          {/* Severity selector */}
          <div className="flex items-center space-x-1 bg-slate-950 p-1 rounded-lg border border-slate-800 text-xs">
            <span className="text-slate-500 px-2 font-medium">Severity:</span>
            {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((s) => (
              <button
                key={s}
                onClick={() => setSelectedSeverity(s)}
                className={`px-2 py-1 rounded text-xs font-semibold transition-colors ${
                  selectedSeverity === s
                    ? 'bg-emerald-600 text-white'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                }`}
              >
                {s}
              </button>
            ))}
          </div>

          {/* Change Type selector */}
          <div className="flex items-center space-x-1 bg-slate-950 p-1 rounded-lg border border-slate-800 text-xs">
            <span className="text-slate-500 px-2 font-medium">Type:</span>
            {['ALL', 'ADDED', 'REMOVED', 'RENAMED', 'MODIFIED'].map((t) => (
              <button
                key={t}
                onClick={() => setSelectedType(t)}
                className={`px-2 py-1 rounded text-xs font-semibold transition-colors ${
                  selectedType === t
                    ? 'bg-slate-700 text-white'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                }`}
              >
                {t}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs text-slate-300">
          <thead className="bg-slate-950/70 uppercase text-slate-400 border-b border-slate-800 tracking-wider">
            <tr>
              <th className="px-4 py-3">Element</th>
              <th className="px-4 py-3">Change Type</th>
              <th className="px-4 py-3">Target Name / Triple</th>
              <th className="px-4 py-3">Severity</th>
              <th className="px-4 py-3">Verbatim Source Quote</th>
              <th className="px-4 py-3 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {filteredItems.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-slate-500">
                  No structural changes matching the active filters.
                </td>
              </tr>
            ) : (
              filteredItems.map((item, idx) => (
                <tr
                  key={idx}
                  onClick={() => onSelectItem(item)}
                  className="hover:bg-slate-800/40 cursor-pointer transition-colors"
                >
                  <td className="px-4 py-3 font-mono text-slate-400">
                    <span className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700">
                      {item.element_type}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`px-2.5 py-0.5 rounded-full font-semibold border ${getChangeTypeStyle(
                        item.change_type
                      )}`}
                    >
                      {item.change_type}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-medium text-slate-100 max-w-xs truncate">
                    {item.canonical_name}
                    {item.previous_name && (
                      <span className="block text-slate-500 text-[10px] font-mono">
                        was: {item.previous_name}
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`px-2 py-0.5 rounded font-semibold border ${getSeverityStyle(
                        item.severity
                      )}`}
                    >
                      {item.severity}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-400 italic max-w-md truncate">
                    {item.source_quote ? `"${item.source_quote}"` : '—'}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectItem(item);
                      }}
                      className="p-1 rounded text-slate-400 hover:text-emerald-400 hover:bg-slate-800 transition-colors"
                      title="Inspect source quote"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      <div className="p-3 border-t border-slate-800 bg-slate-950/40 text-[11px] text-slate-500 flex justify-between">
        <span>Showing {filteredItems.length} of {items.length} changes</span>
        <span>Click any row to view verbatim grounding & confidence</span>
      </div>
    </div>
  );
};

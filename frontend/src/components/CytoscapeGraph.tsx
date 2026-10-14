import React, { useEffect, useRef, useState } from 'react';
import cytoscape, { Core, ElementDefinition } from 'cytoscape';
import { Maximize2, ZoomIn, ZoomOut, RefreshCw, Layers } from 'lucide-react';
import { DiffChanges } from '../api/types';

interface CytoscapeGraphProps {
  diffChanges: DiffChanges;
  title?: string;
}

export const CytoscapeGraph: React.FC<CytoscapeGraphProps> = ({ diffChanges, title = 'Knowledge Graph Diff Visualizer' }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);
  const [selectedElement, setSelectedElement] = useState<any>(null);
  const [layoutName, setLayoutName] = useState<string>('cose');

  useEffect(() => {
    if (!containerRef.current) return;

    const elements: ElementDefinition[] = [];
    const addedNodes = new Set(diffChanges.added_entities);
    const removedNodes = new Set(diffChanges.removed_entities);
    const renamedMap = new Map(diffChanges.renamed_entities.map((r) => [r.to, r.from]));
    const unchangedNodes = new Set(diffChanges.unchanged_entities);

    // 1. Add all unique nodes
    const allNodeNames = new Set([
      ...diffChanges.added_entities,
      ...diffChanges.removed_entities,
      ...diffChanges.renamed_entities.map((r) => r.to),
      ...diffChanges.unchanged_entities,
    ]);

    // Also include any subjects/objects from relations
    diffChanges.added_relations.forEach(([s, , o]) => {
      allNodeNames.add(s);
      allNodeNames.add(o);
    });
    diffChanges.removed_relations.forEach(([s, , o]) => {
      allNodeNames.add(s);
      allNodeNames.add(o);
    });
    diffChanges.unchanged_relations.forEach(([s, , o]) => {
      allNodeNames.add(s);
      allNodeNames.add(o);
    });

    allNodeNames.forEach((nodeName) => {
      let status = 'UNCHANGED';
      let color = '#64748b'; // Slate

      if (addedNodes.has(nodeName)) {
        status = 'ADDED';
        color = '#10b981'; // Emerald
      } else if (removedNodes.has(nodeName)) {
        status = 'REMOVED';
        color = '#f43f5e'; // Rose
      } else if (renamedMap.has(nodeName)) {
        status = 'RENAMED';
        color = '#6366f1'; // Indigo
      } else if (unchangedNodes.has(nodeName)) {
        status = 'UNCHANGED';
        color = '#475569';
      }

      elements.push({
        data: {
          id: nodeName,
          label: nodeName,
          status,
          color,
          wasRenamedFrom: renamedMap.get(nodeName),
        },
      });
    });

    // 2. Add edges
    const addedRelKeys = new Set(diffChanges.added_relations.map(([s, p, o]) => `${s}->${p}->${o}`));
    const removedRelKeys = new Set(diffChanges.removed_relations.map(([s, p, o]) => `${s}->${p}->${o}`));

    diffChanges.added_relations.forEach(([s, p, o], idx) => {
      elements.push({
        data: {
          id: `added_e_${idx}`,
          source: s,
          target: o,
          label: p,
          status: 'ADDED',
          color: '#10b981',
        },
      });
    });

    diffChanges.removed_relations.forEach(([s, p, o], idx) => {
      elements.push({
        data: {
          id: `rem_e_${idx}`,
          source: s,
          target: o,
          label: p,
          status: 'REMOVED',
          color: '#f43f5e',
        },
      });
    });

    diffChanges.modified_relations.forEach((mr, idx) => {
      elements.push({
        data: {
          id: `mod_e_${idx}`,
          source: mr.subject,
          target: mr.object,
          label: `${mr.old_predicate} ➔ ${mr.new_predicate}`,
          status: 'MODIFIED',
          color: '#f59e0b',
        },
      });
    });

    diffChanges.unchanged_relations.forEach(([s, p, o], idx) => {
      elements.push({
        data: {
          id: `unch_e_${idx}`,
          source: s,
          target: o,
          label: p,
          status: 'UNCHANGED',
          color: '#475569',
        },
      });
    });

    const cy = cytoscape({
      container: containerRef.current,
      elements,
      style: [
        {
          selector: 'node',
          style: {
            'background-color': 'data(color)',
            label: 'data(label)',
            color: '#f8fafc',
            'font-size': '11px',
            'font-family': 'Inter, sans-serif',
            'text-valign': 'center',
            'text-halign': 'center',
            'text-wrap': 'wrap',
            'text-max-width': '120px',
            width: 'mapData(label.length, 5, 30, 45, 90)',
            height: 'mapData(label.length, 5, 30, 45, 90)',
            'border-width': 2,
            'border-color': '#0f172a',
            'text-outline-width': 2,
            'text-outline-color': '#0f172a',
          },
        },
        {
          selector: 'node:selected',
          style: {
            'border-width': 4,
            'border-color': '#38bdf8',
            'underlay-color': '#38bdf8',
            'underlay-padding': 4,
            'underlay-opacity': 0.5,
          },
        },
        {
          selector: 'edge',
          style: {
            width: 2,
            'line-color': 'data(color)',
            'target-arrow-color': 'data(color)',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            label: 'data(label)',
            'font-size': '9px',
            color: '#94a3b8',
            'text-outline-width': 1.5,
            'text-outline-color': '#0b0f17',
          },
        },
      ],
      layout: {
        name: layoutName,
        animate: false,
        padding: 50,
      } as any,
    });

    cy.on('tap', 'node', (evt) => {
      const node = evt.target;
      setSelectedElement({
        type: 'node',
        label: node.data('label'),
        status: node.data('status'),
        wasRenamedFrom: node.data('wasRenamedFrom'),
      });
    });

    cy.on('tap', 'edge', (evt) => {
      const edge = evt.target;
      setSelectedElement({
        type: 'edge',
        source: edge.data('source'),
        target: edge.data('target'),
        label: edge.data('label'),
        status: edge.data('status'),
      });
    });

    cy.on('tap', (evt) => {
      if (evt.target === cy) {
        setSelectedElement(null);
      }
    });

    cyRef.current = cy;

    return () => {
      cy.destroy();
    };
  }, [diffChanges, layoutName]);

  const handleZoomIn = () => cyRef.current?.zoom(cyRef.current.zoom() * 1.25);
  const handleZoomOut = () => cyRef.current?.zoom(cyRef.current.zoom() * 0.8);
  const handleFit = () => cyRef.current?.fit();
  const handleResetLayout = () => {
    cyRef.current?.layout({ name: layoutName, animate: true } as any).run();
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-lg flex flex-col">
      {/* Visualizer Header & Toolbar */}
      <div className="px-4 py-3 border-b border-slate-800 bg-slate-900/70 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center space-x-2">
          <Layers className="w-4 h-4 text-emerald-400" />
          <h3 className="text-sm font-semibold text-slate-100">{title}</h3>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap items-center gap-3 text-xs">
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block" />
            <span className="text-slate-300">Added</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500 inline-block" />
            <span className="text-slate-300">Removed</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-indigo-500 inline-block" />
            <span className="text-slate-300">Renamed</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block" />
            <span className="text-slate-300">Modified</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-slate-600 inline-block" />
            <span className="text-slate-400">Unchanged</span>
          </div>
        </div>

        {/* Controls */}
        <div className="flex items-center space-x-1 bg-slate-950 p-1 rounded-lg border border-slate-800">
          <select
            value={layoutName}
            onChange={(e) => setLayoutName(e.target.value)}
            className="bg-slate-900 text-slate-300 border border-slate-800 rounded px-2 py-1 text-xs focus:outline-none"
          >
            <option value="cose">Force-Directed (Cose)</option>
            <option value="concentric">Concentric</option>
            <option value="circle">Circular</option>
            <option value="breadthfirst">Tree / Breadthfirst</option>
          </select>
          <button
            onClick={handleZoomIn}
            className="p-1 text-slate-400 hover:text-slate-100 rounded hover:bg-slate-800 transition-colors"
            title="Zoom In"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={handleZoomOut}
            className="p-1 text-slate-400 hover:text-slate-100 rounded hover:bg-slate-800 transition-colors"
            title="Zoom Out"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={handleFit}
            className="p-1 text-slate-400 hover:text-slate-100 rounded hover:bg-slate-800 transition-colors"
            title="Fit to Screen"
          >
            <Maximize2 className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={handleResetLayout}
            className="p-1 text-slate-400 hover:text-slate-100 rounded hover:bg-slate-800 transition-colors"
            title="Re-run physics layout"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Canvas */}
      <div className="relative w-full h-[520px] bg-slate-950">
        <div ref={containerRef} className="w-full h-full" />

        {/* Inspector Popover */}
        {selectedElement && (
          <div className="absolute bottom-4 left-4 max-w-sm p-4 bg-slate-900/95 border border-slate-800 rounded-xl shadow-2xl backdrop-blur-md text-xs z-10 animate-in fade-in">
            <div className="font-semibold text-slate-200 mb-1 flex items-center justify-between">
              <span>Selected {selectedElement.type.toUpperCase()}</span>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-emerald-400">
                {selectedElement.status}
              </span>
            </div>
            {selectedElement.type === 'node' ? (
              <div>
                <p className="text-slate-300 font-medium text-sm mt-1">{selectedElement.label}</p>
                {selectedElement.wasRenamedFrom && (
                  <p className="text-slate-400 text-xs mt-1">
                    Renamed from: <span className="line-through text-rose-400">{selectedElement.wasRenamedFrom}</span>
                  </p>
                )}
              </div>
            ) : (
              <div>
                <p className="text-slate-300 text-xs mt-1">
                  <span className="text-slate-400 font-mono">{selectedElement.source}</span>
                  <span className="text-emerald-400 mx-1 font-bold">-[{selectedElement.label}]-➔</span>
                  <span className="text-slate-400 font-mono">{selectedElement.target}</span>
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

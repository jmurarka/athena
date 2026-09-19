'use client';

import React, { useState, useCallback, useEffect } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  Edge,
  Node,
  BackgroundVariant,
  Panel,
  Handle,
  Position
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { 
  Square, 
  RectangleHorizontal, 
  Database, 
  Type, 
  Save, 
  Plus, 
  Trash2, 
  Maximize2, 
  Minimize2, 
  Loader2, 
  CheckCircle2, 
  Palette,
  Sparkles,
  ArrowRight
} from 'lucide-react';
import { fetchWithAuth } from '@/lib/api';

// Curated Minimalist Palette with Lavender contrast
const COLOR_PRESETS = [
  { id: 'lavender', label: 'Lavender', bg: '#f5f3ff', border: '#c4b5fd', text: '#5b21b6' },
  { id: 'white', label: 'White', bg: '#ffffff', border: '#cbd5e1', text: '#0f172a' },
  { id: 'grey', label: 'Grey', bg: '#f8fafc', border: '#94a3b8', text: '#334155' },
  { id: 'mint', label: 'Mint', bg: '#f0fdf4', border: '#86efac', text: '#166534' },
  { id: 'sky', label: 'Sky', bg: '#f0f9ff', border: '#7dd3fc', text: '#0369a1' },
  { id: 'amber', label: 'Amber', bg: '#fffbeb', border: '#fcd34d', text: '#b45309' }
];

// Custom Flow Node with 4-way handles for seamless connection
const CustomShapeNode = ({ data, selected }: any) => {
  const isSquare = data.shape === 'square';
  const isNote = data.shape === 'note';
  const isDb = data.shape === 'db';

  return (
    <div
      style={{
        backgroundColor: data.bg || '#ffffff',
        borderColor: selected ? '#7c3aed' : (data.border || '#cbd5e1'),
        borderWidth: selected ? '2px' : '1px',
        color: data.text || '#0f172a',
        width: isSquare ? '110px' : isNote ? '160px' : '180px',
        minHeight: isSquare ? '110px' : '65px'
      }}
      className={`relative px-3 py-2.5 rounded-lg shadow-xs transition-all flex flex-col justify-center items-center text-center font-sans ${
        isNote ? 'border-dashed' : 'border-solid'
      }`}
    >
      {/* 4 Connection Handles */}
      <Handle type="target" position={Position.Top} className="!w-2 !h-2 !bg-[#8b5cf6]" />
      <Handle type="source" position={Position.Bottom} className="!w-2 !h-2 !bg-[#8b5cf6]" />
      <Handle type="target" position={Position.Left} className="!w-2 !h-2 !bg-[#8b5cf6]" />
      <Handle type="source" position={Position.Right} className="!w-2 !h-2 !bg-[#8b5cf6]" />

      <div className="flex items-center gap-1.5 mb-1 opacity-70">
        {isDb ? (
          <Database className="w-3 h-3 text-[#7c3aed]" />
        ) : isSquare ? (
          <Square className="w-3 h-3 text-slate-500" />
        ) : isNote ? (
          <Type className="w-3 h-3 text-amber-600" />
        ) : (
          <RectangleHorizontal className="w-3 h-3 text-[#7c3aed]" />
        )}
        <span className="text-[10px] uppercase font-mono tracking-wider font-semibold">
          {data.subtext || (isDb ? 'Data Store' : isNote ? 'Note' : isSquare ? 'Module' : 'Service')}
        </span>
      </div>

      <div className="text-xs font-semibold leading-snug break-words max-w-full">
        {data.label || 'Node Title'}
      </div>
    </div>
  );
};

const nodeTypes = {
  customShape: CustomShapeNode
};

const defaultInitialNodes: Node[] = [
  {
    id: 'node-client',
    type: 'customShape',
    position: { x: 40, y: 120 },
    data: { 
      label: 'Web Client (Next.js)', 
      shape: 'rect', 
      subtext: 'Frontend', 
      bg: '#ffffff', 
      border: '#cbd5e1', 
      text: '#0f172a' 
    }
  },
  {
    id: 'node-api',
    type: 'customShape',
    position: { x: 260, y: 120 },
    data: { 
      label: 'API Gateway (FastAPI)', 
      shape: 'rect', 
      subtext: 'Gateway', 
      bg: '#f5f3ff', 
      border: '#c4b5fd', 
      text: '#5b21b6' 
    }
  },
  {
    id: 'node-db',
    type: 'customShape',
    position: { x: 480, y: 70 },
    data: { 
      label: 'Database (SQLite/Postgres)', 
      shape: 'db', 
      subtext: 'Database', 
      bg: '#f0fdf4', 
      border: '#86efac', 
      text: '#166534' 
    }
  },
  {
    id: 'node-worker',
    type: 'customShape',
    position: { x: 480, y: 180 },
    data: { 
      label: 'Background Agents', 
      shape: 'square', 
      subtext: 'Worker', 
      bg: '#fffbeb', 
      border: '#fcd34d', 
      text: '#b45309' 
    }
  }
];

const defaultInitialEdges: Edge[] = [
  { id: 'e-client-api', source: 'node-client', target: 'node-api', animated: true, label: 'JSON HTTP' },
  { id: 'e-api-db', source: 'node-api', target: 'node-db', label: 'Query' },
  { id: 'e-api-worker', source: 'node-api', target: 'node-worker', animated: true, label: 'Dispatch' }
];

interface FlowchartCanvasProps {
  projectId: string | null;
  projectTitle: string;
  isExpanded: boolean;
  onToggleExpand: () => void;
}

export default function FlowchartCanvas({
  projectId,
  projectTitle,
  isExpanded,
  onToggleExpand,
}: FlowchartCanvasProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState(defaultInitialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(defaultInitialEdges);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [editLabel, setEditLabel] = useState('');
  const [selectedColor, setSelectedColor] = useState(COLOR_PRESETS[0]);
  const [isSaving, setIsSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  // Load existing canvas state from backend whenever project changes
  useEffect(() => {
    if (!projectId) return;

    async function loadCanvas() {
      try {
        const data = await fetchWithAuth(`/api/projects/${projectId}/canvas`);
        if (data && data.canvas_json && Array.isArray(data.canvas_json.nodes) && data.canvas_json.nodes.length > 0) {
          // Normalize node type to ensure customShape rendering
          const loadedNodes = data.canvas_json.nodes.map((n: any) => ({
            ...n,
            type: 'customShape',
            data: {
              ...n.data,
              bg: n.data.bg || '#ffffff',
              border: n.data.border || '#cbd5e1',
              text: n.data.text || '#0f172a'
            }
          }));
          setNodes(loadedNodes);
          if (Array.isArray(data.canvas_json.edges)) {
            setEdges(data.canvas_json.edges);
          }
        } else {
          setNodes(defaultInitialNodes);
          setEdges(defaultInitialEdges);
        }
      } catch (err) {
        console.warn('Using default canvas layout for project:', err);
        setNodes(defaultInitialNodes);
        setEdges(defaultInitialEdges);
      }
    }
    loadCanvas();
  }, [projectId, setNodes, setEdges]);

  // Connect handler
  const onConnect = useCallback(
    (params: Connection) => {
      setEdges((eds) =>
        addEdge(
          {
            ...params,
            animated: true,
            style: { stroke: '#7c3aed', strokeWidth: 1.5 }
          },
          eds
        )
      );
    },
    [setEdges]
  );

  // Node selection handler
  const onNodeClick = (_: any, node: Node) => {
    setSelectedNode(node);
    setEditLabel(String(node.data?.label || ''));
  };

  const onPaneClick = () => {
    setSelectedNode(null);
  };

  // Add new shape onto the canvas
  const handleAddShape = (shape: 'rect' | 'square' | 'db' | 'note') => {
    const id = `node-${Date.now()}`;
    const xPos = 120 + (nodes.length % 4) * 50;
    const yPos = 100 + (nodes.length % 5) * 40;

    const labelMap = {
      rect: 'New Service',
      square: 'New Module',
      db: 'New Database',
      note: 'Architecture Note'
    };

    const newNode: Node = {
      id,
      type: 'customShape',
      position: { x: xPos, y: yPos },
      data: {
        label: labelMap[shape],
        shape,
        bg: selectedColor.bg,
        border: selectedColor.border,
        text: selectedColor.text,
        subtext: shape === 'db' ? 'Data Store' : shape === 'note' ? 'Note' : shape === 'square' ? 'Module' : 'Service'
      }
    };

    setNodes((nds) => [...nds, newNode]);
    setSelectedNode(newNode);
    setEditLabel(labelMap[shape]);
  };

  // Update selected node label
  const handleLabelChange = (newLabel: string) => {
    setEditLabel(newLabel);
    if (!selectedNode) return;
    setNodes((nds) =>
      nds.map((n) => (n.id === selectedNode.id ? { ...n, data: { ...n.data, label: newLabel } } : n))
    );
  };

  // Apply color to selected node
  const handleApplyColor = (color: typeof COLOR_PRESETS[0]) => {
    setSelectedColor(color);
    if (!selectedNode) return;
    setNodes((nds) =>
      nds.map((n) =>
        n.id === selectedNode.id
          ? {
              ...n,
              data: {
                ...n.data,
                bg: color.bg,
                border: color.border,
                text: color.text
              }
            }
          : n
      )
    );
  };

  // Delete selected node
  const handleDeleteSelected = () => {
    if (!selectedNode) return;
    setNodes((nds) => nds.filter((n) => n.id !== selectedNode.id));
    setEdges((eds) => eds.filter((e) => e.source !== selectedNode.id && e.target !== selectedNode.id));
    setSelectedNode(null);
  };

  // Persist canvas layout to backend
  const handleSaveCanvas = async () => {
    if (!projectId) return;
    setIsSaving(true);
    try {
      await fetchWithAuth(`/api/projects/${projectId}/canvas`, {
        method: 'PUT',
        body: JSON.stringify({
          canvas_json: {
            nodes,
            edges,
            viewport: { x: 0, y: 0, zoom: 1 }
          }
        })
      });
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 2500);
    } catch (err) {
      console.error('Failed to save canvas state:', err);
      alert('Could not save flowchart layout to database.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-[#fbfbfa] font-sans relative overflow-hidden select-none">
      {/* Canvas Top Bar */}
      <header className="h-11 px-4 border-b border-[#eaeaea] bg-white flex items-center justify-between text-xs text-slate-600 shrink-0 z-10">
        <div className="flex items-center gap-2">
          <span className="text-[#7c3aed] font-semibold flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Architecture Flowchart</span>
          </span>
          <span className="text-slate-300">|</span>
          <span className="text-[11px] text-slate-400 font-mono">
            {nodes.length} nodes • {edges.length} arrows
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleSaveCanvas}
            disabled={isSaving || !projectId}
            className="flex items-center gap-1 px-2.5 py-1 rounded bg-[#7c3aed] hover:bg-[#6d28d9] text-white text-xs font-medium transition shadow-xs disabled:opacity-50"
          >
            {isSaving ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : savedSuccess ? (
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-300" />
            ) : (
              <Save className="w-3.5 h-3.5" />
            )}
            <span>{savedSuccess ? 'Saved' : 'Save Flowchart'}</span>
          </button>

          <button
            onClick={onToggleExpand}
            className="p-1 rounded hover:bg-slate-100 text-slate-500 transition"
            title={isExpanded ? 'Restore split layout' : 'Expand full canvas'}
          >
            {isExpanded ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
          </button>
        </div>
      </header>

      {/* Interactive Shape & Color Toolbar Panel */}
      <div className="px-4 py-2 bg-white border-b border-slate-100 flex items-center justify-between gap-3 text-xs flex-wrap z-10 shadow-2xs">
        {/* Insert Shapes */}
        <div className="flex items-center gap-1.5">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mr-1">Add:</span>
          
          <button
            onClick={() => handleAddShape('rect')}
            className="flex items-center gap-1 px-2 py-1 rounded border border-slate-200 hover:border-[#7c3aed] hover:bg-[#f5f3ff] text-slate-700 hover:text-[#6d28d9] transition text-[11px] font-medium"
            title="Add Process / Service Node"
          >
            <RectangleHorizontal className="w-3 h-3" />
            <span>Service</span>
          </button>

          <button
            onClick={() => handleAddShape('square')}
            className="flex items-center gap-1 px-2 py-1 rounded border border-slate-200 hover:border-[#7c3aed] hover:bg-[#f5f3ff] text-slate-700 hover:text-[#6d28d9] transition text-[11px] font-medium"
            title="Add Module / Component"
          >
            <Square className="w-3 h-3" />
            <span>Module</span>
          </button>

          <button
            onClick={() => handleAddShape('db')}
            className="flex items-center gap-1 px-2 py-1 rounded border border-slate-200 hover:border-[#7c3aed] hover:bg-[#f5f3ff] text-slate-700 hover:text-[#6d28d9] transition text-[11px] font-medium"
            title="Add Database Node"
          >
            <Database className="w-3 h-3" />
            <span>Data Store</span>
          </button>

          <button
            onClick={() => handleAddShape('note')}
            className="flex items-center gap-1 px-2 py-1 rounded border border-slate-200 hover:border-[#7c3aed] hover:bg-[#f5f3ff] text-slate-700 hover:text-[#6d28d9] transition text-[11px] font-medium"
            title="Add Text Note"
          >
            <Type className="w-3 h-3" />
            <span>Note</span>
          </button>
        </div>

        {/* Color Palette Selector */}
        <div className="flex items-center gap-1.5">
          <Palette className="w-3 h-3 text-slate-400 mr-0.5" />
          {COLOR_PRESETS.map((color) => (
            <button
              key={color.id}
              onClick={() => handleApplyColor(color)}
              title={`${color.label} Preset`}
              style={{ backgroundColor: color.bg, borderColor: color.border }}
              className={`w-4.5 h-4.5 rounded-full border-2 transition transform hover:scale-110 ${
                selectedColor.id === color.id ? 'ring-2 ring-[#7c3aed] ring-offset-1' : ''
              }`}
            />
          ))}
        </div>
      </div>

      {/* Selected Node Quick Inspector Bar */}
      {selectedNode && (
        <div className="px-4 py-1.5 bg-[#ede9fe]/80 border-b border-[#ddd6fe] flex items-center justify-between text-xs text-[#5b21b6] animate-in fade-in slide-in-from-top-1 duration-100 z-10">
          <div className="flex items-center gap-2 flex-1 max-w-md">
            <span className="font-semibold text-[11px] shrink-0">Selected:</span>
            <input
              type="text"
              value={editLabel}
              onChange={(e) => handleLabelChange(e.target.value)}
              placeholder="Edit node label..."
              className="bg-white border border-[#c4b5fd] rounded px-2 py-0.5 text-xs text-slate-800 outline-none focus:ring-1 focus:ring-[#7c3aed] w-full"
            />
          </div>

          <button
            onClick={handleDeleteSelected}
            className="flex items-center gap-1 text-xs font-medium text-rose-600 hover:text-rose-700 hover:bg-white/80 px-2 py-0.5 rounded transition"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Delete</span>
          </button>
        </div>
      )}

      {/* Interactive Flowchart Canvas (XYFlow) */}
      <div className="flex-1 w-full h-full relative bg-white">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={onNodeClick}
          onPaneClick={onPaneClick}
          fitView
          className="bg-white"
        >
          <Background variant={BackgroundVariant.Dots} gap={16} size={1} color="#cbd5e1" />
          <Controls />
        </ReactFlow>

        {/* Tip Badge */}
        <div className="absolute bottom-3 left-3 bg-white/90 backdrop-blur-xs border border-slate-200 rounded-md px-2.5 py-1 text-[11px] text-slate-500 shadow-xs pointer-events-none flex items-center gap-1.5">
          <span className="text-[#7c3aed] font-bold">Tip:</span>
          <span>Drag dots to connect with arrows • Click node to edit/color</span>
        </div>
      </div>
    </div>
  );
}

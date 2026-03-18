'use client';

import { useMemo, useCallback } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
  type NodeTypes,
  Handle,
  Position,
  MarkerType,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import dagre from 'dagre';

import type { GraphNode, PrerequisiteEdge } from '@/lib/api/prerequisites';

// ============================================================================
// Chapter color palette
// ============================================================================

const CHAPTER_COLORS = [
  { bg: '#dbeafe', border: '#3b82f6', text: '#1e40af' }, // blue
  { bg: '#dcfce7', border: '#22c55e', text: '#166534' }, // green
  { bg: '#fef3c7', border: '#f59e0b', text: '#92400e' }, // amber
  { bg: '#fce7f3', border: '#ec4899', text: '#9d174d' }, // pink
  { bg: '#e0e7ff', border: '#6366f1', text: '#3730a3' }, // indigo
  { bg: '#f3e8ff', border: '#a855f7', text: '#6b21a8' }, // purple
  { bg: '#ccfbf1', border: '#14b8a6', text: '#115e59' }, // teal
  { bg: '#fee2e2', border: '#ef4444', text: '#991b1b' }, // red
  { bg: '#fef9c3', border: '#eab308', text: '#854d0e' }, // yellow
  { bg: '#e0f2fe', border: '#0ea5e9', text: '#075985' }, // sky
];

function getChapterColor(chapterIndex: number) {
  return CHAPTER_COLORS[chapterIndex % CHAPTER_COLORS.length];
}

// ============================================================================
// Custom Node
// ============================================================================

interface ParagraphNodeData {
  label: string;
  paragraphNumber: number | null;
  chapterTitle: string | null;
  gradeLevel: number | null;
  isCrossTextbook: boolean;
  chapterColor: { bg: string; border: string; text: string };
  hasIncoming: boolean;
  hasOutgoing: boolean;
  [key: string]: unknown;
}

function ParagraphNode({ data }: { data: ParagraphNodeData }) {
  return (
    <div
      className="rounded-lg border-2 px-3 py-2 shadow-sm min-w-[160px] max-w-[240px]"
      style={{
        backgroundColor: data.chapterColor.bg,
        borderColor: data.chapterColor.border,
      }}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!w-2 !h-2"
        style={{
          background: data.hasIncoming ? data.chapterColor.border : 'transparent',
          border: data.hasIncoming ? `2px solid ${data.chapterColor.border}` : 'none',
        }}
      />
      <div className="flex items-start gap-2">
        <div className="flex flex-col items-center gap-0.5 shrink-0">
          {data.gradeLevel != null && (
            <span
              className="inline-flex items-center justify-center rounded px-1 py-px text-[9px] font-medium shrink-0"
              style={{
                backgroundColor: data.isCrossTextbook ? '#fef3c7' : data.chapterColor.border + '20',
                color: data.isCrossTextbook ? '#92400e' : data.chapterColor.text,
                border: data.isCrossTextbook ? '1px solid #f59e0b' : 'none',
              }}
            >
              {data.gradeLevel} кл
            </span>
          )}
          {data.paragraphNumber != null && (
            <span
              className="inline-flex items-center justify-center rounded-md px-1.5 py-0.5 text-xs font-bold shrink-0"
              style={{
                backgroundColor: data.chapterColor.border,
                color: '#fff',
              }}
            >
              §{data.paragraphNumber}
            </span>
          )}
        </div>
        <div className="min-w-0">
          <p className="text-xs font-semibold leading-tight truncate" style={{ color: data.chapterColor.text }}>
            {data.label}
          </p>
          {data.chapterTitle && (
            <p className="text-[10px] leading-tight mt-0.5 truncate opacity-70" style={{ color: data.chapterColor.text }}>
              {data.chapterTitle}
            </p>
          )}
        </div>
      </div>
      <Handle
        type="source"
        position={Position.Bottom}
        className="!w-2 !h-2"
        style={{
          background: data.hasOutgoing ? data.chapterColor.border : 'transparent',
          border: data.hasOutgoing ? `2px solid ${data.chapterColor.border}` : 'none',
        }}
      />
    </div>
  );
}

const nodeTypes: NodeTypes = {
  paragraph: ParagraphNode,
};

// ============================================================================
// Dagre layout
// ============================================================================

const NODE_WIDTH = 200;
const NODE_HEIGHT = 60;

function getLayoutedElements(
  nodes: Node[],
  edges: Edge[],
  direction: 'TB' | 'LR' = 'TB'
) {
  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({
    rankdir: direction,
    nodesep: 40,
    ranksep: 80,
    marginx: 20,
    marginy: 20,
  });

  nodes.forEach((node) => {
    g.setNode(node.id, { width: NODE_WIDTH, height: NODE_HEIGHT });
  });

  edges.forEach((edge) => {
    g.setEdge(edge.source, edge.target);
  });

  dagre.layout(g);

  const layoutedNodes = nodes.map((node) => {
    const nodeWithPosition = g.node(node.id);
    return {
      ...node,
      position: {
        x: nodeWithPosition.x - NODE_WIDTH / 2,
        y: nodeWithPosition.y - NODE_HEIGHT / 2,
      },
    };
  });

  return { nodes: layoutedNodes, edges };
}

// ============================================================================
// Main Component
// ============================================================================

interface PrerequisiteGraphProps {
  graphNodes: GraphNode[];
  graphEdges: PrerequisiteEdge[];
}

export function PrerequisiteGraph({
  graphNodes,
  graphEdges,
}: PrerequisiteGraphProps) {
  // Build chapter index map for coloring
  const chapterIndexMap = useMemo(() => {
    const chapters = [...new Set(graphNodes.map((n) => n.chapter_id))];
    const map: Record<number, number> = {};
    chapters.forEach((cid, idx) => {
      map[cid] = idx;
    });
    return map;
  }, [graphNodes]);

  // Determine which nodes have incoming/outgoing edges
  const { nodesWithIncoming, nodesWithOutgoing } = useMemo(() => {
    const incoming = new Set<number>();
    const outgoing = new Set<number>();
    graphEdges.forEach((e) => {
      incoming.add(e.to_paragraph_id);
      outgoing.add(e.from_paragraph_id);
    });
    return { nodesWithIncoming: incoming, nodesWithOutgoing: outgoing };
  }, [graphEdges]);

  // Convert to React Flow format
  const layouted = useMemo(() => {
    const rfNodes: Node[] = graphNodes.map((node) => ({
      id: String(node.id),
      type: 'paragraph',
      position: { x: 0, y: 0 },
      data: {
        label: node.title || `Параграф ${node.id}`,
        paragraphNumber: node.number,
        chapterTitle: node.chapter_title,
        gradeLevel: node.grade_level,
        isCrossTextbook: node.textbook_id != null && node.textbook_id !== graphNodes[0]?.textbook_id,
        chapterColor: getChapterColor(chapterIndexMap[node.chapter_id] ?? 0),
        hasIncoming: nodesWithIncoming.has(node.id),
        hasOutgoing: nodesWithOutgoing.has(node.id),
      } satisfies ParagraphNodeData,
    }));

    const rfEdges: Edge[] = graphEdges.map((edge) => ({
      id: `e-${edge.id}`,
      source: String(edge.from_paragraph_id),
      target: String(edge.to_paragraph_id),
      type: 'default',
      animated: edge.strength === 'recommended',
      style: {
        stroke: edge.strength === 'required' ? '#6366f1' : '#f59e0b',
        strokeWidth: edge.strength === 'required' ? 2 : 1.5,
        strokeDasharray: edge.strength === 'recommended' ? '5 5' : undefined,
      },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: edge.strength === 'required' ? '#6366f1' : '#f59e0b',
        width: 16,
        height: 16,
      },
      label: edge.strength === 'recommended' ? 'рек.' : undefined,
      labelStyle: { fontSize: 10, fill: '#f59e0b' },
    }));

    return getLayoutedElements(rfNodes, rfEdges, 'TB');
  }, [graphNodes, graphEdges, chapterIndexMap, nodesWithIncoming, nodesWithOutgoing]);

  const [nodes, setNodes, onNodesChange] = useNodesState(layouted.nodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(layouted.edges);

  const onLayout = useCallback(
    (direction: 'TB' | 'LR') => {
      const { nodes: layoutedNodes, edges: layoutedEdges } =
        getLayoutedElements(nodes, edges, direction);
      setNodes([...layoutedNodes]);
      setEdges([...layoutedEdges]);
    },
    [nodes, edges, setNodes, setEdges]
  );

  // Legend: unique chapters
  const chapters = useMemo(() => {
    const seen = new Map<number, { title: string; color: ReturnType<typeof getChapterColor> }>();
    graphNodes.forEach((n) => {
      if (!seen.has(n.chapter_id)) {
        seen.set(n.chapter_id, {
          title: n.chapter_title || `Глава ${n.chapter_number ?? '?'}`,
          color: getChapterColor(chapterIndexMap[n.chapter_id] ?? 0),
        });
      }
    });
    return Array.from(seen.values());
  }, [graphNodes, chapterIndexMap]);

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center justify-between gap-4 p-3 border-b bg-muted/30">
        <div className="flex items-center gap-4 flex-wrap">
          {/* Legend */}
          <div className="flex items-center gap-3 flex-wrap">
            {chapters.map((ch, i) => (
              <div key={i} className="flex items-center gap-1.5">
                <span
                  className="w-3 h-3 rounded-sm border"
                  style={{ backgroundColor: ch.color.bg, borderColor: ch.color.border }}
                />
                <span className="text-xs text-muted-foreground truncate max-w-[150px]">
                  {ch.title}
                </span>
              </div>
            ))}
          </div>
          <div className="h-4 w-px bg-border" />
          {/* Edge legend */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5">
              <span className="w-5 h-0.5 bg-indigo-500" />
              <span className="text-xs text-muted-foreground">обязательный</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-5 h-0.5 border-t-2 border-dashed border-amber-500" />
              <span className="text-xs text-muted-foreground">рекомендуемый</span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => onLayout('TB')}
            className="px-2 py-1 text-xs rounded border hover:bg-muted transition-colors"
          >
            Сверху вниз
          </button>
          <button
            onClick={() => onLayout('LR')}
            className="px-2 py-1 text-xs rounded border hover:bg-muted transition-colors"
          >
            Слева направо
          </button>
        </div>
      </div>

      {/* Graph */}
      <div className="flex-1 min-h-0">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes}
          fitView
          fitViewOptions={{ padding: 0.2 }}
          minZoom={0.1}
          maxZoom={2}
          proOptions={{ hideAttribution: true }}
        >
          <Background gap={16} size={1} />
          <Controls showInteractive={false} />
          <MiniMap
            nodeColor={(node) => {
              const data = node.data as ParagraphNodeData;
              return data.chapterColor?.border ?? '#94a3b8';
            }}
            maskColor="rgba(0, 0, 0, 0.1)"
            style={{ height: 100, width: 150 }}
          />
        </ReactFlow>
      </div>
    </div>
  );
}

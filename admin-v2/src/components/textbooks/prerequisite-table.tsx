'use client';

import { useMemo } from 'react';
import { ArrowRight, ArrowLeft, ExternalLink } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

import type { GraphNode, PrerequisiteEdge } from '@/lib/api/prerequisites';

// ============================================================================
// Chapter color palette (same as graph)
// ============================================================================

const CHAPTER_COLORS = [
  { bg: '#dbeafe', border: '#3b82f6', text: '#1e40af', light: '#eff6ff' },
  { bg: '#dcfce7', border: '#22c55e', text: '#166534', light: '#f0fdf4' },
  { bg: '#fef3c7', border: '#f59e0b', text: '#92400e', light: '#fffbeb' },
  { bg: '#fce7f3', border: '#ec4899', text: '#9d174d', light: '#fdf2f8' },
  { bg: '#e0e7ff', border: '#6366f1', text: '#3730a3', light: '#eef2ff' },
  { bg: '#f3e8ff', border: '#a855f7', text: '#6b21a8', light: '#faf5ff' },
  { bg: '#ccfbf1', border: '#14b8a6', text: '#115e59', light: '#f0fdfa' },
  { bg: '#fee2e2', border: '#ef4444', text: '#991b1b', light: '#fef2f2' },
  { bg: '#fef9c3', border: '#eab308', text: '#854d0e', light: '#fefce8' },
  { bg: '#e0f2fe', border: '#0ea5e9', text: '#075985', light: '#f0f9ff' },
];

function getChapterColor(chapterIndex: number) {
  return CHAPTER_COLORS[chapterIndex % CHAPTER_COLORS.length];
}

// ============================================================================
// Types
// ============================================================================

interface ChapterGroup {
  chapterId: number;
  chapterTitle: string;
  chapterNumber: number | null;
  colorIndex: number;
  paragraphs: ParagraphRow[];
}

interface ParagraphRow {
  node: GraphNode;
  prerequisites: { node: GraphNode; strength: string }[];
  dependents: { node: GraphNode; strength: string }[];
  isCrossTextbook: boolean;
}

// ============================================================================
// Component
// ============================================================================

interface PrerequisiteTableProps {
  graphNodes: GraphNode[];
  graphEdges: PrerequisiteEdge[];
  currentTextbookId: number;
}

export function PrerequisiteTable({
  graphNodes,
  graphEdges,
  currentTextbookId,
}: PrerequisiteTableProps) {
  const { chapters, stats } = useMemo(() => {
    const nodeMap = new Map<number, GraphNode>();
    graphNodes.forEach((n) => nodeMap.set(n.id, n));

    // Build adjacency
    const prereqsOf = new Map<number, { node: GraphNode; strength: string }[]>();
    const depsOf = new Map<number, { node: GraphNode; strength: string }[]>();

    graphEdges.forEach((e) => {
      const fromNode = nodeMap.get(e.from_paragraph_id);
      const toNode = nodeMap.get(e.to_paragraph_id);
      if (!fromNode || !toNode) return;

      if (!prereqsOf.has(e.to_paragraph_id)) prereqsOf.set(e.to_paragraph_id, []);
      prereqsOf.get(e.to_paragraph_id)!.push({ node: fromNode, strength: e.strength });

      if (!depsOf.has(e.from_paragraph_id)) depsOf.set(e.from_paragraph_id, []);
      depsOf.get(e.from_paragraph_id)!.push({ node: toNode, strength: e.strength });
    });

    // Group by chapter
    const chapterMap = new Map<number, ChapterGroup>();
    const chapterOrder: number[] = [];
    let chapterIdx = 0;

    graphNodes.forEach((node) => {
      if (!chapterMap.has(node.chapter_id)) {
        chapterMap.set(node.chapter_id, {
          chapterId: node.chapter_id,
          chapterTitle: node.chapter_title || `Глава ${node.chapter_number ?? '?'}`,
          chapterNumber: node.chapter_number,
          colorIndex: chapterIdx++,
          paragraphs: [],
        });
        chapterOrder.push(node.chapter_id);
      }

      const isCross = node.textbook_id != null && node.textbook_id !== currentTextbookId;

      chapterMap.get(node.chapter_id)!.paragraphs.push({
        node,
        prerequisites: prereqsOf.get(node.id) || [],
        dependents: depsOf.get(node.id) || [],
        isCrossTextbook: isCross,
      });
    });

    const chaptersArr = chapterOrder.map((id) => chapterMap.get(id)!);

    // Stats
    const nodesWithPrereqs = new Set<number>();
    const nodesWithDeps = new Set<number>();
    graphEdges.forEach((e) => {
      nodesWithPrereqs.add(e.to_paragraph_id);
      nodesWithDeps.add(e.from_paragraph_id);
    });
    const isolated = graphNodes.filter(
      (n) => !nodesWithPrereqs.has(n.id) && !nodesWithDeps.has(n.id)
    ).length;

    return {
      chapters: chaptersArr,
      stats: {
        totalNodes: graphNodes.length,
        totalEdges: graphEdges.length,
        required: graphEdges.filter((e) => e.strength === 'required').length,
        recommended: graphEdges.filter((e) => e.strength === 'recommended').length,
        isolated,
      },
    };
  }, [graphNodes, graphEdges, currentTextbookId]);

  return (
    <div className="space-y-4 p-4 overflow-auto max-h-[700px]">
      {/* Stats bar */}
      <div className="flex items-center gap-3 flex-wrap text-sm">
        <div className="flex items-center gap-1.5">
          <span className="font-medium text-muted-foreground">Параграфов:</span>
          <Badge variant="secondary">{stats.totalNodes}</Badge>
        </div>
        <div className="h-4 w-px bg-border" />
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-0.5 bg-indigo-500 inline-block" />
          <span className="text-muted-foreground">Обязательных:</span>
          <Badge variant="secondary">{stats.required}</Badge>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-0.5 border-t-2 border-dashed border-amber-500 inline-block" />
          <span className="text-muted-foreground">Рекомендуемых:</span>
          <Badge variant="secondary">{stats.recommended}</Badge>
        </div>
        {stats.isolated > 0 && (
          <>
            <div className="h-4 w-px bg-border" />
            <div className="flex items-center gap-1.5">
              <span className="text-muted-foreground">Без связей:</span>
              <Badge variant="outline">{stats.isolated}</Badge>
            </div>
          </>
        )}
      </div>

      {/* Chapters */}
      {chapters.map((chapter) => {
        const color = getChapterColor(chapter.colorIndex);

        return (
          <div key={chapter.chapterId} className="rounded-lg border overflow-hidden">
            {/* Chapter header */}
            <div
              className="px-4 py-2.5 flex items-center gap-3"
              style={{ backgroundColor: color.bg, borderBottom: `2px solid ${color.border}` }}
            >
              <span
                className="inline-flex items-center justify-center rounded-md px-2 py-0.5 text-xs font-bold"
                style={{ backgroundColor: color.border, color: '#fff' }}
              >
                Гл. {chapter.chapterNumber ?? '?'}
              </span>
              <span className="font-semibold text-sm" style={{ color: color.text }}>
                {chapter.chapterTitle}
              </span>
              <Badge variant="outline" className="ml-auto text-[10px]">
                {chapter.paragraphs.length} §
              </Badge>
            </div>

            {/* Paragraph rows */}
            <div className="divide-y">
              {chapter.paragraphs.map((row) => (
                <ParagraphRowComponent key={row.node.id} row={row} color={color} chapters={chapters} />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ============================================================================
// Paragraph Row
// ============================================================================

function ParagraphRowComponent({
  row,
  color,
  chapters,
}: {
  row: ParagraphRow;
  color: (typeof CHAPTER_COLORS)[0];
  chapters: ChapterGroup[];
}) {
  const hasConnections = row.prerequisites.length > 0 || row.dependents.length > 0;

  return (
    <div
      className="px-4 py-2.5 hover:bg-muted/30 transition-colors"
      style={{ backgroundColor: row.isCrossTextbook ? '#fffbeb' : undefined }}
    >
      {/* Main paragraph info */}
      <div className="flex items-center gap-2">
        {/* Grade badge */}
        {row.node.grade_level != null && (
          <span
            className="inline-flex items-center justify-center rounded px-1.5 py-0.5 text-[10px] font-semibold shrink-0"
            style={
              row.isCrossTextbook
                ? { backgroundColor: '#fef3c7', color: '#92400e', border: '1px solid #f59e0b' }
                : { backgroundColor: color.border + '18', color: color.text }
            }
          >
            {row.node.grade_level} кл
          </span>
        )}
        {/* § number */}
        {row.node.number != null && (
          <span
            className="inline-flex items-center justify-center rounded-md px-1.5 py-0.5 text-xs font-bold shrink-0"
            style={{ backgroundColor: color.border, color: '#fff' }}
          >
            §{row.node.number}
          </span>
        )}
        {/* Title */}
        <span className="text-sm font-medium truncate">
          {row.node.title || `Параграф ${row.node.id}`}
        </span>
        {/* Cross-textbook badge */}
        {row.isCrossTextbook && row.node.textbook_title && (
          <Badge variant="outline" className="text-[10px] shrink-0 gap-1 text-amber-700 border-amber-300">
            <ExternalLink className="h-2.5 w-2.5" />
            {row.node.textbook_title}
          </Badge>
        )}
        {/* Connection count */}
        {hasConnections && (
          <div className="ml-auto flex items-center gap-2 shrink-0">
            {row.prerequisites.length > 0 && (
              <span className="text-[10px] text-muted-foreground flex items-center gap-0.5">
                <ArrowLeft className="h-3 w-3" />
                {row.prerequisites.length}
              </span>
            )}
            {row.dependents.length > 0 && (
              <span className="text-[10px] text-muted-foreground flex items-center gap-0.5">
                <ArrowRight className="h-3 w-3" />
                {row.dependents.length}
              </span>
            )}
          </div>
        )}
      </div>

      {/* Dependencies detail */}
      {hasConnections && (
        <div className="mt-2 flex gap-6 flex-wrap">
          {/* Prerequisites (incoming) */}
          {row.prerequisites.length > 0 && (
            <div className="space-y-1">
              <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wide">
                Требует знания:
              </p>
              <div className="flex flex-wrap gap-1.5">
                {row.prerequisites.map((p) => (
                  <DependencyChip
                    key={p.node.id}
                    node={p.node}
                    strength={p.strength}
                    direction="prereq"
                    chapters={chapters}
                  />
                ))}
              </div>
            </div>
          )}
          {/* Dependents (outgoing) */}
          {row.dependents.length > 0 && (
            <div className="space-y-1">
              <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wide">
                Необходим для:
              </p>
              <div className="flex flex-wrap gap-1.5">
                {row.dependents.map((d) => (
                  <DependencyChip
                    key={d.node.id}
                    node={d.node}
                    strength={d.strength}
                    direction="dep"
                    chapters={chapters}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Dependency Chip
// ============================================================================

function DependencyChip({
  node,
  strength,
  direction,
  chapters,
}: {
  node: GraphNode;
  strength: string;
  direction: 'prereq' | 'dep';
  chapters: ChapterGroup[];
}) {
  const chapterGroup = chapters.find((c) => c.chapterId === node.chapter_id);
  const color = chapterGroup ? getChapterColor(chapterGroup.colorIndex) : CHAPTER_COLORS[0];
  const isRequired = strength === 'required';

  return (
    <div
      className="inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-xs border"
      style={{
        backgroundColor: color.light,
        borderColor: isRequired ? color.border : '#f59e0b',
        borderStyle: isRequired ? 'solid' : 'dashed',
      }}
    >
      {direction === 'prereq' ? (
        <ArrowLeft className="h-3 w-3 shrink-0" style={{ color: isRequired ? '#6366f1' : '#f59e0b' }} />
      ) : (
        <ArrowRight className="h-3 w-3 shrink-0" style={{ color: isRequired ? '#6366f1' : '#f59e0b' }} />
      )}
      {node.grade_level != null && (
        <span className="font-medium text-[10px]" style={{ color: color.text }}>
          {node.grade_level}кл
        </span>
      )}
      {node.number != null && (
        <span className="font-bold" style={{ color: color.text }}>
          §{node.number}
        </span>
      )}
      <span className="truncate max-w-[120px]" style={{ color: color.text }}>
        {node.title || `П.${node.id}`}
      </span>
    </div>
  );
}

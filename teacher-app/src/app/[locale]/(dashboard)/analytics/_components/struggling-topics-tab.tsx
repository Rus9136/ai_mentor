'use client';

import { useMemo } from 'react';
import { useTranslations } from 'next-intl';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { AlertTriangle, BarChart3, ChevronDown, ChevronRight } from 'lucide-react';
import { useState } from 'react';
import type { StrugglingTopicResponse } from '@/lib/api/teachers';

interface StrugglingTopicsTabProps {
  data?: StrugglingTopicResponse[];
}

interface GroupedTopics {
  chapterTitle: string;
  chapterId: number;
  textbookTitle?: string;
  topics: StrugglingTopicResponse[];
}

export function StrugglingTopicsTab({ data }: StrugglingTopicsTabProps) {
  const t = useTranslations('analytics');
  const [expandedChapters, setExpandedChapters] = useState<Set<number>>(new Set());

  // Group topics by chapter
  const grouped = useMemo<GroupedTopics[]>(() => {
    if (!data?.length) return [];

    const map = new Map<number, GroupedTopics>();
    for (const topic of data) {
      if (!map.has(topic.chapter_id)) {
        map.set(topic.chapter_id, {
          chapterTitle: topic.chapter_title,
          chapterId: topic.chapter_id,
          textbookTitle: topic.textbook_title,
          topics: [],
        });
      }
      map.get(topic.chapter_id)!.topics.push(topic);
    }

    // Sort chapters by total struggling count
    return Array.from(map.values()).sort(
      (a, b) =>
        b.topics.reduce((s, t) => s + t.struggling_count, 0) -
        a.topics.reduce((s, t) => s + t.struggling_count, 0)
    );
  }, [data]);

  // Initially expand all chapters
  const isExpanded = (chapterId: number) => {
    // If nothing explicitly toggled, show all expanded
    if (expandedChapters.size === 0 && grouped.length > 0) return true;
    return expandedChapters.has(chapterId);
  };

  const toggleChapter = (chapterId: number) => {
    setExpandedChapters((prev) => {
      const next = new Set(prev);
      // On first toggle, initialize with all chapters
      if (prev.size === 0) {
        grouped.forEach((g) => next.add(g.chapterId));
      }
      if (next.has(chapterId)) {
        next.delete(chapterId);
      } else {
        next.add(chapterId);
      }
      return next;
    });
  };

  if (!data || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-warning" />
            {t('strugglingTopics')}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="py-12 text-center">
            <BarChart3 className="mx-auto mb-4 h-12 w-12 text-muted-foreground/50" />
            <p className="text-muted-foreground">{t('noStrugglingTopics')}</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 text-warning" />
          {t('strugglingTopics')}
        </CardTitle>
        <CardDescription>{t('strugglingDescription')}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {grouped.map((group) => {
          const chapterStrugglingTotal = group.topics.reduce((s, t) => s + t.struggling_count, 0);
          const expanded = isExpanded(group.chapterId);

          return (
            <div key={group.chapterId} className="rounded-lg border">
              {/* Chapter header */}
              <button
                onClick={() => toggleChapter(group.chapterId)}
                className="flex w-full items-center justify-between p-3 text-left hover:bg-muted/50"
              >
                <div className="flex items-center gap-2">
                  {expanded ? (
                    <ChevronDown className="h-4 w-4 text-muted-foreground" />
                  ) : (
                    <ChevronRight className="h-4 w-4 text-muted-foreground" />
                  )}
                  <div>
                    <p className="font-medium text-sm">{group.chapterTitle}</p>
                    {group.textbookTitle && (
                      <p className="text-xs text-muted-foreground">{group.textbookTitle}</p>
                    )}
                  </div>
                </div>
                <span className="rounded-full bg-destructive/10 px-2.5 py-0.5 text-xs font-semibold text-destructive">
                  {chapterStrugglingTotal} {t('studentsStruggling')}
                </span>
              </button>

              {/* Paragraphs inside chapter */}
              {expanded && (
                <div className="border-t px-3 pb-3">
                  {group.topics.map((topic) => (
                    <div
                      key={topic.paragraph_id}
                      className="mt-3 rounded-lg border border-destructive/20 bg-destructive/5 p-3"
                    >
                      <div className="flex items-start justify-between">
                        <p className="text-sm font-medium text-foreground">
                          {topic.paragraph_title}
                        </p>
                        <p className="ml-2 shrink-0 text-lg font-bold text-destructive">
                          {topic.struggling_count}
                        </p>
                      </div>

                      <div className="mt-2 flex items-center gap-4">
                        <div className="flex-1">
                          <div className="flex items-center justify-between text-xs text-muted-foreground">
                            <span>
                              {t('percentStruggling', { pct: Math.round(topic.struggling_percentage) })}
                            </span>
                            <span>
                              {t('avgScore', { score: Math.round(topic.average_score) })}
                            </span>
                          </div>
                          <Progress
                            value={topic.struggling_percentage}
                            className="mt-1.5 h-1.5"
                            indicatorClassName="bg-destructive"
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}

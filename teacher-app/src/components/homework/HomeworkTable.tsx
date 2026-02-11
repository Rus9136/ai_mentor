'use client';

import { useTranslations } from 'next-intl';
import Link from 'next/link';
import { useLocale } from 'next-intl';
import { Calendar, Users, Sparkles } from 'lucide-react';
import { HomeworkStatusBadge } from './HomeworkStatusBadge';
import type { HomeworkListResponse } from '@/types/homework';

interface HomeworkTableProps {
  homework: HomeworkListResponse[];
}

export function HomeworkTable({ homework }: HomeworkTableProps) {
  const t = useTranslations('homework');
  const locale = useLocale();

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString(locale === 'kz' ? 'kk-KZ' : 'ru-RU', {
      day: 'numeric',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const isOverdue = (dateStr: string, status: string) => {
    return new Date(dateStr) < new Date() && status === 'published';
  };

  return (
    <div className="border rounded-lg overflow-hidden">
      <table className="w-full">
        <thead className="bg-muted/50">
          <tr>
            <th className="text-left px-4 py-3 text-sm font-medium text-muted-foreground">
              {t('table.title')}
            </th>
            <th className="text-left px-4 py-3 text-sm font-medium text-muted-foreground hidden md:table-cell">
              {t('table.class')}
            </th>
            <th className="text-left px-4 py-3 text-sm font-medium text-muted-foreground">
              {t('table.status')}
            </th>
            <th className="text-left px-4 py-3 text-sm font-medium text-muted-foreground hidden sm:table-cell">
              {t('table.dueDate')}
            </th>
            <th className="text-left px-4 py-3 text-sm font-medium text-muted-foreground hidden lg:table-cell">
              {t('table.progress')}
            </th>
            <th className="text-left px-4 py-3 text-sm font-medium text-muted-foreground w-12">
              {/* AI column */}
            </th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {homework.map((hw) => (
            <tr
              key={hw.id}
              className="hover:bg-muted/30 transition-colors"
            >
              {/* Title */}
              <td className="px-4 py-3">
                <Link
                  href={`/${locale}/homework/${hw.id}`}
                  className="font-medium text-primary hover:underline line-clamp-1"
                >
                  {hw.title}
                </Link>
                {/* Mobile: show class under title */}
                {hw.class_name && (
                  <p className="text-sm text-muted-foreground md:hidden mt-0.5">
                    {hw.class_name}
                  </p>
                )}
              </td>

              {/* Class - hidden on mobile */}
              <td className="px-4 py-3 hidden md:table-cell">
                <span className="text-sm">{hw.class_name || '—'}</span>
              </td>

              {/* Status */}
              <td className="px-4 py-3">
                <HomeworkStatusBadge status={hw.status} />
              </td>

              {/* Due date - hidden on xs */}
              <td className="px-4 py-3 hidden sm:table-cell">
                <div
                  className={`flex items-center gap-1.5 text-sm ${
                    isOverdue(hw.due_date, hw.status)
                      ? 'text-destructive'
                      : 'text-muted-foreground'
                  }`}
                >
                  <Calendar className="h-3.5 w-3.5" />
                  <span>{formatDate(hw.due_date)}</span>
                </div>
              </td>

              {/* Progress - hidden on md and smaller */}
              <td className="px-4 py-3 hidden lg:table-cell">
                <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
                  <Users className="h-3.5 w-3.5" />
                  <span>
                    {hw.submitted_count}/{hw.total_students}
                  </span>
                </div>
              </td>

              {/* AI indicator */}
              <td className="px-4 py-3">
                {hw.ai_generation_enabled && (
                  <span title={t('card.aiEnabled')}>
                    <Sparkles className="h-4 w-4 text-primary" />
                  </span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

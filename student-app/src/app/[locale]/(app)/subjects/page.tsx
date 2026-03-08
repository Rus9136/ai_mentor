'use client';

import { useMemo } from 'react';
import { useTranslations } from 'next-intl';
import { useTextbooks } from '@/lib/hooks/use-textbooks';
import { useStudentProfile } from '@/lib/hooks/use-profile';
import { TextbookSection } from '@/components/textbooks/TextbookSection';
import { BookOpen, Loader2, AlertCircle, Star } from 'lucide-react';

export default function SubjectsPage() {
  const t = useTranslations('home');
  const tCommon = useTranslations('common');
  const tTextbook = useTranslations('textbook');
  const { data: textbooks, isLoading, error, refetch } = useTextbooks();
  const { data: profile } = useStudentProfile();

  const { myTextbooks, otherGroups } = useMemo(() => {
    if (!textbooks) return { myTextbooks: [], otherGroups: [] };

    const gradeLevel = profile?.grade_level;
    const my = gradeLevel
      ? textbooks.filter((tb) => tb.grade_level === gradeLevel)
      : [];
    const other = textbooks.filter(
      (tb) => !gradeLevel || tb.grade_level !== gradeLevel
    );

    // Group other textbooks by grade_level
    const grouped = new Map<number, typeof other>();
    for (const tb of other) {
      const grade = tb.grade_level;
      if (!grouped.has(grade)) grouped.set(grade, []);
      grouped.get(grade)!.push(tb);
    }

    // Sort by grade
    const sortedGroups = Array.from(grouped.entries())
      .sort(([a], [b]) => a - b)
      .map(([grade, tbs]) => ({ grade, textbooks: tbs }));

    return { myTextbooks: my, otherGroups: sortedGroups };
  }, [textbooks, profile]);

  // Loading State
  if (isLoading) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-6 md:py-8">
        <h1 className="mb-6 text-2xl font-bold text-foreground">{t('subjects.title')}</h1>
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <span className="ml-2 text-muted-foreground">{tCommon('loading')}</span>
        </div>
      </div>
    );
  }

  // Error State
  if (error) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-6 md:py-8">
        <h1 className="mb-6 text-2xl font-bold text-foreground">{t('subjects.title')}</h1>
        <div className="card-flat p-6 text-center">
          <AlertCircle className="mx-auto h-10 w-10 text-destructive" />
          <p className="mt-2 text-sm text-muted-foreground">{tTextbook('errorLoading')}</p>
          <button
            onClick={() => refetch()}
            className="mt-4 rounded-full bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90"
          >
            {tCommon('retry')}
          </button>
        </div>
      </div>
    );
  }

  // Empty State
  if (!textbooks || textbooks.length === 0) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-6 md:py-8">
        <h1 className="mb-6 text-2xl font-bold text-foreground">{t('subjects.title')}</h1>
        <div className="card-flat p-8 text-center">
          <BookOpen className="mx-auto h-12 w-12 text-muted-foreground/50" />
          <p className="mt-4 text-muted-foreground">{tTextbook('noTextbooks')}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-6 md:py-8">
      <h1 className="mb-6 text-2xl font-bold text-foreground">{t('subjects.title')}</h1>

      {/* My textbooks (matching student grade) */}
      {myTextbooks.length > 0 && (
        <TextbookSection
          title={profile ? `${tTextbook('myTextbooks')} (${profile.grade_level} ${tTextbook('grade')})` : tTextbook('myTextbooks')}
          textbooks={myTextbooks}
          defaultOpen={true}
          icon={<Star className="h-5 w-5 text-primary" />}
        />
      )}

      {/* Other textbooks grouped by grade */}
      {otherGroups.length > 0 && otherGroups.map(({ grade, textbooks: tbs }) => (
        <TextbookSection
          key={grade}
          title={`${grade} ${tTextbook('grade')}`}
          textbooks={tbs}
          defaultOpen={myTextbooks.length === 0}
        />
      ))}
    </div>
  );
}

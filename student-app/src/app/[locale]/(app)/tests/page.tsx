'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { ClipboardList, Loader2, RefreshCw } from 'lucide-react';
import { useAllStudentTests, testKeys } from '@/lib/hooks/use-tests';
import { TestPurpose, AvailableTest } from '@/lib/api/tests';
import { TestCard } from '@/components/tests';
import { TestQuizModal } from '@/components/tests/TestQuizModal';
import { cn } from '@/lib/utils';
import { useQueryClient } from '@tanstack/react-query';

type FilterTab = 'all' | 'diagnostic' | 'summative' | 'practice';

const tabToPurpose: Record<FilterTab, TestPurpose | undefined> = {
  all: undefined,
  diagnostic: 'diagnostic',
  summative: 'summative',
  practice: 'practice',
};

export default function TestsPage() {
  const t = useTranslations('tests');
  const [activeTab, setActiveTab] = useState<FilterTab>('all');
  const [selectedTest, setSelectedTest] = useState<AvailableTest | null>(null);
  const queryClient = useQueryClient();

  const { data: tests, isLoading, error, refetch } = useAllStudentTests(tabToPurpose[activeTab]);

  const handleStartTest = (test: AvailableTest) => {
    setSelectedTest(test);
  };

  const handleCloseQuiz = () => {
    setSelectedTest(null);
    // Invalidate tests query to refresh results
    queryClient.invalidateQueries({ queryKey: testKeys.all });
  };

  const handleTestCompleted = (passed: boolean, score: number) => {
    // Invalidate tests query to refresh results
    queryClient.invalidateQueries({ queryKey: testKeys.all });
  };

  // Sort tests: not completed first, then by last attempt date
  const sortedTests = tests?.sort((a, b) => {
    // Tests without attempts first
    if (a.attempts_count === 0 && b.attempts_count > 0) return -1;
    if (a.attempts_count > 0 && b.attempts_count === 0) return 1;

    // Then by latest attempt date (most recent first)
    if (a.latest_attempt_date && b.latest_attempt_date) {
      return new Date(b.latest_attempt_date).getTime() - new Date(a.latest_attempt_date).getTime();
    }

    return 0;
  });

  return (
    <div className="mx-auto max-w-4xl px-4 py-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">{t('title')}</h1>
      </div>

      {/* Tabs */}
      <div className="flex flex-wrap gap-2 mb-6">
        {(['all', 'diagnostic', 'summative', 'practice'] as FilterTab[]).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={cn(
              'px-4 py-2 rounded-full text-sm font-medium transition-colors',
              activeTab === tab
                ? 'bg-primary text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            )}
          >
            {t(`tabs.${tab}`)}
          </button>
        ))}
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="flex flex-col items-center justify-center h-64">
          <Loader2 className="w-8 h-8 text-primary animate-spin mb-4" />
          <p className="text-gray-500">{t('loading')}</p>
        </div>
      ) : error ? (
        <div className="flex flex-col items-center justify-center h-64 text-center">
          <p className="text-red-500 mb-4">{t('error')}</p>
          <button
            onClick={() => refetch()}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium bg-primary text-white hover:bg-primary/90 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            {t('retry')}
          </button>
        </div>
      ) : sortedTests?.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-64 text-center">
          <div className="w-16 h-16 rounded-full bg-gray-100 flex items-center justify-center mb-4">
            <ClipboardList className="w-8 h-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-1">{t('empty.title')}</h3>
          <p className="text-gray-500">{t('empty.description')}</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {sortedTests?.map((test) => (
            <TestCard
              key={test.id}
              test={test}
              onStart={() => handleStartTest(test)}
            />
          ))}
        </div>
      )}

      {/* Quiz Modal */}
      {selectedTest && (
        <TestQuizModal
          isOpen={!!selectedTest}
          onClose={handleCloseQuiz}
          test={selectedTest}
          paragraphId={selectedTest.paragraph_id || undefined}
          onCompleted={handleTestCompleted}
        />
      )}
    </div>
  );
}

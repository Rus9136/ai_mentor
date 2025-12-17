'use client';

import { useState, useMemo } from 'react';
import { useSearchParams } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { Target, Search, Filter, BookOpen } from 'lucide-react';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { RoleGuard } from '@/components/auth';
import { useOutcomes, useFrameworks, useSubjects } from '@/lib/hooks/use-goso';
import type { LearningOutcome } from '@/types';

const GRADES = [5, 6, 7, 8, 9, 10, 11];

export default function OutcomesPage() {
  const t = useTranslations('nav');
  const searchParams = useSearchParams();

  const initialSubsectionId = searchParams.get('subsection_id');

  const [search, setSearch] = useState('');
  const [selectedGrade, setSelectedGrade] = useState<string>('all');
  const [selectedFramework, setSelectedFramework] = useState<string>('all');

  const { data: frameworks = [] } = useFrameworks();
  const { data: subjects = [] } = useSubjects();

  const queryParams = useMemo(() => {
    const params: {
      framework_id?: number;
      subsection_id?: number;
      grade?: number;
      search?: string;
    } = {};

    if (selectedFramework && selectedFramework !== 'all') {
      params.framework_id = Number(selectedFramework);
    }
    if (initialSubsectionId) {
      params.subsection_id = Number(initialSubsectionId);
    }
    if (selectedGrade && selectedGrade !== 'all') {
      params.grade = Number(selectedGrade);
    }
    if (search.length >= 3) {
      params.search = search;
    }

    return params;
  }, [selectedFramework, selectedGrade, search, initialSubsectionId]);

  const { data: outcomes = [], isLoading } = useOutcomes(queryParams);

  const getSubjectName = (subjectId: number) => {
    const subject = subjects.find((s) => s.id === subjectId);
    return subject?.name_ru || '';
  };

  const getFrameworkForOutcome = (outcome: LearningOutcome) => {
    return frameworks.find((f) => f.id === outcome.framework_id);
  };

  // Group outcomes by grade
  const groupedOutcomes = useMemo(() => {
    const groups: Record<number, LearningOutcome[]> = {};
    outcomes.forEach((outcome) => {
      if (!groups[outcome.grade]) {
        groups[outcome.grade] = [];
      }
      groups[outcome.grade].push(outcome);
    });
    return groups;
  }, [outcomes]);

  const sortedGrades = Object.keys(groupedOutcomes)
    .map(Number)
    .sort((a, b) => a - b);

  return (
    <RoleGuard allowedRoles={['super_admin']}>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{t('learningOutcomes')}</h1>
          <p className="text-muted-foreground">
            Цели обучения по ГОСО стандартам
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Filter className="h-5 w-5" />
              Фильтры
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-4">
              <div className="md:col-span-2">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Поиск по названию (мин. 3 символа)..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>

              <Select value={selectedFramework} onValueChange={setSelectedFramework}>
                <SelectTrigger>
                  <SelectValue placeholder="Все стандарты" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Все стандарты</SelectItem>
                  {frameworks.map((framework) => (
                    <SelectItem key={framework.id} value={String(framework.id)}>
                      {framework.title_ru}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={selectedGrade} onValueChange={setSelectedGrade}>
                <SelectTrigger>
                  <SelectValue placeholder="Все классы" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Все классы</SelectItem>
                  {GRADES.map((grade) => (
                    <SelectItem key={grade} value={String(grade)}>
                      {grade} класс
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {isLoading ? (
          <div className="space-y-4">
            <Skeleton className="h-32" />
            <Skeleton className="h-32" />
            <Skeleton className="h-32" />
          </div>
        ) : outcomes.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-muted mb-4">
                <Target className="h-8 w-8 text-muted-foreground" />
              </div>
              <h3 className="text-lg font-semibold mb-2">Ничего не найдено</h3>
              <p className="text-muted-foreground text-center">
                Попробуйте изменить параметры фильтра
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <p className="text-muted-foreground">
                Найдено: {outcomes.length} целей обучения
              </p>
            </div>

            {sortedGrades.map((grade) => (
              <Card key={grade}>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Badge variant="default">{grade} класс</Badge>
                    <span className="text-muted-foreground font-normal text-sm">
                      {groupedOutcomes[grade].length} целей
                    </span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {groupedOutcomes[grade]
                      .sort((a, b) => a.display_order - b.display_order)
                      .map((outcome) => {
                        const framework = getFrameworkForOutcome(outcome);
                        return (
                          <div
                            key={outcome.id}
                            className="p-4 rounded-lg border bg-card hover:bg-muted/30 transition-colors"
                          >
                            <div className="flex items-start gap-3">
                              <div className="flex-1">
                                <div className="flex items-center gap-2 mb-2 flex-wrap">
                                  <Badge variant="outline">{outcome.code}</Badge>
                                  {outcome.section_code && (
                                    <Badge variant="secondary" className="text-xs">
                                      {outcome.section_code}
                                    </Badge>
                                  )}
                                  {outcome.subsection_code && (
                                    <Badge variant="secondary" className="text-xs">
                                      {outcome.subsection_code}
                                    </Badge>
                                  )}
                                  {outcome.cognitive_level && (
                                    <Badge variant="outline" className="text-xs">
                                      {outcome.cognitive_level}
                                    </Badge>
                                  )}
                                </div>
                                <p className="text-sm">{outcome.title_ru}</p>
                                {outcome.description_ru && (
                                  <p className="text-xs text-muted-foreground mt-1">
                                    {outcome.description_ru}
                                  </p>
                                )}
                                <div className="flex items-center gap-2 mt-2 text-xs text-muted-foreground">
                                  {framework && (
                                    <span className="flex items-center gap-1">
                                      <BookOpen className="h-3 w-3" />
                                      {getSubjectName(framework.subject_id)}
                                    </span>
                                  )}
                                  {outcome.section_name_ru && (
                                    <span>• {outcome.section_name_ru}</span>
                                  )}
                                </div>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </RoleGuard>
  );
}

'use client';

import { useState, useCallback } from 'react';
import { useRouter } from '@/i18n/routing';
import { Loader2, Presentation, RefreshCw, Save, Play, FileDown, Download } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { ContentSelector, ContentSelection } from '@/components/homework/ContentSelector';
import { SlidePreview } from '@/components/presentation/SlidePreview';
import { getTheme, THEMES } from '@/components/presentation/slide-themes';
import { useGeneratePresentation, useSavePresentation } from '@/lib/hooks/use-presentations';
import { exportPresentationPptx } from '@/lib/api/presentations';
import type { PresentationGenerateResponse, SlideThemeName } from '@/types/presentation';

export default function PresentationCreatePage() {
  const [selection, setSelection] = useState<ContentSelection>({});
  const [language, setLanguage] = useState<string>('kk');
  const [slideCount, setSlideCount] = useState<string>('10');
  const [themeName, setThemeName] = useState<SlideThemeName>('warm');
  const [result, setResult] = useState<PresentationGenerateResponse | null>(null);
  const [savedId, setSavedId] = useState<number | null>(null);

  const router = useRouter();
  const mutation = useGeneratePresentation();
  const saveMutation = useSavePresentation();
  const theme = getTheme(themeName);

  const handleSelect = useCallback((sel: ContentSelection) => {
    setSelection(sel);
  }, []);

  const handleGenerate = () => {
    if (!selection.paragraphId) return;
    setSavedId(null);
    mutation.mutate(
      {
        paragraph_id: selection.paragraphId,
        language,
        slide_count: Number(slideCount),
      },
      {
        onSuccess: (data) => setResult(data),
      }
    );
  };

  const canGenerate = !!selection.paragraphId && !mutation.isPending;

  const handleSave = () => {
    if (!result || !selection.paragraphId) return;
    saveMutation.mutate(
      {
        paragraph_id: selection.paragraphId,
        language,
        slide_count: Number(slideCount),
        slides_data: result.presentation as unknown as Record<string, unknown>,
        context_data: { ...result.context, theme: themeName } as unknown as Record<string, unknown>,
      },
      {
        onSuccess: (data) => setSavedId(data.id),
      }
    );
  };

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Создание презентации</h1>
        <p className="text-sm text-muted-foreground">
          AI-генерация презентации из параграфа учебника
        </p>
      </div>

      <Card>
        <CardHeader className="pb-4">
          <CardTitle className="flex items-center gap-2 text-base">
            <Presentation className="h-5 w-5" />
            Параметры
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <ContentSelector onSelect={handleSelect} disabled={mutation.isPending} />

          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label>Язык</Label>
              <Select value={language} onValueChange={setLanguage} disabled={mutation.isPending}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="kk">Қазақша</SelectItem>
                  <SelectItem value="ru">Русский</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Слайдов</Label>
              <Select value={slideCount} onValueChange={setSlideCount} disabled={mutation.isPending}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="5">5</SelectItem>
                  <SelectItem value="10">10</SelectItem>
                  <SelectItem value="15">15</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Стиль оформления</Label>
              <Select value={themeName} onValueChange={(v) => setThemeName(v as SlideThemeName)}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {Object.values(THEMES).map((t) => (
                    <SelectItem key={t.name} value={t.name}>{t.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <Button onClick={handleGenerate} disabled={!canGenerate} className="w-full" size="lg">
            {mutation.isPending ? (
              <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Генерация...</>
            ) : result ? (
              <><RefreshCw className="mr-2 h-4 w-4" />Пересоздать</>
            ) : (
              'Создать презентацию'
            )}
          </Button>

          {mutation.isError && (
            <p className="text-sm text-destructive">Ошибка генерации. Попробуйте ещё раз.</p>
          )}
        </CardContent>
      </Card>

      {result && (
        <>
          <div className="flex gap-3 items-center flex-wrap">
            {!savedId ? (
              <Button onClick={handleSave} disabled={saveMutation.isPending}>
                {saveMutation.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
                Сохранить
              </Button>
            ) : (
              <>
                <Button onClick={() => router.push(`/presentations/${savedId}/view`)}>
                  <Play className="mr-2 h-4 w-4" />
                  Начать показ
                </Button>
                <Button variant="outline" onClick={() => router.push(`/presentations/${savedId}/view?print=true`)}>
                  <FileDown className="mr-2 h-4 w-4" />
                  PDF
                </Button>
                <Button variant="outline" onClick={() => exportPresentationPptx(savedId, themeName)}>
                  <Download className="mr-2 h-4 w-4" />
                  PPTX
                </Button>
                <Button variant="ghost" onClick={() => router.push('/presentations')}>
                  Мои презентации
                </Button>
                <span className="text-sm text-green-600">Сохранено!</span>
              </>
            )}
          </div>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">
                {result.presentation.title} — {result.presentation.slides.length} слайдов
              </CardTitle>
            </CardHeader>
            <CardContent>
              <SlidePreview
                slides={result.presentation.slides}
                theme={theme}
                context={{ subject: result.context.subject, grade_level: result.context.grade_level }}
              />
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}

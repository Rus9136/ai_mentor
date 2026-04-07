'use client';

import { getMediaUrl } from '@/lib/api/client';
import type { SlideData } from '@/types/presentation';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';

interface SlidePreviewProps {
  slides: SlideData[];
}

const SLIDE_TYPE_LABELS: Record<string, string> = {
  title: 'Титульный',
  objectives: 'Цели',
  content: 'Контент',
  key_terms: 'Термины',
  quiz: 'Вопрос',
  summary: 'Итоги',
};

const SLIDE_TYPE_COLORS: Record<string, string> = {
  title: 'bg-blue-600',
  objectives: 'bg-blue-500',
  content: 'bg-slate-600',
  key_terms: 'bg-purple-600',
  quiz: 'bg-green-600',
  summary: 'bg-blue-800',
};

export function SlidePreview({ slides }: SlidePreviewProps) {
  return (
    <div className="space-y-4">
      {slides.map((slide, idx) => (
        <SlideCard key={idx} slide={slide} index={idx} />
      ))}
    </div>
  );
}

function SlideCard({ slide, index }: { slide: SlideData; index: number }) {
  const typeLabel = SLIDE_TYPE_LABELS[slide.type] || slide.type;
  const typeColor = SLIDE_TYPE_COLORS[slide.type] || 'bg-slate-500';

  return (
    <Card className="overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-2 bg-muted/50 border-b">
        <Badge variant="secondary" className="text-xs">
          {index + 1}
        </Badge>
        <Badge className={`${typeColor} text-white text-xs`}>
          {typeLabel}
        </Badge>
        <span className="text-sm font-medium text-muted-foreground">
          {slide.title}
        </span>
      </div>

      <CardContent className="p-4">
        {slide.type === 'title' && <TitleSlide slide={slide} />}
        {slide.type === 'objectives' && <ObjectivesSlide slide={slide} />}
        {slide.type === 'content' && <ContentSlide slide={slide} />}
        {slide.type === 'key_terms' && <KeyTermsSlide slide={slide} />}
        {slide.type === 'quiz' && <QuizSlide slide={slide} />}
        {slide.type === 'summary' && <SummarySlide slide={slide} />}
      </CardContent>
    </Card>
  );
}

function TitleSlide({ slide }: { slide: SlideData }) {
  return (
    <div className="text-center py-6 bg-blue-50 rounded-lg">
      <h2 className="text-2xl font-bold text-blue-900">{slide.title}</h2>
      {slide.subtitle && (
        <p className="text-lg text-blue-700 mt-2">{slide.subtitle}</p>
      )}
    </div>
  );
}

function ObjectivesSlide({ slide }: { slide: SlideData }) {
  return (
    <div className="space-y-2">
      {slide.items?.map((item, i) => (
        <div key={i} className="flex items-start gap-2">
          <span className="font-semibold text-blue-600 min-w-[24px]">
            {i + 1}.
          </span>
          <span className="text-sm">{item}</span>
        </div>
      ))}
    </div>
  );
}

function ContentSlide({ slide }: { slide: SlideData }) {
  const imageUrl = slide.image_url ? getMediaUrl(slide.image_url) : null;

  return (
    <div className={imageUrl ? 'grid grid-cols-3 gap-4' : ''}>
      <div className={imageUrl ? 'col-span-2' : ''}>
        <p className="text-sm whitespace-pre-line leading-relaxed">
          {slide.body}
        </p>
      </div>
      {imageUrl && (
        <div className="flex items-start justify-center">
          <img
            src={imageUrl}
            alt={slide.title}
            className="max-h-48 rounded-lg object-contain"
          />
        </div>
      )}
    </div>
  );
}

function KeyTermsSlide({ slide }: { slide: SlideData }) {
  return (
    <div className="space-y-2">
      {slide.terms?.map((t, i) => (
        <div key={i} className="flex gap-3 p-2 bg-slate-50 rounded">
          <span className="font-semibold text-blue-700 min-w-[120px]">
            {t.term}
          </span>
          <span className="text-sm text-muted-foreground">— {t.definition}</span>
        </div>
      ))}
    </div>
  );
}

function QuizSlide({ slide }: { slide: SlideData }) {
  return (
    <div className="space-y-3">
      <p className="font-semibold text-base">{slide.question}</p>
      <div className="space-y-2">
        {slide.options?.map((option, i) => {
          const isAnswer = i === slide.answer;
          const letters = ['A', 'B', 'C', 'D', 'E', 'F'];
          return (
            <div
              key={i}
              className={`flex items-center gap-2 p-2 rounded text-sm ${
                isAnswer
                  ? 'bg-green-50 border border-green-300 text-green-800'
                  : 'bg-slate-50 border border-transparent'
              }`}
            >
              <span className="font-semibold min-w-[24px]">
                {letters[i] || i + 1})
              </span>
              <span>{option}</span>
              {isAnswer && (
                <Badge variant="outline" className="ml-auto text-green-600 border-green-300 text-xs">
                  Правильный
                </Badge>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function SummarySlide({ slide }: { slide: SlideData }) {
  return (
    <div className="space-y-2">
      {slide.items?.map((item, i) => (
        <div key={i} className="flex items-start gap-2">
          <span className="text-green-600">&#10003;</span>
          <span className="text-sm">{item}</span>
        </div>
      ))}
    </div>
  );
}

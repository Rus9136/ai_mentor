'use client';

import { useState, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { useRouter } from '@/i18n/routing';
import { Button } from '@/components/ui/button';
import { Loader2, Plus, Trash2, Send, Users } from 'lucide-react';
import { useCreateQuickQuestion } from '@/lib/hooks/use-quiz';
import { useTeacherQuizWebSocket } from '@/lib/hooks/use-quiz-websocket';
import { QRCodeSVG } from 'qrcode.react';

type Phase = 'create' | 'lobby' | 'live';

export default function QuickQuestionPage() {
  const t = useTranslations('quiz');
  const router = useRouter();
  const createQuickQuestion = useCreateQuickQuestion();

  const [phase, setPhase] = useState<Phase>('create');
  const [questionText, setQuestionText] = useState('');
  const [options, setOptions] = useState(['', '']);
  const [sessionData, setSessionData] = useState<{ id: number; join_code: string } | null>(null);
  const [participantCount, setParticipantCount] = useState(0);
  const [responses, setResponses] = useState<Record<string, number>>({});
  const [responseTotal, setResponseTotal] = useState(0);

  const joinCode = sessionData?.join_code || null;
  const { lastMessage, sendQuickQuestion, sendEndQuickQuestion, connected } = useTeacherQuizWebSocket(
    phase !== 'create' ? joinCode : null,
  );

  useEffect(() => {
    if (!lastMessage) return;
    switch (lastMessage.type) {
      case 'participant_joined':
        setParticipantCount((lastMessage.data as { count: number }).count);
        break;
      case 'quick_response_update':
        setResponses((lastMessage.data as { responses: Record<string, number> }).responses);
        setResponseTotal((lastMessage.data as { total: number }).total);
        break;
    }
  }, [lastMessage]);

  const addOption = () => {
    if (options.length < 6) setOptions([...options, '']);
  };

  const removeOption = (index: number) => {
    if (options.length > 2) setOptions(options.filter((_, i) => i !== index));
  };

  const handleCreate = async () => {
    const validOptions = options.filter((o) => o.trim());
    if (!questionText.trim() || validOptions.length < 2) return;

    try {
      const result = await createQuickQuestion.mutateAsync({
        question_text: questionText.trim(),
        options: validOptions,
      });
      setSessionData({ id: result.id, join_code: result.join_code });
      setPhase('lobby');
    } catch {
      // error handled by mutation
    }
  };

  const handleSendQuestion = () => {
    const validOptions = options.filter((o) => o.trim());
    sendQuickQuestion(questionText.trim(), validOptions);
    setPhase('live');
    setResponses({});
    setResponseTotal(0);
  };

  const handleEndQuestion = () => {
    sendEndQuickQuestion();
  };

  const qrUrl = joinCode ? `https://ai-mentor.kz/ru/webview/quiz?code=${joinCode}` : '';

  if (phase === 'create') {
    return (
      <div className="mx-auto max-w-lg space-y-6">
        <h1 className="text-2xl font-bold">{t('quickQuestion')}</h1>

        <div>
          <label className="mb-1.5 block text-sm font-medium">{t('questionText')}</label>
          <textarea
            className="w-full rounded-lg border bg-card px-3 py-2.5 text-sm"
            rows={3}
            value={questionText}
            onChange={(e) => setQuestionText(e.target.value)}
            placeholder={t('typeQuestion')}
          />
        </div>

        <div className="space-y-2">
          <label className="block text-sm font-medium">{t('options')}</label>
          {options.map((opt, i) => (
            <div key={i} className="flex items-center gap-2">
              <span className="w-6 text-center text-sm font-bold text-muted-foreground">
                {String.fromCharCode(65 + i)}
              </span>
              <input
                className="flex-1 rounded-lg border bg-card px-3 py-2 text-sm"
                value={opt}
                onChange={(e) => {
                  const newOpts = [...options];
                  newOpts[i] = e.target.value;
                  setOptions(newOpts);
                }}
                placeholder={`${t('option')} ${String.fromCharCode(65 + i)}`}
              />
              {options.length > 2 && (
                <button onClick={() => removeOption(i)} className="text-muted-foreground hover:text-red-500">
                  <Trash2 className="h-4 w-4" />
                </button>
              )}
            </div>
          ))}
          {options.length < 6 && (
            <Button variant="outline" size="sm" onClick={addOption}>
              <Plus className="mr-1 h-3 w-3" /> {t('addOption')}
            </Button>
          )}
        </div>

        <Button
          onClick={handleCreate}
          disabled={!questionText.trim() || options.filter((o) => o.trim()).length < 2 || createQuickQuestion.isPending}
          className="w-full"
        >
          {createQuickQuestion.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
          {t('createRoom')}
        </Button>
      </div>
    );
  }

  if (phase === 'lobby') {
    return (
      <div className="mx-auto max-w-lg space-y-6 text-center">
        <h1 className="text-2xl font-bold">{t('quickQuestion')}</h1>

        <div className="rounded-xl border bg-card p-6">
          <p className="mb-2 text-sm text-muted-foreground">{t('joinCode')}</p>
          <p className="mb-4 text-4xl font-bold tracking-widest">{joinCode}</p>
          <div className="flex justify-center">
            <QRCodeSVG value={qrUrl} size={160} />
          </div>
        </div>

        <div className="flex items-center justify-center gap-2 text-muted-foreground">
          <Users className="h-5 w-5" />
          <span>{participantCount} {t('connected')}</span>
        </div>

        <Button onClick={handleSendQuestion} disabled={participantCount === 0} className="w-full">
          <Send className="mr-2 h-4 w-4" />
          {t('sendQuestion')}
        </Button>
      </div>
    );
  }

  // phase === 'live'
  const COLORS = ['#E53E3E', '#3182CE', '#D69E2E', '#38A169', '#805AD5', '#DD6B20'];
  const LABELS = ['A', 'B', 'C', 'D', 'E', 'F'];
  const validOptions = options.filter((o) => o.trim());
  const maxResponse = Math.max(1, ...Object.values(responses));

  return (
    <div className="mx-auto max-w-lg space-y-6">
      <h1 className="text-xl font-bold">{questionText}</h1>
      <p className="text-sm text-muted-foreground">{responseTotal} {t('responses')}</p>

      <div className="space-y-3">
        {validOptions.map((opt, i) => {
          const count = responses[String(i)] || 0;
          const pct = Math.round((count / maxResponse) * 100);
          return (
            <div key={i}>
              <div className="mb-1 flex items-center justify-between text-sm">
                <span className="font-medium">{LABELS[i]}. {opt}</span>
                <span className="text-muted-foreground">{count}</span>
              </div>
              <div className="h-6 w-full overflow-hidden rounded-full bg-muted">
                <div
                  className="h-full rounded-full transition-all duration-300"
                  style={{ width: `${pct}%`, backgroundColor: COLORS[i] }}
                />
              </div>
            </div>
          );
        })}
      </div>

      <div className="flex gap-3">
        <Button variant="outline" onClick={handleEndQuestion} className="flex-1">
          {t('endQuestion')}
        </Button>
        <Button onClick={() => router.push('/quiz')} variant="secondary" className="flex-1">
          {t('backToList')}
        </Button>
      </div>
    </div>
  );
}

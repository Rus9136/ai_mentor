'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { QRCodeSVG } from 'qrcode.react';
import { Copy, Check, Users } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface Participant {
  id: number;
  student_name: string;
}

interface QuizLobbyTeacherProps {
  joinCode: string;
  participants: Participant[];
  onStart: () => void;
  onCancel: () => void;
  isStarting: boolean;
}

export default function QuizLobbyTeacher({ joinCode, participants, onStart, onCancel, isStarting }: QuizLobbyTeacherProps) {
  const t = useTranslations('quiz');
  const [copied, setCopied] = useState(false);

  const quizUrl = `https://ai-mentor.kz/ru/webview/quiz?code=${joinCode}`;

  const handleCopy = async () => {
    await navigator.clipboard.writeText(joinCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Join Code */}
      <div className="rounded-xl border bg-card p-6 text-center">
        <p className="mb-2 text-sm font-medium text-muted-foreground">{t('joinCode')}</p>
        <div className="flex items-center justify-center gap-3">
          <span className="text-5xl font-bold tracking-widest">{joinCode}</span>
          <button onClick={handleCopy} className="rounded-lg p-2 hover:bg-muted">
            {copied ? <Check className="h-5 w-5 text-green-500" /> : <Copy className="h-5 w-5 text-muted-foreground" />}
          </button>
        </div>
        {copied && <p className="mt-1 text-sm text-green-600">{t('codeCopied')}</p>}

        <div className="mt-4 flex justify-center">
          <QRCodeSVG value={quizUrl} size={180} level="H" includeMargin />
        </div>
        <p className="mt-2 text-xs text-muted-foreground">{t('scanQR')}</p>
      </div>

      {/* Participants */}
      <div className="rounded-xl border bg-card p-4">
        <div className="mb-3 flex items-center gap-2 text-sm font-medium">
          <Users className="h-4 w-4" />
          {t('connected', { count: participants.length })}
        </div>
        {participants.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {participants.map((p) => (
              <span key={p.id} className="rounded-full bg-primary/10 px-3 py-1 text-sm font-medium text-primary">
                {p.student_name}
              </span>
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">{t('waitingForStudents')}</p>
        )}
      </div>

      {/* Actions */}
      <div className="flex gap-3">
        <Button onClick={onStart} disabled={participants.length === 0 || isStarting} className="flex-1">
          {t('startQuiz')}
        </Button>
        <Button variant="outline" onClick={onCancel}>
          {t('cancelQuiz')}
        </Button>
      </div>
    </div>
  );
}

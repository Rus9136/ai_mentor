'use client';

import { useQuizSounds, type QuizSound } from '@/lib/hooks/use-quiz-sounds';
import { Volume2, VolumeX } from 'lucide-react';

const SOUNDS: { name: QuizSound; label: string; desc: string }[] = [
  { name: 'lobby', label: 'Lobby', desc: 'Вход в лобби' },
  { name: 'questionAppear', label: 'Question', desc: 'Новый вопрос' },
  { name: 'tick', label: 'Tick', desc: 'Таймер < 5 сек' },
  { name: 'timeUp', label: 'Time Up', desc: 'Время вышло' },
  { name: 'correct', label: 'Correct', desc: 'Правильный ответ' },
  { name: 'incorrect', label: 'Incorrect', desc: 'Неправильный ответ' },
  { name: 'streak', label: 'Streak', desc: 'Бонус за серию' },
  { name: 'result', label: 'Result', desc: 'Результат вопроса' },
  { name: 'victory', label: 'Victory', desc: 'Квиз завершён' },
];

export default function TestSoundsPage() {
  const { play, muted, toggleMute } = useQuizSounds();

  return (
    <div className="flex min-h-dvh flex-col items-center gap-6 p-6">
      <h1 className="text-2xl font-bold">Quiz Sounds Test</h1>

      <button
        onClick={toggleMute}
        className="flex items-center gap-2 rounded-lg bg-gray-200 px-4 py-2 font-medium"
      >
        {muted ? <VolumeX className="h-5 w-5" /> : <Volume2 className="h-5 w-5" />}
        {muted ? 'Muted' : 'Sound On'}
      </button>

      <div className="grid w-full max-w-md gap-3">
        {SOUNDS.map((s) => (
          <button
            key={s.name}
            onClick={() => play(s.name)}
            className="flex items-center justify-between rounded-xl bg-card p-4 shadow transition-transform active:scale-95"
          >
            <div className="text-left">
              <p className="font-semibold">{s.label}</p>
              <p className="text-sm text-muted-foreground">{s.desc}</p>
            </div>
            <span className="text-2xl">▶</span>
          </button>
        ))}
      </div>

      <button
        onClick={() => {
          const sequence: [QuizSound, number][] = [
            ['lobby', 0],
            ['questionAppear', 1000],
            ['tick', 2000],
            ['tick', 3000],
            ['tick', 4000],
            ['correct', 5000],
            ['streak', 5300],
            ['result', 6500],
            ['victory', 8000],
          ];
          sequence.forEach(([sound, delay]) => setTimeout(() => play(sound), delay));
        }}
        className="mt-4 rounded-xl bg-primary px-6 py-3 font-bold text-white"
      >
        Play Full Sequence (8 sec)
      </button>
    </div>
  );
}

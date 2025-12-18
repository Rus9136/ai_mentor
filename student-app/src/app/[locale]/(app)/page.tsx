'use client';

import { useTranslations } from 'next-intl';
import { useAuth } from '@/providers/auth-provider';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { LogOut, BookOpen } from 'lucide-react';

export default function HomePage() {
  const t = useTranslations('home');
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="border-b bg-white shadow-sm">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
              <BookOpen className="h-5 w-5 text-primary" />
            </div>
            <span className="text-xl font-bold text-gray-900">AI Mentor</span>
          </div>

          <div className="flex items-center gap-4">
            {user?.avatar_url && (
              <img
                src={user.avatar_url}
                alt="Avatar"
                className="h-8 w-8 rounded-full"
              />
            )}
            <span className="text-sm text-gray-600">
              {user?.first_name} {user?.last_name}
            </span>
            <Button variant="ghost" size="sm" onClick={logout}>
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="mx-auto max-w-7xl px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">{t('title')}</h1>
          <p className="mt-2 text-gray-600">{t('subtitle')}</p>
        </div>

        {/* Placeholder content */}
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {['История Казахстана', 'Математика', 'Физика'].map((subject) => (
            <Card
              key={subject}
              className="cursor-pointer transition-shadow hover:shadow-lg"
            >
              <CardHeader>
                <CardTitle className="text-lg">{subject}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  Нажмите для начала обучения
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      </main>
    </div>
  );
}

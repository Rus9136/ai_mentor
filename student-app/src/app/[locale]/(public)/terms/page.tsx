'use client';

import { useTranslations } from 'next-intl';
import { Link } from '@/i18n/routing';
import { GraduationCap, ArrowLeft } from 'lucide-react';

export default function TermsPage() {
  const t = useTranslations('terms');

  const sections = [
    { title: t('sections.definitions.title'), content: t('sections.definitions.content') },
    { title: t('sections.subject.title'), content: t('sections.subject.content') },
    { title: t('sections.registration.title'), content: t('sections.registration.content') },
    { title: t('sections.userRights.title'), content: t('sections.userRights.content') },
    { title: t('sections.adminRights.title'), content: t('sections.adminRights.content') },
    { title: t('sections.ai.title'), content: t('sections.ai.content') },
    { title: t('sections.ip.title'), content: t('sections.ip.content') },
    { title: t('sections.personalData.title'), content: t('sections.personalData.content') },
    { title: t('sections.liability.title'), content: t('sections.liability.content') },
    { title: t('sections.termination.title'), content: t('sections.termination.content') },
    { title: t('sections.changes.title'), content: t('sections.changes.content') },
    { title: t('sections.law.title'), content: t('sections.law.content') },
    { title: t('sections.contact.title'), content: t('sections.contact.content') },
  ];

  return (
    <div className="relative overflow-hidden">
      {/* Decorative blobs */}
      <div className="blob blob-orange blob-animate absolute -top-32 -right-32 h-96 w-96 opacity-30" />
      <div className="blob blob-green absolute -bottom-24 -left-24 h-80 w-80 opacity-20" />

      {/* Header */}
      <header className="relative z-10 border-b border-border/40 bg-background/95 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-4xl items-center justify-between px-4">
          <Link href="/" className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary">
              <GraduationCap className="h-5 w-5 text-white" />
            </div>
            <span className="text-xl font-bold text-foreground">AI Mentor</span>
          </Link>

          <Link
            href="/"
            className="flex items-center gap-2 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
          >
            <ArrowLeft className="h-4 w-4" />
            {t('back')}
          </Link>
        </div>
      </header>

      {/* Content */}
      <main className="relative z-10 mx-auto max-w-4xl px-4 py-12">
        <h1 className="mb-2 text-3xl font-extrabold tracking-tight text-foreground sm:text-4xl">
          {t('title')}
        </h1>
        <p className="mb-4 text-sm text-muted-foreground">
          {t('lastUpdated')}
        </p>
        <p className="mb-10 text-muted-foreground leading-relaxed">
          {t('intro')}
        </p>

        <div className="space-y-8">
          {sections.map((section, index) => (
            <section key={index}>
              <h2 className="mb-3 text-xl font-bold text-foreground">
                {index + 1}. {section.title}
              </h2>
              <p className="text-muted-foreground leading-relaxed whitespace-pre-line">
                {section.content}
              </p>
            </section>
          ))}
        </div>
      </main>

      {/* Footer */}
      <footer className="relative z-10 border-t border-border/40 bg-background/80 backdrop-blur-sm">
        <div className="mx-auto max-w-4xl px-4 py-6 text-center text-xs text-muted-foreground">
          {t('footer')}
        </div>
      </footer>
    </div>
  );
}

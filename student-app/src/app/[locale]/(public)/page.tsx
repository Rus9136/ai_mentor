'use client';

import { useTranslations } from 'next-intl';
import { Link } from '@/i18n/routing';
import {
  GraduationCap,
  Brain,
  BookOpen,
  MessageSquare,
  BarChart3,
  ArrowRight,
  ChevronDown,
} from 'lucide-react';

export default function LandingPage() {
  const t = useTranslations('landing');

  const features = [
    {
      icon: Brain,
      title: t('features.adaptive.title'),
      description: t('features.adaptive.description'),
      color: 'bg-orange-100 text-orange-600',
    },
    {
      icon: BookOpen,
      title: t('features.lessons.title'),
      description: t('features.lessons.description'),
      color: 'bg-green-100 text-green-600',
    },
    {
      icon: MessageSquare,
      title: t('features.ai.title'),
      description: t('features.ai.description'),
      color: 'bg-orange-100 text-orange-600',
    },
    {
      icon: BarChart3,
      title: t('features.progress.title'),
      description: t('features.progress.description'),
      color: 'bg-green-100 text-green-600',
    },
  ];

  return (
    <div className="relative overflow-hidden">
      {/* Decorative blobs */}
      <div className="blob blob-orange blob-animate absolute -top-32 -right-32 h-96 w-96 opacity-60" />
      <div className="blob blob-orange absolute -bottom-24 -left-24 h-80 w-80 opacity-40" />
      <div className="blob blob-green absolute top-1/3 -left-16 h-48 w-48 opacity-30" />
      <div className="blob blob-cream absolute bottom-1/4 right-1/4 h-64 w-64 opacity-50" />

      {/* Hero Section */}
      <section className="relative z-10 flex min-h-screen flex-col items-center justify-center px-4 py-20 text-center">
        {/* Logo */}
        <div className="mb-6 flex h-20 w-20 items-center justify-center rounded-3xl bg-primary shadow-soft-lg">
          <GraduationCap className="h-10 w-10 text-white" />
        </div>

        <h1 className="mb-4 text-4xl font-extrabold tracking-tight text-foreground sm:text-5xl md:text-6xl">
          {t('hero.title')}
        </h1>

        <p className="mx-auto mb-8 max-w-2xl text-lg text-muted-foreground sm:text-xl">
          {t('hero.subtitle')}
        </p>

        {/* CTA Buttons */}
        <div className="flex flex-col gap-3 sm:flex-row sm:gap-4">
          <Link
            href="/login"
            className="inline-flex items-center gap-2 rounded-full bg-primary px-8 py-3 text-base font-semibold text-primary-foreground shadow-soft-lg transition-all hover:opacity-90 hover:shadow-soft-xl"
          >
            {t('hero.cta')}
            <ArrowRight className="h-5 w-5" />
          </Link>
          <a
            href="#features"
            className="inline-flex items-center gap-2 rounded-full border border-border px-8 py-3 text-base font-semibold text-foreground transition-colors hover:bg-muted"
          >
            {t('hero.learnMore')}
          </a>
        </div>

        {/* Scroll indicator */}
        <div className="absolute bottom-8 animate-bounce">
          <ChevronDown className="h-6 w-6 text-muted-foreground" />
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="relative z-10 px-4 py-20">
        <div className="mx-auto max-w-5xl">
          <h2 className="mb-4 text-center text-3xl font-bold text-foreground sm:text-4xl">
            {t('features.title')}
          </h2>
          <p className="mx-auto mb-12 max-w-2xl text-center text-muted-foreground">
            {t('features.subtitle')}
          </p>

          <div className="grid gap-6 sm:grid-cols-2">
            {features.map((feature, index) => (
              <div
                key={index}
                className="rounded-2xl border border-border/40 bg-card/80 p-6 backdrop-blur-sm transition-all hover:shadow-soft-lg"
              >
                <div
                  className={`mb-4 flex h-12 w-12 items-center justify-center rounded-xl ${feature.color}`}
                >
                  <feature.icon className="h-6 w-6" />
                </div>
                <h3 className="mb-2 text-lg font-bold text-foreground">
                  {feature.title}
                </h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 border-t border-border/40 bg-background/80 backdrop-blur-sm">
        <div className="mx-auto max-w-5xl px-4 py-8">
          <div className="flex flex-col items-center gap-6 sm:flex-row sm:justify-between">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary">
                <GraduationCap className="h-5 w-5 text-white" />
              </div>
              <span className="text-lg font-bold text-foreground">AI Mentor</span>
            </div>

            {/* Links */}
            <div className="flex items-center gap-6">
              <Link
                href="/terms"
                className="text-sm text-muted-foreground transition-colors hover:text-foreground"
              >
                {t('footer.terms')}
              </Link>
              <Link
                href="/privacy"
                className="text-sm text-muted-foreground transition-colors hover:text-foreground"
              >
                {t('footer.privacy')}
              </Link>
              <Link
                href="/login"
                className="text-sm font-medium text-primary transition-colors hover:text-primary/80"
              >
                {t('footer.login')}
              </Link>
            </div>
          </div>

          <div className="mt-6 text-center text-xs text-muted-foreground">
            {t('footer.copyright')}
          </div>
        </div>
      </footer>
    </div>
  );
}

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
  Smartphone,
} from 'lucide-react';
import { QRCodeSVG } from 'qrcode.react';

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

      {/* Download App Section */}
      <section className="relative z-10 px-4 py-20">
        <div className="mx-auto max-w-5xl">
          <div className="flex items-center justify-center gap-2 mb-4">
            <Smartphone className="h-7 w-7 text-primary" />
            <h2 className="text-center text-3xl font-bold text-foreground sm:text-4xl">
              {t('download.title')}
            </h2>
          </div>
          <p className="mx-auto mb-12 max-w-2xl text-center text-muted-foreground">
            {t('download.subtitle')}
          </p>

          <div className="flex flex-col items-center gap-8 sm:flex-row sm:justify-center sm:gap-16">
            {/* Google Play */}
            <a
              href="https://play.google.com/store/apps/details?id=kz.aimentor.ai_mentor_student"
              target="_blank"
              rel="noopener noreferrer"
              className="group flex flex-col items-center gap-4"
            >
              <div className="rounded-2xl border border-border/40 bg-card/80 p-4 backdrop-blur-sm transition-all group-hover:shadow-soft-lg">
                <QRCodeSVG
                  value="https://play.google.com/store/apps/details?id=kz.aimentor.ai_mentor_student"
                  size={160}
                  level="M"
                  includeMargin={false}
                />
              </div>
              <div className="flex items-center gap-2">
                <svg viewBox="0 0 24 24" className="h-6 w-6 text-muted-foreground group-hover:text-foreground transition-colors" fill="currentColor">
                  <path d="M3.609 1.814L13.792 12 3.61 22.186a.996.996 0 0 1-.61-.92V2.734a1 1 0 0 1 .609-.92zm10.89 10.893l2.302 2.302-10.937 6.333 8.635-8.635zm3.199-3.199l2.807 1.626a1 1 0 0 1 0 1.732l-2.807 1.626L15.206 12l2.492-2.492zM5.864 2.658L16.8 8.99l-2.302 2.302-8.634-8.634z"/>
                </svg>
                <span className="text-sm font-semibold text-muted-foreground group-hover:text-foreground transition-colors">
                  {t('download.playStore')}
                </span>
              </div>
            </a>

            {/* App Store */}
            <a
              href="https://apps.apple.com/kz/app/ai-mentor-kz/id6757806291"
              target="_blank"
              rel="noopener noreferrer"
              className="group flex flex-col items-center gap-4"
            >
              <div className="rounded-2xl border border-border/40 bg-card/80 p-4 backdrop-blur-sm transition-all group-hover:shadow-soft-lg">
                <QRCodeSVG
                  value="https://apps.apple.com/kz/app/ai-mentor-kz/id6757806291"
                  size={160}
                  level="M"
                  includeMargin={false}
                />
              </div>
              <div className="flex items-center gap-2">
                <svg viewBox="0 0 24 24" className="h-6 w-6 text-muted-foreground group-hover:text-foreground transition-colors" fill="currentColor">
                  <path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.8-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z"/>
                </svg>
                <span className="text-sm font-semibold text-muted-foreground group-hover:text-foreground transition-colors">
                  {t('download.appStore')}
                </span>
              </div>
            </a>
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

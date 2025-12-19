import type { Metadata } from 'next';
import { Nunito } from 'next/font/google';
import { NextIntlClientProvider } from 'next-intl';
import { getMessages, setRequestLocale } from 'next-intl/server';
import { notFound } from 'next/navigation';
import { routing } from '@/i18n/routing';
import { AuthProvider } from '@/providers/auth-provider';
import { QueryProvider } from '@/providers/query-provider';
import '../globals.css';

const nunito = Nunito({
  subsets: ['latin', 'cyrillic'],
  weight: ['400', '500', '600', '700', '800'],
  variable: '--font-nunito',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'AI Mentor - Учись по-своему',
  description: 'Адаптивная образовательная платформа для школьников 7-11 классов',
};

interface LocaleLayoutProps {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}

export function generateStaticParams() {
  return routing.locales.map((locale) => ({ locale }));
}

export default async function LocaleLayout({
  children,
  params,
}: LocaleLayoutProps) {
  const { locale } = await params;

  if (!routing.locales.includes(locale as 'ru' | 'kz')) {
    notFound();
  }

  setRequestLocale(locale);
  const messages = await getMessages();

  return (
    <html lang={locale} className={nunito.variable}>
      <body className="min-h-screen bg-background font-sans antialiased">
        <QueryProvider>
          <NextIntlClientProvider messages={messages}>
            <AuthProvider>{children}</AuthProvider>
          </NextIntlClientProvider>
        </QueryProvider>
      </body>
    </html>
  );
}

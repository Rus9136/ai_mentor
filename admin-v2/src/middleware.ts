import createMiddleware from 'next-intl/middleware';
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { locales, defaultLocale } from './i18n/config';

const intlMiddleware = createMiddleware({
  locales,
  defaultLocale,
  localePrefix: 'always',
});

export default function middleware(request: NextRequest) {
  const pathname = request.nextUrl.pathname;

  // 301 редирект со старых URL /kk/... на новые /kz/...
  if (pathname.startsWith('/kk/') || pathname === '/kk') {
    const newPath = pathname.replace(/^\/kk/, '/kz');
    return NextResponse.redirect(new URL(newPath, request.url), 301);
  }

  return intlMiddleware(request);
}

export const config = {
  // Match all pathnames except for
  // - … if they start with `/api`, `/_next` or `/_vercel`
  // - … the ones containing a dot (e.g. `favicon.ico`)
  // Добавлен kk для обработки редиректа
  matcher: ['/', '/(ru|kz|kk)/:path*', '/((?!api|_next|_vercel|.*\\..*).*)'],
};

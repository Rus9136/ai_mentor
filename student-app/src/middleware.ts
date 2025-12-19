import createMiddleware from 'next-intl/middleware';
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { routing } from './i18n/routing';

const intlMiddleware = createMiddleware(routing);

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
  // Добавлен kk для обработки редиректа
  matcher: ['/', '/(ru|kz|kk)/:path*'],
};

import { getRequestConfig } from 'next-intl/server';
import { routing } from './routing';

// Маппинг URL локали на файл переводов
// URL использует 'kz', но файл переводов называется 'kk.json'
const localeToMessageFile: Record<string, string> = {
  ru: 'ru',
  kz: 'kk',
};

export default getRequestConfig(async ({ requestLocale }) => {
  let locale = await requestLocale;

  if (!locale || !routing.locales.includes(locale as 'ru' | 'kz')) {
    locale = routing.defaultLocale;
  }

  const messageFile = localeToMessageFile[locale] || locale;

  return {
    locale,
    messages: (await import(`../../messages/${messageFile}.json`)).default,
  };
});

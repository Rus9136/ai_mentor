import { getRequestConfig } from 'next-intl/server';
import { locales, type Locale } from './config';

// Маппинг URL локали на файл переводов
// URL использует 'kz', но файл переводов называется 'kk.json'
const localeToMessageFile: Record<string, string> = {
  ru: 'ru',
  kz: 'kk',
};

export default getRequestConfig(async ({ requestLocale }) => {
  let locale = await requestLocale;

  // Ensure that the incoming locale is valid
  if (!locale || !locales.includes(locale as Locale)) {
    locale = 'ru';
  }

  const messageFile = localeToMessageFile[locale] || locale;

  return {
    locale,
    messages: (await import(`../../messages/${messageFile}.json`)).default,
  };
});

export const locales = ['ru', 'kz'] as const;
export type Locale = (typeof locales)[number];

export const defaultLocale: Locale = 'ru';

export const localeNames: Record<Locale, string> = {
  ru: 'Русский',
  kz: 'Қазақша',
};

import type { EpochData } from '@/types/lab';

/**
 * Historical epochs of Kazakhstan for the interactive map.
 * Each epoch has a GeoJSON file in public/data/history/ (to be added in Phase 3).
 * For now, this serves as the timeline data source.
 */
export const EPOCHS: EpochData[] = [
  {
    id: 'saka',
    name: 'Саки и Усуни',
    period: 'VII в. до н.э. — V в. н.э.',
    start_year: -700,
    end_year: 500,
    description:
      'Племенные союзы саков, усуней и кангюев на территории Казахстана. Сакская царица Томирис, курганы Иссыка, золотой человек.',
    paragraph_id: null,
    color: '#D4A574',
  },
  {
    id: 'turkic',
    name: 'Тюркский каганат',
    period: 'VI—VIII вв.',
    start_year: 552,
    end_year: 744,
    description:
      'Первая тюркская империя. Великий Шёлковый путь, руническая письменность, города Суяб и Баласагун.',
    paragraph_id: null,
    color: '#7EB5A6',
  },
  {
    id: 'golden_horde',
    name: 'Золотая Орда',
    period: 'XIII—XV вв.',
    start_year: 1227,
    end_year: 1465,
    description:
      'Улус Джучи (Золотая Орда). Монгольское завоевание, расцвет городов Сарай-Бату, Сыгнак. Распад на Белую и Синюю Орду.',
    paragraph_id: null,
    color: '#E8A838',
  },
  {
    id: 'kazakh_khanate',
    name: 'Казахское ханство',
    period: 'XV—XVIII вв.',
    start_year: 1465,
    end_year: 1731,
    description:
      'Основание Казахского ханства Кереем и Жанибеком. Деление на три жуза. Расцвет при хане Касыме, Хак-Назаре, Тауке.',
    paragraph_id: null,
    color: '#4A90D9',
  },
  {
    id: 'russian_empire',
    name: 'В составе Российской империи',
    period: 'XVIII—XIX вв.',
    start_year: 1731,
    end_year: 1917,
    description:
      'Присоединение казахских жузов к России. Ликвидация ханской власти, национально-освободительные движения Кенесары, Исатая.',
    paragraph_id: null,
    color: '#8B6E5A',
  },
  {
    id: 'kazakh_ssr',
    name: 'Казахская ССР',
    period: '1936—1991',
    start_year: 1936,
    end_year: 1991,
    description:
      'Казахстан в составе СССР. Индустриализация, коллективизация, Великая Отечественная война, освоение целины, Семипалатинский полигон.',
    paragraph_id: null,
    color: '#C75050',
  },
  {
    id: 'independence',
    name: 'Независимый Казахстан',
    period: '1991 — настоящее время',
    start_year: 1991,
    end_year: 2026,
    description:
      'Провозглашение независимости 16 декабря 1991 года. Перенос столицы в Астану, вступление в международные организации.',
    paragraph_id: null,
    color: '#00AFCA',
  },
];

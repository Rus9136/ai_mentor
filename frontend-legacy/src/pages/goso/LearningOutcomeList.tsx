import {
  List,
  Datagrid,
  TextField,
  TextInput,
  SelectInput,
  TopToolbar,
  FilterButton,
  FunctionField,
} from 'react-admin';
import { Chip, Typography, Box } from '@mui/material';
import type { LearningOutcome } from '../../types';

/**
 * Выбор класса для фильтра
 */
const gradeChoices = [
  { id: 5, name: '5 класс' },
  { id: 6, name: '6 класс' },
  { id: 7, name: '7 класс' },
  { id: 8, name: '8 класс' },
  { id: 9, name: '9 класс' },
  { id: 10, name: '10 класс' },
  { id: 11, name: '11 класс' },
];

/**
 * Фильтры для списка целей обучения
 */
const outcomeFilters = [
  <TextInput key="q" source="q" label="Поиск" alwaysOn />,
  <SelectInput
    key="grade"
    source="grade"
    label="Класс"
    choices={gradeChoices}
    alwaysOn
  />,
];

/**
 * Actions для списка
 */
const ListActions = () => (
  <TopToolbar>
    <FilterButton />
  </TopToolbar>
);

/**
 * Рендер функция для отображения кода с подсветкой
 */
const renderCode = (record: LearningOutcome) => (
  <Chip
    label={record.code}
    size="small"
    color="primary"
    variant="outlined"
    sx={{ fontWeight: 600, fontFamily: 'monospace' }}
  />
);

/**
 * Рендер функция для класса
 */
const renderGrade = (record: LearningOutcome) => (
  <Chip
    label={`${record.grade} кл.`}
    size="small"
    color="secondary"
  />
);

/**
 * Рендер функция для когнитивного уровня
 */
const renderCognitiveLevel = (record: LearningOutcome) => {
  if (!record?.cognitive_level) {
    return <Typography variant="body2" color="text.secondary">—</Typography>;
  }

  const levelColors: Record<string, 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning'> = {
    'знание': 'default',
    'понимание': 'info',
    'применение': 'success',
    'анализ': 'warning',
    'синтез': 'secondary',
    'оценка': 'error',
  };

  const color = levelColors[record.cognitive_level.toLowerCase()] || 'default';

  return (
    <Chip
      label={record.cognitive_level}
      size="small"
      color={color}
      variant="outlined"
    />
  );
};

/**
 * Пустой компонент для случая когда нет данных
 */
const Empty = () => (
  <Box textAlign="center" p={3}>
    <Typography variant="h6" color="textSecondary">
      Нет целей обучения
    </Typography>
    <Typography variant="body2" color="textSecondary">
      Цели обучения по заданным фильтрам не найдены
    </Typography>
  </Box>
);

/**
 * Список целей обучения (Learning Outcomes)
 *
 * Отображает таблицу с целями обучения ГОСО.
 * Поддерживает фильтрацию по классу и поиск.
 * Read-only для SUPER_ADMIN.
 */
export const LearningOutcomeList = () => (
  <List
    title="Цели обучения ГОСО"
    filters={outcomeFilters}
    actions={<ListActions />}
    sort={{ field: 'code', order: 'ASC' }}
    perPage={25}
    empty={<Empty />}
  >
    <Datagrid
      bulkActionButtons={false}
      sx={{
        '& .RaDatagrid-rowCell': {
          verticalAlign: 'top',
          py: 1.5,
        },
      }}
    >
      <FunctionField label="Код" render={renderCode} />
      <FunctionField label="Класс" render={renderGrade} />
      <TextField source="title_ru" label="Цель обучения" />
      <FunctionField label="Уровень" render={renderCognitiveLevel} />
    </Datagrid>
  </List>
);

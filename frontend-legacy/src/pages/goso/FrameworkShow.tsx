import { useState, useEffect } from 'react';
import {
  Show,
  TabbedShowLayout,
  useRecordContext,
} from 'react-admin';
import {
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Typography,
  Box,
  Chip,
  CircularProgress,
  Alert,
  Card,
  CardContent,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Badge,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import FolderIcon from '@mui/icons-material/Folder';
import FolderOpenIcon from '@mui/icons-material/FolderOpen';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import type { Framework, GosoSection, GosoSubsection, LearningOutcome } from '../../types';
import { getAuthToken } from '../../providers/authProvider';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// Расширенный тип с вложенными данными
interface SectionWithSubsections extends GosoSection {
  subsections: SubsectionWithOutcomes[];
}

interface SubsectionWithOutsections extends GosoSubsection {
  outcomes: LearningOutcome[];
}

type SubsectionWithOutcomes = SubsectionWithOutsections;

/**
 * Компонент для отображения целей обучения в подразделе
 */
const OutcomesList = ({ outcomes, grade }: { outcomes: LearningOutcome[]; grade?: number }) => {
  // Группируем по классам
  const outcomesByGrade = outcomes.reduce((acc, outcome) => {
    const g = outcome.grade;
    if (!acc[g]) acc[g] = [];
    acc[g].push(outcome);
    return acc;
  }, {} as Record<number, LearningOutcome[]>);

  const grades = Object.keys(outcomesByGrade).map(Number).sort((a, b) => a - b);
  const filteredGrades = grade ? grades.filter(g => g === grade) : grades;

  if (filteredGrades.length === 0) {
    return (
      <Typography variant="body2" color="text.secondary" sx={{ pl: 2, py: 1 }}>
        Нет целей обучения {grade ? `для ${grade} класса` : ''}
      </Typography>
    );
  }

  return (
    <Box>
      {filteredGrades.map(g => (
        <Box key={g} sx={{ mb: 2 }}>
          <Typography variant="subtitle2" color="primary" sx={{ mb: 1 }}>
            {g} класс ({outcomesByGrade[g].length} целей)
          </Typography>
          <List dense disablePadding>
            {outcomesByGrade[g].map(outcome => (
              <ListItem key={outcome.id} sx={{ py: 0.5, pl: 1 }}>
                <ListItemIcon sx={{ minWidth: 32 }}>
                  <CheckCircleOutlineIcon fontSize="small" color="action" />
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Typography variant="body2">
                      <strong>{outcome.code}</strong> — {outcome.title_ru}
                    </Typography>
                  }
                  secondary={outcome.cognitive_level && (
                    <Chip
                      label={outcome.cognitive_level}
                      size="small"
                      variant="outlined"
                      sx={{ mt: 0.5, height: 20, fontSize: '0.7rem' }}
                    />
                  )}
                />
              </ListItem>
            ))}
          </List>
        </Box>
      ))}
    </Box>
  );
};

/**
 * Компонент для отображения подраздела с целями
 */
const SubsectionAccordion = ({
  subsection,
  gradeFilter,
}: {
  subsection: SubsectionWithOutcomes;
  gradeFilter?: number;
}) => {
  const [expanded, setExpanded] = useState(false);

  const filteredOutcomes = gradeFilter
    ? subsection.outcomes.filter(o => o.grade === gradeFilter)
    : subsection.outcomes;

  const outcomesCount = filteredOutcomes.length;

  if (outcomesCount === 0 && gradeFilter) {
    return null; // Скрываем пустые подразделы при фильтрации
  }

  return (
    <Accordion
      expanded={expanded}
      onChange={() => setExpanded(!expanded)}
      sx={{
        '&:before': { display: 'none' },
        boxShadow: 'none',
        border: '1px solid',
        borderColor: 'divider',
        mb: 1,
      }}
    >
      <AccordionSummary
        expandIcon={<ExpandMoreIcon />}
        sx={{ 
          bgcolor: 'rgba(33, 150, 243, 0.12)', 
          '& .MuiTypography-root': { color: 'text.primary' },
          '& .MuiSvgIcon-root': { color: 'text.secondary' }
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
          {expanded ? <FolderOpenIcon color="action" /> : <FolderIcon color="action" />}
          <Typography variant="body1" sx={{ fontWeight: 500 }}>
            {subsection.code}. {subsection.name_ru}
          </Typography>
          <Badge
            badgeContent={outcomesCount}
            color="primary"
            sx={{ ml: 'auto', mr: 2 }}
          />
        </Box>
      </AccordionSummary>
      <AccordionDetails sx={{ pt: 2 }}>
        {expanded && <OutcomesList outcomes={filteredOutcomes} grade={gradeFilter} />}
      </AccordionDetails>
    </Accordion>
  );
};

/**
 * Компонент для отображения раздела с подразделами
 */
const SectionAccordion = ({
  section,
  gradeFilter,
}: {
  section: SectionWithSubsections;
  gradeFilter?: number;
}) => {
  const [expanded, setExpanded] = useState(false);

  // Подсчитываем общее количество целей
  const totalOutcomes = section.subsections.reduce((sum, sub) => {
    const filtered = gradeFilter
      ? sub.outcomes.filter(o => o.grade === gradeFilter)
      : sub.outcomes;
    return sum + filtered.length;
  }, 0);

  // Фильтруем непустые подразделы
  const filteredSubsections = gradeFilter
    ? section.subsections.filter(sub => sub.outcomes.some(o => o.grade === gradeFilter))
    : section.subsections;

  if (filteredSubsections.length === 0 && gradeFilter) {
    return null;
  }

  return (
    <Accordion
      expanded={expanded}
      onChange={() => setExpanded(!expanded)}
      sx={{ mb: 2 }}
    >
      <AccordionSummary
        expandIcon={<ExpandMoreIcon />}
        sx={{ bgcolor: 'primary.light', color: 'primary.contrastText' }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            {section.code}. {section.name_ru}
          </Typography>
          <Chip
            label={`${totalOutcomes} целей`}
            size="small"
            sx={{
              ml: 'auto',
              bgcolor: 'white',
              color: 'primary.main',
            }}
          />
        </Box>
      </AccordionSummary>
      <AccordionDetails sx={{ p: 2 }}>
        {expanded && filteredSubsections.map(subsection => (
          <SubsectionAccordion
            key={subsection.id}
            subsection={subsection}
            gradeFilter={gradeFilter}
          />
        ))}
      </AccordionDetails>
    </Accordion>
  );
};

/**
 * Вкладка "Информация" — общие данные о версии ГОСО
 */
const InfoTab = () => {
  const record = useRecordContext<Framework>();

  if (!record) {
    return <CircularProgress />;
  }

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 3 }}>
          <Box>
            <Typography variant="subtitle2" color="text.secondary">Код</Typography>
            <Typography variant="body1">{record.code}</Typography>
          </Box>
          <Box>
            <Typography variant="subtitle2" color="text.secondary">Статус</Typography>
            <Chip
              label={record.is_active ? 'Активен' : 'Неактивен'}
              color={record.is_active ? 'success' : 'default'}
              size="small"
            />
          </Box>
          <Box sx={{ gridColumn: '1 / -1' }}>
            <Typography variant="subtitle2" color="text.secondary">Название</Typography>
            <Typography variant="body1">{record.title_ru}</Typography>
          </Box>
          {record.description_ru && (
            <Box sx={{ gridColumn: '1 / -1' }}>
              <Typography variant="subtitle2" color="text.secondary">Описание</Typography>
              <Typography variant="body1">{record.description_ru}</Typography>
            </Box>
          )}
          <Divider sx={{ gridColumn: '1 / -1', my: 1 }} />
          {record.document_type && (
            <Box>
              <Typography variant="subtitle2" color="text.secondary">Тип документа</Typography>
              <Typography variant="body1">{record.document_type}</Typography>
            </Box>
          )}
          {record.order_number && (
            <Box>
              <Typography variant="subtitle2" color="text.secondary">Номер приказа</Typography>
              <Typography variant="body1">{record.order_number}</Typography>
            </Box>
          )}
          {record.ministry && (
            <Box sx={{ gridColumn: '1 / -1' }}>
              <Typography variant="subtitle2" color="text.secondary">Министерство</Typography>
              <Typography variant="body1">{record.ministry}</Typography>
            </Box>
          )}
          <Box>
            <Typography variant="subtitle2" color="text.secondary">Действует с</Typography>
            <Typography variant="body1">
              {record.valid_from
                ? new Date(record.valid_from).toLocaleDateString('ru-RU')
                : '—'}
            </Typography>
          </Box>
          <Box>
            <Typography variant="subtitle2" color="text.secondary">Действует до</Typography>
            <Typography variant="body1">
              {record.valid_to
                ? new Date(record.valid_to).toLocaleDateString('ru-RU')
                : 'По настоящее время'}
            </Typography>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};

/**
 * Вкладка "Структура" — иерархия разделов, подразделов и целей
 */
const StructureTab = () => {
  const record = useRecordContext<Framework>();
  const [structure, setStructure] = useState<SectionWithSubsections[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [gradeFilter, setGradeFilter] = useState<number | undefined>(undefined);

  useEffect(() => {
    if (!record?.id) return;

    const fetchStructure = async () => {
      try {
        const token = getAuthToken();

        // 1. Загружаем структуру framework (sections)
        const structureResponse = await fetch(
          `${API_URL}/goso/frameworks/${record.id}/structure`,
          {
            headers: { Authorization: `Bearer ${token}` },
          }
        );

        if (!structureResponse.ok) {
          throw new Error(`HTTP error! status: ${structureResponse.status}`);
        }

        const frameworkData = await structureResponse.json();
        const sections: GosoSection[] = frameworkData.sections || [];

        // 2. Загружаем все outcomes для этого framework
        const outcomesResponse = await fetch(
          `${API_URL}/goso/outcomes?framework_id=${record.id}&limit=1000`,
          {
            headers: { Authorization: `Bearer ${token}` },
          }
        );

        if (!outcomesResponse.ok) {
          throw new Error(`HTTP error! status: ${outcomesResponse.status}`);
        }

        const outcomes: LearningOutcome[] = await outcomesResponse.json();

        // 3. Группируем outcomes по subsection_id
        const outcomesBySubsection = outcomes.reduce((acc, outcome) => {
          const subId = outcome.subsection_id;
          if (!acc[subId]) acc[subId] = [];
          acc[subId].push(outcome);
          return acc;
        }, {} as Record<number, LearningOutcome[]>);

        // 4. Строим полную структуру
        // Для каждого section загружаем subsections отдельно (если нет в structure)
        // Пока используем API endpoints для загрузки

        // Загружаем subsections для каждого section
        const sectionsWithSubsections: SectionWithSubsections[] = await Promise.all(
          sections.map(async (section) => {
            // API не возвращает subsections напрямую, загрузим outcomes и сгруппируем
            // По структуре outcomes.subsection_id связан с subsections

            // Найдем уникальные subsection_id из outcomes для этого section
            // Но outcomes не содержит section_id напрямую...

            // Загрузим subsections через дополнительный запрос
            // К сожалению, backend не имеет эндпоинта для subsections отдельно
            // Поэтому используем данные из outcomes

            // Для MVP: группируем outcomes по subsection и получаем уникальные subsection_id
            const sectionOutcomes = outcomes.filter(o => {
              // Код outcome начинается с класс.раздел.подраздел.номер
              // Например: 5.1.1.1 -> раздел 1
              const parts = o.code.split('.');
              if (parts.length >= 2) {
                return parts[1] === section.code;
              }
              return false;
            });

            // Группируем по subsection_id
            const subsectionIds = [...new Set(sectionOutcomes.map(o => o.subsection_id))];

            // Создаем subsections из outcomes
            const subsections: SubsectionWithOutcomes[] = subsectionIds.map(subId => {
              const subOutcomes = outcomesBySubsection[subId] || [];
              // Извлекаем название из первого outcome (если есть)
              const firstOutcome = subOutcomes[0];
              const subCode = firstOutcome?.code.split('.').slice(1, 3).join('.') || String(subId);

              return {
                id: subId,
                section_id: section.id,
                code: subCode,
                name_ru: `Подраздел ${subCode}`,
                display_order: subId,
                is_active: true,
                created_at: '',
                updated_at: '',
                outcomes: subOutcomes,
              };
            });

            return {
              ...section,
              subsections: subsections.sort((a, b) => a.display_order - b.display_order),
            };
          })
        );

        setStructure(sectionsWithSubsections.sort((a, b) => a.display_order - b.display_order));
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Ошибка загрузки структуры');
      } finally {
        setLoading(false);
      }
    };

    fetchStructure();
  }, [record?.id]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        Ошибка загрузки структуры: {error}
      </Alert>
    );
  }

  if (!structure || structure.length === 0) {
    return (
      <Alert severity="info" sx={{ m: 2 }}>
        Структура ГОСО не загружена
      </Alert>
    );
  }

  // Подсчитываем общую статистику
  const totalOutcomes = structure.reduce(
    (sum, section) =>
      sum + section.subsections.reduce((subSum, sub) => subSum + sub.outcomes.length, 0),
    0
  );

  // Получаем уникальные классы
  const grades = [...new Set(
    structure.flatMap(s => s.subsections.flatMap(sub => sub.outcomes.map(o => o.grade)))
  )].sort((a, b) => a - b);

  return (
    <Box sx={{ p: 2 }}>
      {/* Статистика и фильтры */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
            <Typography variant="h6">
              Всего: {structure.length} разделов, {totalOutcomes} целей обучения
            </Typography>
            <Box sx={{ ml: 'auto', display: 'flex', gap: 1 }}>
              <Chip
                label="Все классы"
                variant={!gradeFilter ? 'filled' : 'outlined'}
                color={!gradeFilter ? 'primary' : 'default'}
                onClick={() => setGradeFilter(undefined)}
                clickable
              />
              {grades.map(g => (
                <Chip
                  key={g}
                  label={`${g} кл.`}
                  variant={gradeFilter === g ? 'filled' : 'outlined'}
                  color={gradeFilter === g ? 'primary' : 'default'}
                  onClick={() => setGradeFilter(g)}
                  clickable
                />
              ))}
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* Дерево разделов */}
      {structure.map(section => (
        <SectionAccordion
          key={section.id}
          section={section}
          gradeFilter={gradeFilter}
        />
      ))}
    </Box>
  );
};

/**
 * Основной компонент FrameworkShow
 */
export const FrameworkShow = () => (
  <Show title="Просмотр версии ГОСО">
    <TabbedShowLayout>
      <TabbedShowLayout.Tab label="Информация">
        <InfoTab />
      </TabbedShowLayout.Tab>
      <TabbedShowLayout.Tab label="Структура" path="structure">
        <StructureTab />
      </TabbedShowLayout.Tab>
    </TabbedShowLayout>
  </Show>
);
